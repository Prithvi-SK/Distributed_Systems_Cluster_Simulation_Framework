import docker

client = docker.from_env()

def launch_node(node_id, cpu):
    client.containers.run(
        "node_sim_image",
        command=[node_id, str(cpu)],
        name=node_id,
        network="host",
        detach=True,
        auto_remove=True
    )
