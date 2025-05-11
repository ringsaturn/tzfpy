from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from tzfpy import get_tz

tz = get_tz(139.7744, 35.6812)  # Tokyo

now = datetime.now(timezone.utc)
now = now.replace(tzinfo=ZoneInfo(tz))
print(now)
# 2025-04-29 01:33:56.325194+09:00
