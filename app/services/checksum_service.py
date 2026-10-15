import hashlib


def compute_checksum(data: bytes) -> str:
    """Calcula el checksum SHA-256 de los bytes recibidos."""
    return hashlib.sha256(data).hexdigest()