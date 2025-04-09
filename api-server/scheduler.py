# api_server/scheduler.py

def first_fit_scheduler(nodes, cpu_required):
    for node_id, info in nodes.items():
        if info['status'] == 'online' and int(info['available_cpu']) >= cpu_required:
            return node_id
    return None
