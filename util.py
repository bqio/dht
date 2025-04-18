import hashlib
import secrets
import time


def generate_node_id() -> bytes:
    data = f"{secrets.token_hex(32)}-{time.time()}"
    return hashlib.sha1(data.encode()).digest()


def generate_transaction_id() -> bytes:
    return secrets.token_bytes(4)
