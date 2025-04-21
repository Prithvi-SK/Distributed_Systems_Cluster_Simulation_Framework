# api_server/scheduler.py

"""
Scheduler module for the cluster simulation.
Contains various algorithms for pod scheduling.
"""

def first_fit_scheduler(nodes, cpu_required):
    """
    First Fit Algorithm: Assigns pod to the first node with enough CPU.
    
    Args:
        nodes: Dictionary of nodes with their properties
        cpu_required: CPU cores required by the pod
        
    Returns:
        node_id: ID of the selected node, or None if no suitable node found
    """
    for node_id, info in nodes.items():
        if info["status"] == "online" and info["available_cpu"] >= cpu_required:
            return node_id
    return None

def best_fit_scheduler(nodes, cpu_required):
    """
    Best Fit Algorithm: Assigns pod to the node with minimum adequate available CPU.
    Minimizes fragmentation by using the most constrained node first.
    
    Args:
        nodes: Dictionary of nodes with their properties
        cpu_required: CPU cores required by the pod
        
    Returns:
        node_id: ID of the selected node, or None if no suitable node found
    """
    suitable_nodes = {}
    
    for node_id, info in nodes.items():
        if info["status"] == "online" and info["available_cpu"] >= cpu_required:
            suitable_nodes[node_id] = info["available_cpu"]
    
    if not suitable_nodes:
        return None
        
    # Return node with minimum available CPU that still fits the requirement
    return min(suitable_nodes.items(), key=lambda x: x[1])[0]

def worst_fit_scheduler(nodes, cpu_required):
    """
    Worst Fit Algorithm: Assigns pod to the node with maximum available CPU.
    Reduces future fragmentation by using least constrained nodes first.
    
    Args:
        nodes: Dictionary of nodes with their properties
        cpu_required: CPU cores required by the pod
        
    Returns:
        node_id: ID of the selected node, or None if no suitable node found
    """
    suitable_nodes = {}
    
    for node_id, info in nodes.items():
        if info["status"] == "online" and info["available_cpu"] >= cpu_required:
            suitable_nodes[node_id] = info["available_cpu"]
    
    if not suitable_nodes:
        return None
        
    # Return node with maximum available CPU
    return max(suitable_nodes.items(), key=lambda x: x[1])[0]

def round_robin_scheduler(nodes, cpu_required, last_used_node_id=None):
    """
    Round Robin Algorithm: Assigns pods to nodes in a circular order.
    
    Args:
        nodes: Dictionary of nodes with their properties
        cpu_required: CPU cores required by the pod
        last_used_node_id: ID of the last node used (to continue from)
        
    Returns:
        node_id: ID of the selected node, or None if no suitable node found
    """
    node_ids = list(nodes.keys())
    if not node_ids:
        return None
    
    # Sort node IDs to maintain consistent order
    node_ids.sort()
    
    # Find starting point for round robin
    start_index = 0
    if last_used_node_id in node_ids:
        start_index = (node_ids.index(last_used_node_id) + 1) % len(node_ids)
    
    # Try nodes in round-robin order starting from the next node after last used
    for i in range(len(node_ids)):
        index = (start_index + i) % len(node_ids)
        node_id = node_ids[index]
        info = nodes[node_id]
        
        if info["status"] == "online" and info["available_cpu"] >= cpu_required:
            return node_id
    
    return None

# Dictionary of available schedulers
SCHEDULERS = {
    'first-fit': first_fit_scheduler,
    'best-fit': best_fit_scheduler,
    'worst-fit': worst_fit_scheduler,
    'round-robin': round_robin_scheduler
}
