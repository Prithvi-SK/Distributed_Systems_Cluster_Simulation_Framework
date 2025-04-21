import time
import threading
import datetime
import sys
import os
from scheduler import SCHEDULERS
from flask import Flask, request, jsonify, render_template, redirect, url_for
from threading import Lock
from utils import launch_node

app = Flask(__name__)
nodes = {}
lock = Lock()
activities = []  # To store recent activities for the dashboard
current_scheduler = 'first-fit'  # Default scheduler
last_used_node = None  # For round-robin scheduler

# Custom Jinja2 filter to format timestamps
@app.template_filter('timestamp_to_time')
def timestamp_to_time(timestamp):
    return datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

@app.route('/')
def index():
    with lock:
        # Calculate dashboard stats
        online_nodes = sum(1 for node in nodes.values() if node.get('status') == 'online')
        total_pods = sum(len(node.get('pods', [])) for node in nodes.values())
        
        # Prepare data for CPU utilization chart
        node_ids = list(nodes.keys())
        cpu_total = [node.get('cpu', 0) for node in nodes.values()]
        cpu_available = [node.get('available_cpu', 0) for node in nodes.values()]
        
        # Prepare data for node status chart
        status_counts = {
            'online': sum(1 for node in nodes.values() if node.get('status') == 'online'),
            'offline': sum(1 for node in nodes.values() if node.get('status') == 'offline'),
            'starting': sum(1 for node in nodes.values() if node.get('status') == 'starting')
        }
        
        return render_template('index.html', 
                              nodes=nodes,
                              online_nodes=online_nodes,
                              total_pods=total_pods,
                              node_ids=node_ids,
                              cpu_total=cpu_total,
                              cpu_available=cpu_available,
                              status_counts=status_counts,
                              activities=activities[-10:],
                              current_scheduler=current_scheduler)

@app.route('/nodes')
def nodes_page():
    with lock:
        return render_template('nodes.html', nodes=nodes, current_scheduler=current_scheduler)

@app.route('/pods')
def pods_page():
    with lock:
        return render_template('pods.html', nodes=nodes, current_scheduler=current_scheduler)

@app.route('/api/dashboard_data')
def dashboard_data():
    with lock:
        # Get new activities since last request (if any)
        last_activity_time = request.args.get('last_time', 0, type=float)
        new_activities = [a for a in activities if a.get('timestamp', 0) > last_activity_time]
        
        # Calculate current stats
        total_nodes = len(nodes)
        online_nodes = sum(1 for node in nodes.values() if node.get('status') == 'online')
        total_pods = sum(len(node.get('pods', [])) for node in nodes.values())
        
        # Prepare data for charts
        node_ids = list(nodes.keys())
        cpu_total = [node.get('cpu', 0) for node in nodes.values()]
        cpu_available = [node.get('available_cpu', 0) for node in nodes.values()]
        
        status_counts = {
            'online': sum(1 for node in nodes.values() if node.get('status') == 'online'),
            'offline': sum(1 for node in nodes.values() if node.get('status') == 'offline'),
            'starting': sum(1 for node in nodes.values() if node.get('status') == 'starting')
        }
        
        return jsonify({
            'total_nodes': total_nodes,
            'online_nodes': online_nodes,
            'total_pods': total_pods,
            'node_ids': node_ids,
            'cpu_total': cpu_total,
            'cpu_available': cpu_available,
            'status_counts': status_counts,
            'activities': new_activities,
            'current_scheduler': current_scheduler
        })

@app.route('/nodes/<node_id>/pods')
def node_pods(node_id):
    with lock:
        if node_id in nodes:
            return jsonify({'pods': nodes[node_id]['pods']})
        return jsonify({'error': 'Node not found'}), 404

@app.route('/set_scheduler', methods=['POST'])
def set_scheduler():
    global current_scheduler
    data = request.get_json()
    scheduler_name = data.get('scheduler')
    
    if scheduler_name not in SCHEDULERS.keys():
        return jsonify({"error": f"Unknown scheduler: {scheduler_name}"}), 400
    
    with lock:
        old_scheduler = current_scheduler
        current_scheduler = scheduler_name
        add_activity('info', f"Scheduler changed from {old_scheduler} to {current_scheduler}")
    
    return jsonify({"message": f"Scheduler set to {current_scheduler}"}), 200

@app.route('/get_scheduler', methods=['GET'])
def get_scheduler():
    return jsonify({"scheduler": current_scheduler, "available_schedulers": list(SCHEDULERS.keys())})

# Original API routes
@app.route('/hello')
def hello():
    return jsonify({"message": "Hello Rishav"})

@app.route('/add_node', methods=['POST'])
def add_node():
    data = request.get_json()
    cpu = data.get("cpu_cores")
    if not cpu:
        return jsonify({"error": "Missing 'cpu_cores'"}), 400

    with lock:
        node_id = f"node{len(nodes)}"
        launch_node(node_id, cpu)
        nodes[node_id] = {
            "cpu": int(cpu),
            "available_cpu": int(cpu),
            "pods": [],
            "status": "starting",
            "last_heartbeat": time.time()
        }
        
        # Add activity
        add_activity('info', f"Node {node_id} added with {cpu} CPU cores")

    return jsonify({"message": f"{node_id} launched", "cpu": cpu}), 201

@app.route('/delete_node', methods=['POST'])
def delete_node():
    data = request.get_json()
    node_id = data.get("node_id")
    
    if not node_id:
        return jsonify({"error": "Missing 'node_id'"}), 400
    
    with lock:
        if node_id not in nodes:
            return jsonify({"error": f"Node {node_id} not found"}), 404
        
        # Get pods on the node
        pods = nodes[node_id]['pods']
        
        # Remove node
        del nodes[node_id]
        
        # Add activity
        add_activity('warning', f"Node {node_id} deleted with {len(pods)} pods")
        
        # Attempt to reschedule pods if there were any
        if pods:
            rescheduled_count = 0
            for pod in pods:
                cpu = pod["cpu"]
                
                # Use current scheduler algorithm
                if current_scheduler == 'round-robin':
                    new_node_id = SCHEDULERS[current_scheduler](nodes, cpu, last_used_node)
                else:
                    new_node_id = SCHEDULERS[current_scheduler](nodes, cpu)
                
                if new_node_id:
                    nodes[new_node_id]["available_cpu"] -= cpu
                    nodes[new_node_id]["pods"].append(pod)
                    rescheduled_count += 1
                    add_activity('success', f"Pod {pod['id']} rescheduled to node {new_node_id}")
            
            if rescheduled_count < len(pods):
                add_activity('danger', f"{len(pods) - rescheduled_count} pods could not be rescheduled")
    
    return jsonify({"message": f"Node {node_id} deleted"}), 200

@app.route('/heartbeat', methods=['POST'])
def heartbeat():
    data = request.get_json()
    node_id = data.get("node_id")

    with lock:
        if node_id in nodes:
            old_status = nodes[node_id]["status"]
            nodes[node_id]["status"] = "online"
            nodes[node_id]["last_heartbeat"] = time.time()
            
            # Add activity for status change
            if old_status != "online":
                add_activity('success', f"Node {node_id} is now online")

    return jsonify({"message": f"Heartbeat received from {node_id}"}), 200

@app.route('/launch_pod', methods=['POST'])
def launch_pod():
    global last_used_node
    data = request.get_json()
    cpu_required = data.get("cpu")
    if not cpu_required:
        return jsonify({"error": "Missing 'cpu'"}), 400

    with lock:
        # Provide detailed diagnostics
        online_nodes_count = sum(1 for info in nodes.values() if info["status"] == "online")
        if online_nodes_count == 0:
            add_activity('warning', f"Failed to schedule pod: No online nodes available")
            return jsonify({
                "error": "No online nodes available. Please add nodes and wait for them to come online.",
                "status": "no_online_nodes"
            }), 503
            
        # More diagnostics on available CPU
        max_available = 0
        max_node = None
        for node_id, info in nodes.items():
            if info["status"] == "online" and info["available_cpu"] > max_available:
                max_available = info["available_cpu"]
                max_node = node_id
                
        if max_available < cpu_required:
            add_activity('warning', f"Failed to schedule pod: Maximum available CPU ({max_available} on {max_node}) is less than required ({cpu_required})")
            return jsonify({
                "error": f"No node has enough available CPU. Maximum available is {max_available} cores on {max_node}, but {cpu_required} cores were requested.",
                "status": "insufficient_cpu"
            }), 503
            
        # Use the current scheduler algorithm
        if current_scheduler == 'round-robin':
            selected_node = SCHEDULERS[current_scheduler](nodes, cpu_required, last_used_node)
        else:
            selected_node = SCHEDULERS[current_scheduler](nodes, cpu_required)
        
        if not selected_node:
            # This shouldn't happen given our checks above, but just in case
            add_activity('danger', f"Failed to schedule pod: Scheduler couldn't find a suitable node")
            return jsonify({
                "error": "Scheduler couldn't find a suitable node despite available resources. This may be a bug.",
                "status": "scheduler_error"
            }), 503

        # Update last used node for round-robin
        last_used_node = selected_node
        
        pod_id = f"pod{len(nodes[selected_node]['pods'])}"
        nodes[selected_node]['available_cpu'] -= cpu_required
        nodes[selected_node]['pods'].append({"id": pod_id, "cpu": cpu_required})
        
        # Add activity
        add_activity('primary', f"Pod {pod_id} launched on node {selected_node} using {current_scheduler} scheduler (CPU: {cpu_required})")

    return jsonify({"message": "Pod launched", "node": selected_node, "pod_id": pod_id}), 201

@app.route('/list_nodes', methods=['GET'])
def get_all_nodes():
    with lock:
        return jsonify(nodes)

@app.route('/api/system_status')
def system_status():
    """Get detailed system status information for diagnostics"""
    with lock:
        status = {
            "nodes": {
                "total": len(nodes),
                "online": sum(1 for info in nodes.values() if info["status"] == "online"),
                "offline": sum(1 for info in nodes.values() if info["status"] == "offline"),
                "starting": sum(1 for info in nodes.values() if info["status"] == "starting")
            },
            "pods": {
                "total": sum(len(info.get("pods", [])) for info in nodes.values())
            },
            "resources": {
                "total_cpu": sum(info.get("cpu", 0) for info in nodes.values()),
                "available_cpu": sum(info.get("available_cpu", 0) for info in nodes.values())
            },
            "scheduler": current_scheduler,
            "node_details": []
        }
        
        # Add detailed info for each node
        for node_id, info in nodes.items():
            status["node_details"].append({
                "id": node_id,
                "status": info["status"],
                "cpu": info["cpu"],
                "available_cpu": info["available_cpu"],
                "pods_count": len(info["pods"]),
                "last_heartbeat_ago": time.time() - info.get("last_heartbeat", 0)
            })
            
        return jsonify(status)

def add_activity(activity_type, message):
    """Add an activity to the activity log"""
    current_time = time.time()
    formatted_time = datetime.datetime.fromtimestamp(current_time).strftime('%H:%M:%S')
    
    activities.append({
        'type': activity_type,
        'message': message,
        'time': formatted_time,
        'timestamp': current_time
    })
    
    # Limit to last 100 activities
    if len(activities) > 100:
        activities.pop(0)

def monitor_health():
    while True:
        time.sleep(10)
        now = time.time()
        with lock:
            # Print heartbeat debug info
            print(f"[Monitor] Checking node health at {datetime.datetime.now()}")
            for node_id, info in nodes.items():
                last_heartbeat_ago = now - info.get("last_heartbeat", 0)
                print(f"  - Node {node_id}: status={info['status']}, last heartbeat={last_heartbeat_ago:.1f}s ago")
                
            # Give nodes more time to start up (30 seconds instead of 15)
            for node_id, info in list(nodes.items()):
                if info["status"] == "starting" and (now - info.get("last_heartbeat", 0) > 30):
                    info["status"] = "offline"
                    add_activity('danger', f"Node {node_id} failed to start (no heartbeat for 30s)")
                    print(f"[Monitor] Node {node_id} failed to start")
                
                elif info["status"] == "online" and (now - info.get("last_heartbeat", 0) > 15):
                    info["status"] = "offline"
                    add_activity('danger', f"Node {node_id} marked OFFLINE")
                    print(f"[Monitor] Node {node_id} marked OFFLINE")
                    
                    # Recover pods from this failed node
                    recovered_pods = info["pods"]
                    info["pods"] = []
                    info["available_cpu"] = info["cpu"]

                    for pod in recovered_pods:
                        cpu = pod["cpu"]
                        
                        # Use current scheduler algorithm
                        if current_scheduler == 'round-robin':
                            new_node_id = SCHEDULERS[current_scheduler](nodes, cpu, last_used_node)
                        else:
                            new_node_id = SCHEDULERS[current_scheduler](nodes, cpu)
                            
                        if new_node_id:
                            nodes[new_node_id]["available_cpu"] -= cpu
                            nodes[new_node_id]["pods"].append(pod)
                            add_activity('warning', f"Pod {pod['id']} recovered to node {new_node_id}")
                            print(f" → Recovered pod {pod['id']} to node {new_node_id}")
                        else:
                            add_activity('danger', f"Pod {pod['id']} could not be rescheduled")
                            print(f" !! Pod {pod['id']} could not be rescheduled")

if __name__ == '__main__':
    threading.Thread(target=monitor_health, daemon=True).start()
    app.run(host='0.0.0.0', port=5000, debug=True)
