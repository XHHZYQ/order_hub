"""时间工具：统一 UTC 存储、按应用时区格式化输出（YYYY-MM-DD HH:mm:ss）。"""

from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from app.core.config import settings

APP_TZ = ZoneInfo(settings.TIMEZONE)

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def now_utc() -> datetime:
    """当前 UTC 时间（aware）。"""
    return datetime.now(timezone.utc)


def to_local(dt: datetime | None) -> datetime | None:
    """把 datetime 归一到应用时区（naive 视为 UTC）。"""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(APP_TZ)


def format_datetime(dt: datetime | None) -> str | None:
    """格式化为 YYYY-MM-DD HH:mm:ss（接口出参口径）。"""
    if dt is None:
        return None
    local = to_local(dt)
    return local.strftime(DATETIME_FORMAT)


def parse_datetime(value: str | datetime | date | None) -> datetime | None:
    """解析入参时间，返回 aware UTC datetime。

    支持 "YYYY-MM-DD HH:mm:ss"、"YYYY-MM-DD" 以及 ISO 8601；
    无时区信息时按应用时区解释。
    """
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=APP_TZ).astimezone(timezone.utc)
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day, tzinfo=APP_TZ).astimezone(timezone.utc)

    text = str(value).strip()
    parsed: datetime | None = None
    for fmt in (DATETIME_FORMAT, "%Y-%m-%d", "%Y/%m/%d %H:%M:%S", "%Y/%m/%d"):
        try:
            parsed = datetime.strptime(text, fmt)
            break
        except ValueError:
            continue
    if parsed is None:
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=APP_TZ)
    return parsed.astimezone(timezone.utc)
