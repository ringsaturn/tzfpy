from zoneinfo import ZoneInfo

import arrow

from tzfpy import get_tz

tz = get_tz(139.7744, 35.6812)  # Tokyo

arrow_now = arrow.now(ZoneInfo(tz))
print(arrow_now)
# 2025-04-29T10:33:45.551282+09:00
