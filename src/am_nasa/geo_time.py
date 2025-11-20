import math

def local_time_from_jd(jd: float, longitude_deg: float):
    offset_days = longitude_deg / 360.0
    jd_local = jd + offset_days
    frac = jd_local % 1
    hours = frac * 24
    return jd_local, hours

def local_date_string(jd: float, longitude_deg: float) -> str:
    jd_local, hours = local_time_from_jd(jd, longitude_deg)
    total_minutes = hours * 60
    hh = int(total_minutes // 60)
    mm = int(total_minutes % 60)
    jd_days = int(jd_local + 0.5)
    F = jd_local + 0.5 - jd_days
    if jd_days >= 2299161:
        a = int((jd_days - 1867216.25)/36524.25)
        jd_days += 1 + a - int(a/4)
    b = jd_days + 1524
    c = int((b - 122.1)/365.25)
    d = int(365.25 * c)
    e = int((b - d)/30.6001)
    day = b - d - int(30.6001*e) + F
    month = e - 1 if e < 14 else e - 13
    year = c - 4716 if month > 2 else c - 4715
    return f"{year:04d}-{month:02d}-{int(day):02d} {hh:02d}:{mm:02d}"
