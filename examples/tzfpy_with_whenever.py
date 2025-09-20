from whenever import Instant

from tzfpy import get_tz

now = Instant.now()

tz = get_tz(139.7744, 35.6812)  # Tokyo

now = now.to_tz(tz)

print(now)
# 2025-04-29T10:33:28.427784+09:00[Asia/Tokyo]
