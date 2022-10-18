import datetime
from typing import Literal

TimestampStyle = Literal["f", "F", "d", "D", "t", "T", "R"]


def utcnow() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def format_dt(
    datetime_object: datetime.datetime, /, style: TimestampStyle | None = None
) -> str:
    return (
        f"<t:{int(datetime_object.timestamp())}>"
        if style is None
        else f"<t:{int(datetime_object.timestamp())}:{style}>"
    )
