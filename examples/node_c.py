from src.node import IPv10Node
import time

C = IPv10Node("127.0.0.1", 5003)
C.peers = [("127.0.0.1", 5002)]
C.start()

time.sleep(1)
C.connect_peer("127.0.0.1", 5002)

print("Node C address:", C.address)

while True: time.sleep(1)
