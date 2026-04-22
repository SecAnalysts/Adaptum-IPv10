from src.node import IPv10Node
import time

B = IPv10Node("127.0.0.1", 5002)
B.peers = [
    ("127.0.0.1", 5001),
    ("127.0.0.1", 5003)
]
B.start()

time.sleep(1)
B.connect_peer("127.0.0.1", 5001)
B.connect_peer("127.0.0.1", 5003)

while True: time.sleep(1)
