from app.cache.lru import LRUCache


def test_get_missing_returns_none():
    c = LRUCache(2)
    assert c.get("a") is None
    assert c.misses == 1
    assert c.hits == 0


def test_put_and_get():
    c = LRUCache(2)
    c.put("a", 1)
    assert c.get("a") == 1
    assert c.hits == 1


def test_eviction_is_lru_order():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    assert c.get("a") == 1  # a becomes most-recently-used; b is now LRU
    c.put("c", 3)  # evicts b
    assert c.get("b") is None
    assert c.get("a") == 1
    assert c.get("c") == 3


def test_put_updates_value_and_recency():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    c.put("a", 10)  # update + refresh
    c.put("c", 3)  # evicts b (LRU)
    assert c.get("b") is None
    assert c.get("a") == 10
    assert c.get("c") == 3


def test_capacity_is_enforced():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    c.put("c", 3)  # evicts a (LRU)
    assert len(c) == 2
    assert c.get("a") is None
    assert c.get("b") == 2
    assert c.get("c") == 3


def test_clear_resets_state():
    c = LRUCache(3)
    c.put("a", 1)
    c.get("x")  # miss
    c.clear()
    assert len(c) == 0
    assert c.hits == 0
    assert c.misses == 0
    assert c.get("a") is None  # a new miss after clearing
    assert c.misses == 1


def test_hit_rate():
    c = LRUCache(2)
    c.put("a", 1)
    c.get("a")  # hit
    c.get("x")  # miss
    assert c.hit_rate == 0.5
