import time


class SearchCache:
    def __init__(self, ttl=3600):
        self.cache = {}
        self.ttl = ttl

    def get(self, key):
        if key in self.cache:
            result, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return result
            else:
                del self.cache[key]
        return None

    def set(self, key, value):
        self.cache[key] = (value, time.time())
