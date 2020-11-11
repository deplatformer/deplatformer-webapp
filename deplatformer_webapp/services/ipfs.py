import os

from ..helpers import import_or_install

ipfshttpclient = import_or_install("ipfshttpclient")


class IPFSPinningFailed(Exception):
    pass


class IPFSService(object):
    def __init__(self, ipfs_uri):
        self._client = ipfshttpclient.connect(ipfs_uri, session=True)

    def add_file(self, filename):
        return self._client.add(filename)["Hash"]

    def pin_file(self, filepath):
        try:
            cid = self.add_file(filepath)
            self._client.pin.add(cid, timeout=5000)
            return {"success": True, "cid": cid, "error": None}
        except Exception as e:
            return {"success": False, "cid": None, "error": e}

    def pin_dir(self, directory, ignore=[]):
        results = {}
        for path, subdirectory, files in os.walk(directory):
            for file in files:
                if file not in ignore:
                    filepath = os.path.join(
                        path,
                        file,
                    )
                    results[filepath] = self.pin_file(filepath)
        return results

    def close(self):
        self._client.close()
