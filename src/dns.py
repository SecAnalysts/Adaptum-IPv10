DNS_TABLE = {}

def register(name, address):
    DNS_TABLE[name] = address

def resolve(name):
    return DNS_TABLE.get(name)

def merge(records):
    for k, v in records.items():
        DNS_TABLE[k] = v

def export():
    return DNS_TABLE.copy()
