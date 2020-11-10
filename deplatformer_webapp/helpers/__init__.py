import docker

def is_docker_running():
    """Checks if docker is running"""
    client = docker.from_env()
    is_running = True
    try:
        client.info()
    except Exception:
        is_running = False
    finally:
        client.close()
    return is_running