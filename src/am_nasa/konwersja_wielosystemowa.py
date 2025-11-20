import math
from .am_core import jd_from_am, am_from_jd
from .kalendarze_lunisolarne import (
    jd_from_islamic,
    jd_from_persian,
    jd_from_chinese,
    jd_from_hindu,
    jd_from_coptic,
    jd_from_ethiopian,
    jd_from_french_rev,
    jd_from_maya,
)


def jd_from_julian(year: int, month: int, day: int) -> float:
    a = (14 - month) // 12
    y = year + 4800 - a
    m = month + 12 * a - 3
    jd = day + ((153 * m + 2) // 5) + 365 * y + y // 4 - 32083
    return jd + 0.5


def jd_from_gregorian(year: int, month: int, day: int) -> float:
    a = (14 - month) // 12
    y = year + 4800 - a
    m = month + 12 * a - 3
    jd = day + ((153 * m + 2) // 5) + 365 * y + y // 4 - y // 100 + y // 400 - 32045
    return jd + 0.5


def konwertuj(data: dict) -> dict:
    """
    Centralna funkcja: system + rok/miesiąc/dzień -> JD, AM.

    data = {
        "system": "gregorian" | "julian" | ... | "am",
        "year": int,
        "month": int,
        "day": int lub float (dla AM: AM-day),
    }
    """
    system = data["system"].lower()
    year = int(data["year"])
    month = int(data["month"])
    day = data["day"]

    if system == "gregorian":
        jd = jd_from_gregorian(year, month, int(day))
    elif system == "julian":
        jd = jd_from_julian(year, month, int(day))
    elif system == "islamic":
        jd = jd_from_islamic(year, month, int(day))
    elif system == "persian":
        jd = jd_from_persian(year, month, int(day))
    elif system == "chinese":
        jd = jd_from_chinese(year, month, int(day))
    elif system == "hindu":
        jd = jd_from_hindu(year, month, int(day))
    elif system == "coptic":
        jd = jd_from_coptic(year, month, int(day))
    elif system == "ethiopian":
        jd = jd_from_ethiopian(year, month, int(day))
    elif system == "french_rev":
        jd = jd_from_french_rev(year, month, int(day))
    elif system == "maya":
        jd = jd_from_maya(year, month, int(day))
    elif system == "am":
        jd = jd_from_am(float(day), year)
    else:
        raise ValueError(f"Nieznany system kalendarzowy: {system}")

    am_day = am_from_jd(jd, year)
    return {
        "JD": jd,
        "AM": am_day,
    }
