import json
import argparse
import logging
import time

from src.node import IPv10Node

# CLI
parser = argparse.ArgumentParser()
parser.add_argument("--config", required=True)
args = parser.parse_args()

# logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# load config
with open(args.config) as f:
    config = json.load(f)

node = IPv10Node(config)
node.start()

# demo send (optional)
time.sleep(3)

# contoh kirim
# node.send_message("nodeC.adaptum", "Hello from production node 🚀")

while True:
    time.sleep(1)
