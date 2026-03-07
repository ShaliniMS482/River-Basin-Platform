from django.core.cache import cache

def make_cache_key(prefix, **kwargs):
    key_parts = [prefix] + [f"{k}:{v}" for k, v in kwargs.items()]
    return ":".join(key_parts)

def invalidate_basin_cache(basin_id):
    cache.delete_pattern(f"basin:{basin_id}:timeseries*")
    cache.delete_pattern(f"basin:{basin_id}:events*")
    cache.delete_pattern(f"basin:{basin_id}:summary*")