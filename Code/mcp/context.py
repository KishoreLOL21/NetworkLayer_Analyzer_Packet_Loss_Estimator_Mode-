class MCPContext:
    def __init__(self):
        self.memory = {
            "short_term": {},
            "long_term": {
                "history": [],
                "logs": []
            }
        }

    def update(self, key, value, memory_type="short_term"):
        self.memory[memory_type][key] = value

    def get(self, key, default=None, memory_type="short_term"):
        return self.memory[memory_type].get(key, default)

    def append(self, key, value, memory_type="long_term"):
        if key not in self.memory[memory_type]:
            self.memory[memory_type][key] = []
        self.memory[memory_type][key].append(value)

    def dump(self):
        return self.memory