import subprocess
import sys
import os
import time
import traceback

def launch_node(node_id, cpu_cores):
    """
    Launch a node simulator as a separate Python process without using Docker.
    
    Args:
        node_id: Unique identifier for the node
        cpu_cores: Number of CPU cores assigned to the node
    """
    try:
        # Get the path to the node.py script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        node_script = os.path.join(project_root, "node-sim", "node.py")
        
        # Check if the script exists
        if not os.path.exists(node_script):
            print(f"ERROR: Node script not found at {node_script}")
            return False
        
        # Launch the process in the foreground for debugging
        # so we can watch output from the nodes in the console
        python_cmd = sys.executable
        cmd = [python_cmd, node_script, node_id, str(cpu_cores)]
        
        print(f"Starting node with command: {' '.join(cmd)}")
        
        # Use subprocess.Popen with stdout and stderr directed to the console
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        # Start a thread to read and display the output (non-blocking)
        def log_output(process):
            while True:
                stdout_line = process.stdout.readline()
                if stdout_line:
                    print(f"NODE OUTPUT: {stdout_line.strip()}")
                stderr_line = process.stderr.readline()
                if stderr_line:
                    print(f"NODE ERROR: {stderr_line.strip()}")
                
                # Check if process has terminated
                if process.poll() is not None:
                    remaining_stdout, remaining_stderr = process.communicate()
                    if remaining_stdout:
                        print(f"NODE FINAL OUTPUT: {remaining_stdout.strip()}")
                    if remaining_stderr:
                        print(f"NODE FINAL ERROR: {remaining_stderr.strip()}")
                    break
        
        import threading
        threading.Thread(target=log_output, args=(process,), daemon=True).start()
        
        print(f"Node {node_id} launched with {cpu_cores} CPU cores")
        return True
    except Exception as e:
        print(f"Error launching node: {e}")
        traceback.print_exc()
        return False