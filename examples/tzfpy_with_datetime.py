from datetime import UTC as DT_UTC
from datetime import datetime
from zoneinfo import ZoneInfo

from tzfpy import get_tz

tz = get_tz(139.7744, 35.6812)  # Tokyo

now = datetime.now(DT_UTC)
now = now.replace(tzinfo=ZoneInfo(tz))
print(now)
