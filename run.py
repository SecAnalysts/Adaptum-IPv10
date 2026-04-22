import json
import argparse
import logging
import time

from src.node import IPv10Node

parser = argparse.ArgumentParser()
parser.add_argument("--config", required=True)
args = parser.parse_args()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

with open(args.config) as f:
    config = json.load(f)

node = IPv10Node(config)
node.start()

time.sleep(3)

# optional test
# node.send_message("nodeC.adaptum", "Hello Adaptum 🚀")

while True:
    time.sleep(1)
