from flask import Flask, request, jsonify
from threading import Lock
from utils import launch_node

app = Flask(__name__)
nodes = {}
lock = Lock()

@app.route('/add_node', methods=['POST'])
def add_node():
    data = request.get_json()
    cpu = data.get("cpu_cores")
    if not cpu:
        return jsonify({"error": "Missing 'cpu_cores'"}), 400

    with lock:
        node_id = f"node{len(nodes)}"
        launch_node(node_id, cpu)
        nodes[node_id] = {"cpu": cpu, "pods": [], "status": "starting"}

    return jsonify({"message": f"{node_id} launched", "cpu": cpu}), 201

@app.route('/heartbeat', methods=['POST'])
def heartbeat():
    data = request.get_json()
    node_id = data.get("node_id")

    with lock:
        if node_id in nodes:
            nodes[node_id]["status"] = "online"

    return jsonify({"message": f"Heartbeat received from {node_id}"}), 200

@app.route('/nodes', methods=['GET'])
def list_nodes():
    with lock:
        return jsonify(nodes)

if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5000)
