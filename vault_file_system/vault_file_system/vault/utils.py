import json

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

def sha256(data: bytes) -> bytes:
    """Calculate the SHA256 digest of given data."""
    digest = hashes.Hash(hashes.SHA1(), backend=default_backend())
    digest.update(data)
    digest = digest.finalize()
    return digest

def json_to_dict(file_path) -> dict:
    with open(file_path) as file:
        file_json = json.load(file)

    return file_json
