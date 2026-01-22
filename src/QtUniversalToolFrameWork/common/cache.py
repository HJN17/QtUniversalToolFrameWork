
# coding:utf-8

from collections import OrderedDict 

class LRUCache:

    """
    LRU缓存实现类，用于缓存最近使用的图片。
    当缓存满时，会移除最近最少使用的项。
    """
    
    def __init__(self, capacity: int = 300):
        self.cache = OrderedDict()
        self.capacity = capacity

    def keys(self):
        return self.cache.keys()

    def get(self, key: str):
        if key not in self.cache:
            return None
        
        self.cache.move_to_end(key)

        return self.cache[key]

    def put(self, key: str, value: object): 
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)
    
    def delete(self, key: str):
        if key in self.cache:
            del self.cache[key]

    def clear(self):
        self.cache.clear()

    def size(self):
        return len(self.cache.keys())