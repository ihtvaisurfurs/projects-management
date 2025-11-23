import re
from datetime import datetime
from typing import Optional

from core.constants import DATE_FORMATS

PHONE_PATTERN = re.compile(r"^\+\d{10,15}$")
DATE_PATTERN = re.compile(r"^\d{4}([/-])(0[1-9]|1[0-2])\1(0[1-9]|[12][0-9]|3[01])$")
VERSION_PATTERN = re.compile(r"^\d+(?:\.\d+)*$")


def is_valid_phone(phone: str) -> bool:
    return bool(PHONE_PATTERN.match(phone.strip()))


def parse_date(value: str) -> Optional[str]:
    value = value.strip()
    if not DATE_PATTERN.match(value):
        return None
    for fmt in DATE_FORMATS:
        try:
            dt = datetime.strptime(value, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def parse_start_date(value: str) -> Optional[str]:
    return parse_date(value)


def parse_version(value: str) -> Optional[str]:
    cleaned = value.strip()
    if not VERSION_PATTERN.match(cleaned):
        return None
    return cleaned
