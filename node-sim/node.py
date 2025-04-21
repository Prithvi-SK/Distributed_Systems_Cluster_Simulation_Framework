import requests
import sys
import time
import json
import platform
import os
import traceback

def send_heartbeat(node_id):
    """Send heartbeat to the API server"""
    try:
        API_URL = "http://localhost:5000/heartbeat"
        payload = {"node_id": node_id}
        headers = {"Content-Type": "application/json"}
        
        # Print diagnostic info
        print(f"[{node_id}] Sending heartbeat to {API_URL}")
        print(f"[{node_id}] Payload: {json.dumps(payload)}")
        
        # Send the heartbeat
        response = requests.post(API_URL, json=payload, headers=headers, timeout=5)
        
        # Check if the heartbeat was successful
        if response.status_code == 200:
            print(f"[{node_id}] Heartbeat sent successfully: {response.text}")
            return True
        else:
            print(f"[{node_id}] Heartbeat failed: {response.status_code} - {response.text}")
            return False
    except requests.exceptions.ConnectionError as e:
        print(f"[{node_id}] Connection error: {str(e)}")
        print(f"[{node_id}] Make sure the API server is running at {API_URL}")
        return False
    except Exception as e:
        print(f"[{node_id}] Heartbeat error: {str(e)}")
        traceback.print_exc()
        return False

def main():
    """Main function to run the node"""
    try:
        # Print diagnostic information
        print(f"Python version: {sys.version}")
        print(f"Platform: {platform.platform()}")
        print(f"Working directory: {os.getcwd()}")
        
        # Check command line arguments
        if len(sys.argv) < 3:
            print("Usage: python node.py <node_id> <cpu_cores>")
            sys.exit(1)
            
        node_id = sys.argv[1]
        cpu_cores = int(sys.argv[2])
        
        print(f"[{node_id}] Starting node with {cpu_cores} CPU cores")
        
        # Try an initial heartbeat
        initial_success = send_heartbeat(node_id)
        if not initial_success:
            print(f"[{node_id}] WARNING: Initial heartbeat failed, but continuing...")
        
        # Heartbeat loop
        retry_count = 0
        max_retries = 3
        while True:
            success = send_heartbeat(node_id)
            if not success:
                retry_count += 1
                print(f"[{node_id}] Heartbeat failed, retry {retry_count}/{max_retries}")
                if retry_count >= max_retries:
                    print(f"[{node_id}] Too many failures, retrying with exponential backoff")
                    time.sleep(5 * retry_count)  # Exponential backoff
                    # Don't reset retry_count to allow longer sleeps
            else:
                retry_count = 0  # Reset retry count on success
            
            # Wait before next heartbeat
            time.sleep(5)
    except KeyboardInterrupt:
        print(f"[{node_id}] Node shutting down due to keyboard interrupt")
    except Exception as e:
        print(f"[{node_id}] Fatal error: {str(e)}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()