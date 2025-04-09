import time
import threading
from scheduler import first_fit_scheduler
from flask import Flask, request, jsonify
from threading import Lock
from utils import launch_node

app = Flask(__name__)
nodes = {}
lock = Lock()

@app.route('/')
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

    return jsonify({"message": f"{node_id} launched", "cpu": cpu}), 201

@app.route('/heartbeat', methods=['POST'])
def heartbeat():
    data = request.get_json()
    node_id = data.get("node_id")

    with lock:
        if node_id in nodes:
            nodes[node_id]["status"] = "online"
            nodes[node_id]["last_heartbeat"] = time.time()

    return jsonify({"message": f"Heartbeat received from {node_id}"}), 200

@app.route('/nodes', methods=['GET'])
def list_nodes():
    with lock:
        return jsonify(nodes)

@app.route('/launch_pod', methods=['POST'])
def launch_pod():
    data = request.get_json()
    cpu_required = data.get("cpu")
    if not cpu_required:
        return jsonify({"error": "Missing 'cpu'"}), 400

    with lock:
        selected_node = first_fit_scheduler(nodes, cpu_required)
        if not selected_node:
            return jsonify({"error": "No node has enough available CPU"}), 503

        pod_id = f"pod{len(nodes[selected_node]['pods'])}"
        nodes[selected_node]['available_cpu'] -= cpu_required
        nodes[selected_node]['pods'].append({"id": pod_id, "cpu": cpu_required})

    return jsonify({"message": "Pod launched", "node": selected_node, "pod_id": pod_id}), 201

@app.route('/list_nodes', methods=['GET'])
def get_all_nodes():
    with lock:
        return jsonify(nodes)

def monitor_health():
    while True:
        time.sleep(10)
        now = time.time()
        with lock:
            for node_id, info in list(nodes.items()):
                if info["status"] == "online" and (now - info.get("last_heartbeat", 0) > 15):
                    info["status"] = "offline"
                    print(f"[Monitor] Node {node_id} marked OFFLINE")

                    # Recover pods from this failed node
                    recovered_pods = info["pods"]
                    info["pods"] = []
                    info["available_cpu"] = info["cpu"]

                    for pod in recovered_pods:
                        cpu = pod["cpu"]
                        new_node_id = first_fit_scheduler(nodes, cpu)
                        if new_node_id:
                            nodes[new_node_id]["available_cpu"] -= cpu
                            nodes[new_node_id]["pods"].append(pod)
                            print(f" → Recovered pod {pod['id']} to node {new_node_id}")
                        else:
                            print(f" !! Pod {pod['id']} could not be rescheduled")

if __name__ == '__main__':
    threading.Thread(target=monitor_health, daemon=True).start()
    app.run(host='127.0.0.1', port=5000, debug=True)
