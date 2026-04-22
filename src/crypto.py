import os
import json
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.asymmetric import ed25519

class CryptoManager:
    def __init__(self):
        self.private_key = ed25519.Ed25519PrivateKey.generate()
        self.public_key = self.private_key.public_key()

    def sign(self, data: str) -> str:
        return self.private_key.sign(data.encode()).hex()

    def verify(self, public_key_bytes, signature, data):
        pub = ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)
        pub.verify(bytes.fromhex(signature), data.encode())

    def generate_session_key(self):
        return AESGCM.generate_key(bit_length=128)

    def encrypt(self, key, data: str):
        aes = AESGCM(key)
        nonce = os.urandom(12)
        encrypted = aes.encrypt(nonce, data.encode(), None)
        return {
            "nonce": nonce.hex(),
            "data": encrypted.hex()
        }

    def decrypt(self, key, payload):
        aes = AESGCM(key)
        nonce = bytes.fromhex(payload["nonce"])
        data = bytes.fromhex(payload["data"])
        return aes.decrypt(nonce, data, None).decode()
