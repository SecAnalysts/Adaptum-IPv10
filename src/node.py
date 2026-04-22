import socket
import threading
import json
import hashlib
import logging

from crypto import CryptoManager
from dns import register, resolve


class IPv10Node:
    def __init__(self, config):
        self.host = config["host"]
        self.port = config["port"]
        self.name = config["name"]
        self.peers = config.get("peers", [])

        self.crypto = CryptoManager()
        self.address = self.generate_address()

        register(self.name, self.address)

        self.sessions = {}
        self.known_nodes = {}

        logging.info(f"{self.name} initialized ({self.address[:10]})")

    def generate_address(self):
        pub = self.crypto.public_key.public_bytes_raw()
        return hashlib.sha256(pub).hexdigest()

    def get_pubkey_bytes(self):
        return self.crypto.public_key.public_bytes_raw()

    def start(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((self.host, self.port))
        server.listen(5)

        logging.info(f"{self.name} listening on {self.host}:{self.port}")

        threading.Thread(target=self.listen, args=(server,), daemon=True).start()

        # auto connect peers
        for peer in self.peers:
            self.connect_peer(peer[0], peer[1])

    def listen(self, server):
        while True:
            try:
                conn, addr = server.accept()
                data = conn.recv(8192)

                if data:
                    packet = json.loads(data.decode())
                    self.handle(packet, addr)

                conn.close()
            except Exception as e:
                logging.error(f"Listen error: {e}")

    def handle(self, packet, addr):

        if packet["type"] == "INTRO":
            node_addr = packet["address"]
            pubkey = bytes.fromhex(packet["pubkey"])

            self.known_nodes[node_addr] = pubkey
            logging.info(f"Registered node {node_addr[:8]}")
            return

        if packet["type"] == "DATA":
            key = self.sessions.get(addr)
            if not key:
                return

            try:
                decrypted = self.crypto.decrypt(key, packet["payload"])
                inner = json.loads(decrypted)

                sender = inner["src"]
                signature = inner.get("signature")
                payload = inner["payload"]

                pubkey = self.known_nodes.get(sender)

                if not pubkey:
                    logging.warning("Unknown sender, dropped")
                    return

                self.crypto.verify(pubkey, signature, payload)

                if inner["dst"] == self.address:
                    logging.info(f"RECEIVED: {payload}")
                else:
                    inner["ttl"] -= 1
                    if inner["ttl"] > 0:
                        self.forward(inner, exclude=addr)

            except Exception as e:
                logging.warning(f"Invalid packet: {e}")

    def send_raw(self, host, port, packet):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((host, port))
            s.send(json.dumps(packet).encode())
            s.close()
        except Exception as e:
            logging.error(f"Send error: {e}")

    def connect_peer(self, host, port):
        key = self.crypto.generate_session_key()
        self.sessions[(host, port)] = key

        intro = {
            "type": "INTRO",
            "address": self.address,
            "pubkey": self.get_pubkey_bytes().hex()
        }

        self.send_raw(host, port, intro)
        logging.info(f"Connected to {host}:{port}")

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
            if exclude and tuple(peer) == tuple(exclude):
                continue
            self.send_secure(peer[0], peer[1], packet)

    def send_message(self, dst, message):

        if ".adaptum" in dst:
            resolved = resolve(dst)
            if not resolved:
                logging.warning(f"Domain not found: {dst}")
                return
            dst = resolved

        signature = self.crypto.sign(message)

        packet = {
            "src": self.address,
            "dst": dst,
            "ttl": 5,
            "payload": message,
            "signature": signature
        }

        self.forward(packet)
