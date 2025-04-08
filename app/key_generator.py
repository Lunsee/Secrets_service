# app/key_generator.py

import uuid

def generate_unique_key() -> str:
    """
    generate unique key for secrets.
    UUID.
    """
    return str(uuid.uuid4())