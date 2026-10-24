"""Hand-written O(1) LRU cache using a hash map + doubly linked list.

Intentionally NOT using functools.lru_cache: this is the "algorithm evidence"
piece of the project. get/put are O(1) because the dict gives O(1) node lookup
and the linked list gives O(1) reorder/eviction via pointer surgery.
"""


class _Node:
    __slots__ = ("key", "value", "prev", "next")

    def __init__(self, key=None, value=None):
        self.key = key
        self.value = value
        self.prev = None
        self.next = None


class LRUCache:
    def __init__(self, capacity: int):
        if capacity < 1:
            raise ValueError("capacity must be >= 1")
        self.capacity = capacity
        self.cache: dict = {}  # key -> _Node
        self.hits = 0
        self.misses = 0
        # Sentinel head/tail so we never special-case the ends.
        self.head = _Node()
        self.tail = _Node()
        self.head.next = self.tail
        self.tail.prev = self.head

    # --- internal pointer surgery -------------------------------------------------
    def _remove(self, node: _Node) -> None:
        node.prev.next = node.next
        node.next.prev = node.prev

    def _add_front(self, node: _Node) -> None:
        node.next = self.head.next
        node.prev = self.head
        self.head.next.prev = node
        self.head.next = node

    # --- public API ---------------------------------------------------------------
    def get(self, key):
        node = self.cache.get(key)
        if node is None:
            self.misses += 1
            return None
        self._remove(node)
        self._add_front(node)
        self.hits += 1
        return node.value

    def put(self, key, value) -> None:
        node = self.cache.get(key)
        if node is not None:
            node.value = value
            self._remove(node)
            self._add_front(node)
            return
        node = _Node(key, value)
        self.cache[key] = node
        self._add_front(node)
        if len(self.cache) > self.capacity:
            lru = self.tail.prev
            self._remove(lru)
            del self.cache[lru.key]

    def clear(self) -> None:
        self.cache.clear()
        self.head.next = self.tail
        self.tail.prev = self.head
        self.hits = 0
        self.misses = 0

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total else 0.0

    def __contains__(self, key) -> bool:
        return key in self.cache

    def __len__(self) -> int:
        return len(self.cache)
