from django.utils import timezone
from django.core.cache import cache

def _cache_gate(key: str, minutes: int) -> bool:
    now = timezone.now()

    added = cache.add(key, now, minutes * 60)
    if added:
        return True

    last = cache.get(key)
    if last and (now - last).total_seconds() >= minutes * 60:
        cache.set(key, now, minutes * 60)
        return True
    
    return False