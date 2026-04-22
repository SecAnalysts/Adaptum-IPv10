DNS_TABLE = {
    "nodeA.adaptum": None,
    "nodeB.adaptum": None,
    "nodeC.adaptum": None,
}

def register(name, address):
    DNS_TABLE[name] = address

def resolve(name):
    return DNS_TABLE.get(name)
