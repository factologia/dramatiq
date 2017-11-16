import time

from .rate_limiter import RateLimiter


class BucketRateLimiter(RateLimiter):
    """A rate limiter that ensures that only up to `limit` operations
    may happen over some time interval.

    Examples:

      Up to 10 operations every second:

      >>> BucketRateLimiter(backend, "some-key", limit=10, bucket=1_000)

      Up to 1 operation every minute:

      >>> BucketRateLimiter(backend, "some-key", limit=1, bucket=60_000)

    Warning:

      Bucket rate limits are cheap to maintain but are susceptible to
      burst "attacks".  Given a bucket rate limit of 100 per minute,
      an attacker could make a burst of 100 calls in the last second
      of a minute and then another 100 calls in the first second of
      the subsequent minute.

      For a rate limiter that doesn't have this problem (but is more
      expensive to maintain), see |WindowRateLimiter|.

    Parameters:
      backend(RateLimiterBackend): The backend to use.
      key(str): The key to rate limit on.
      limit(int): The maximum number of operations per bucket per key.
      bucket(int): The bucket interval in milliseconds.

    .. |WindowRateLimiter| replace:: :class:`WindowRateLimiter<dramatiq.rate_limits.WindowRateLimiter>`
    """

    def __init__(self, backend, key, *, limit=1, bucket=1000):
        assert limit >= 1, "limit must be positive"

        super().__init__(backend, key)
        self.limit = limit
        self.bucket = bucket

    def _acquire(self):
        timestamp = int(time.time() * 1000)
        current_timestamp = timestamp - (timestamp % self.bucket)
        current_key = "%s@%d" % (self.key, current_timestamp)
        added = self.backend.add(current_key, 1, ttl=self.bucket)
        if added:
            return True

        return self.backend.incr(current_key, 1, maximum=self.limit, ttl=self.bucket)

    def _release(self):
        pass
