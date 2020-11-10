import atexit

import docker


def run_docker_ipfs_daemon(staging_dir, data_dir):
    client = docker.from_env()
    return client.containers.run(
        "ipfs/go-ipfs:latest",
        name="deplatformer_ipfs_host",
        volumes={staging_dir: {"bind": "/export", "mode": "rw"}, data_dir: {"bind": "/data/ipfs", "mode": "rw"}},
        ports={"4001/tcp": 4001, "4001/udp": 4001, "8080": ("127.0.0.1", 8080), 5001: ("127.0.0.1", 5001)},
        auto_remove=True,
        detach=True,
        tty=True,
    )


def register_ipfs_daemon_exit_handler(ipfs_container):
    def container_exit():
        print("Gracefully closing IPFS daemon...")
        ipfs_container.stop()

    atexit.register(container_exit)
