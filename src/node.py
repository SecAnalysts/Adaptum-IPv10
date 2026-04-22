import socket
import threading
import json
import hashlib

from crypto import CryptoManager
from dns import register, resolve

class IPv10Node:
    def __init__(self, host, port):
        self.host = host
        self.port = port

        self.crypto = CryptoManager()
        self.address = self.generate_address()

        # DNS auto register
        self.name = f"node_{port}.adaptum"
        register(self.name, self.address)

        self.peers = []
        self.sessions = {}

    def generate_address(self):
        pub = self.crypto.public_key.public_bytes_raw()
        return hashlib.sha256(pub).hexdigest()

    def start(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((self.host, self.port))
        server.listen(5)

        print(f"[{self.name}] {self.address[:10]} listening on {self.port}")

        threading.Thread(target=self.listen, args=(server,), daemon=True).start()

    def listen(self, server):
        while True:
            conn, addr = server.accept()
            data = conn.recv(8192)
            if data:
                try:
                    packet = json.loads(data.decode())
                    self.handle(packet, addr)
                except:
                    pass
            conn.close()

    def handle(self, packet, addr):
        if packet["type"] == "DATA":
            key = self.sessions.get(addr)
            if not key:
                return

            decrypted = self.crypto.decrypt(key, packet["payload"])
            inner = json.loads(decrypted)

            if inner["dst"] == self.address:
                print(f"[{self.name}] RECEIVED:", inner["payload"])
            else:
                inner["ttl"] -= 1
                if inner["ttl"] > 0:
                    self.forward(inner, exclude=addr)

    def send_raw(self, host, port, packet):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((host, port))
            s.send(json.dumps(packet).encode())
            s.close()
        except:
            pass

    def connect_peer(self, host, port):
        key = self.crypto.generate_session_key()
        self.sessions[(host, port)] = key

    def send_secure(self, host, port, packet):
        key = self.sessions.get((host, port))
        if not key:
            return

        encrypted = self.crypto.encrypt(key, json.dumps(packet))

        data = {
            "type": "DATA",
            "payload": encrypted
        }

        self.send_raw(host, port, data)

    def forward(self, packet, exclude=None):
        for peer in self.peers:
            if exclude and peer == exclude:
                continue
            self.send_secure(peer[0], peer[1], packet)

    def send_message(self, dst, message):
        # resolve DNS
        if ".adaptum" in dst:
            resolved = resolve(dst)
            if not resolved:
                print("Domain not found:", dst)
                return
            dst = resolved

        packet = {
            "src": self.address,
            "dst": dst,
            "ttl": 5,
            "payload": message
        }

        self.forward(packet)
