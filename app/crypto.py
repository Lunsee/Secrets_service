from cryptography.fernet import Fernet
import os

from dotenv import load_dotenv

load_dotenv()  # .env

FERNET_KEY = os.getenv("FERNET_KEY")
cipher = Fernet(FERNET_KEY)

def encrypt_secret(secret: str) -> str:
    return cipher.encrypt(secret.encode()).decode()

def decrypt_secret(encrypted_secret: str) -> str:
    return cipher.decrypt(encrypted_secret.encode()).decode()