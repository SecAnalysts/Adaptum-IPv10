from src.node import IPv10Node
import time

A = IPv10Node("127.0.0.1", 5001)
A.peers = [("127.0.0.1", 5002)]
A.start()

time.sleep(1)
A.connect_peer("127.0.0.1", 5002)

time.sleep(2)

A.send_message("node_5003.adaptum", "Hello from Adaptum IPv10 🚀")

while True:
    time.sleep(1)
