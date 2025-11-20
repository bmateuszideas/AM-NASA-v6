import math

def jd_from_french_rev(year: int, month: int, day: int) -> float:
    jd_epoch = 2375839.5
    jd = jd_epoch + (year - 1) * 365 + math.floor((year - 1) / 4)
    jd += (month - 1) * 30 + (day - 1)
    return jd

def jd_from_maya(haab_year: int, haab_month: int, haab_day: int) -> float:
    GMT_CORR = 584283.5
    total_days = haab_year * 365 + haab_month * 20 + haab_day
    return GMT_CORR + total_days

def jd_from_islamic(year: int, month: int, day: int) -> float:
    return (day +
            math.ceil(29.5 * (month - 1)) +
            (year - 1) * 354 +
            math.floor((3 + 11 * year) / 30) +
            1948439.5)

def jd_from_persian(year: int, month: int, day: int) -> float:
    epbase = year - (474 if year >= 0 else 473)
    epyear = 474 + (epbase % 2820)
    jd = day + (month <= 7 and (month - 1) * 31 or ((month - 1) * 30 + 6))
    jd += math.floor((epyear * 682 - 110) / 2816) + (epyear - 1) * 365
    jd += math.floor(epbase / 2820) * 1029983 + 1948320.5
    return jd

def jd_from_chinese(year: int, month: int, day: int) -> float:
    base = 758325.5
    days = (year - 1) * 365.2422 + (month - 1) * 29.5306 + (day - 1)
    return base + days

def jd_from_hindu(year: int, month: int, day: int) -> float:
    base = 588465.5
    days = (year * 365.25875) + ((month - 1) * 30.438) + (day - 1)
    return base + days

def jd_from_coptic(year: int, month: int, day: int) -> float:
    return 1824665.5 + 365 * (year - 1) + math.floor((year - 1) / 4) + 30 * (month - 1) + day - 1

def jd_from_ethiopian(year: int, month: int, day: int) -> float:
    return jd_from_coptic(year - 8, month, day)
