import requests
import sys
import time

node_id = sys.argv[1]
cpu_cores = sys.argv[2]
API_URL = "http://localhost:5000/heartbeat"

while True:
    try:
        requests.post(API_URL, json={"node_id": node_id})
        print(f"[{node_id}] Heartbeat sent")
    except Exception as e:
        print(f"[{node_id}] Heartbeat failed: {e}")
    time.sleep(5)
