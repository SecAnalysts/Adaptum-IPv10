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

        # DNS
        self.name = f"node_{port}.adaptum"
        register(self.name, self.address)

        self.peers = []
        self.sessions = {}

        # 🔐 NEW: identity storage
        self.known_nodes = {}  # address -> pubkey

    def generate_address(self):
        pub = self.crypto.public_key.public_bytes_raw()
        return hashlib.sha256(pub).hexdigest()

    def get_pubkey_bytes(self):
        return self.crypto.public_key.public_bytes_raw()

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

        # 🔐 HANDLE INTRO (public key exchange)
        if packet["type"] == "INTRO":
            node_addr = packet["address"]
            pubkey = bytes.fromhex(packet["pubkey"])

            self.known_nodes[node_addr] = pubkey
            print(f"[{self.name}] Registered node {node_addr[:8]}")
            return

        # 🔐 HANDLE DATA
        if packet["type"] == "DATA":
            key = self.sessions.get(addr)
            if not key:
                return

            decrypted = self.crypto.decrypt(key, packet["payload"])
            inner = json.loads(decrypted)

            sender = inner["src"]
            signature = inner.get("signature")
            payload = inner["payload"]

            pubkey = self.known_nodes.get(sender)

            # ❌ unknown sender
            if not pubkey:
                print(f"[{self.name}] Unknown sender, dropping")
                return

            # ❌ invalid signature
            try:
                self.crypto.verify(pubkey, signature, payload)
            except:
                print(f"[{self.name}] Invalid signature, dropping")
                return

            # ✅ valid
            if inner["dst"] == self.address:
                print(f"[{self.name}] VERIFIED MESSAGE:", payload)
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

    # 🔐 CONNECT + INTRO
    def connect_peer(self, host, port):
        key = self.crypto.generate_session_key()
        self.sessions[(host, port)] = key

        intro_packet = {
            "type": "INTRO",
            "address": self.address,
            "pubkey": self.get_pubkey_bytes().hex()
        }

        self.send_raw(host, port, intro_packet)

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

        # DNS resolve
        if ".adaptum" in dst:
            resolved = resolve(dst)
            if not resolved:
                print("Domain not found:", dst)
                return
            dst = resolved

        # 🔐 SIGN MESSAGE
        signature = self.crypto.sign(message)

        packet = {
            "src": self.address,
            "dst": dst,
            "ttl": 5,
            "payload": message,
            "signature": signature
        }

        self.forward(packet)
