import os
from zipfile import ZipFile

import docker
import pip


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


def unzip(
    zip_file,
):
    print("Extracting zip file")
    # Get root name of zip file, use as directory name
    contents_dir = os.path.splitext(zip_file)
    # Create a ZipFile Object
    with ZipFile(
        zip_file,
        "r",
    ) as unzip_dir:
        # Extract all the contents of zip file in FB directory
        unzip_dir.extractall(contents_dir[0])

    return contents_dir[0]


def import_or_install(package):
    try:
        return __import__(package)
    except ImportError:
        cwd = os.path.abspath(os.path.dirname(__file__))
        wheel_path = os.path.join(cwd, "../lib/ipfshttpclient-0.7.0a1-py3-none-any.whl")
        pip.main(["install", wheel_path])
    finally:
        return __import__(package)
