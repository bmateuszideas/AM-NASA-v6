import math
J2000 = 2451545.0
T_CENT = 36525.0

def sun_ecliptic_longitude(jd: float) -> float:
    T = (jd - J2000) / T_CENT
    L0 = 280.46646 + 36000.76983*T + 0.0003032*T**2
    M = 357.52911 + 35999.05029*T - 0.0001537*T**2
    C = (1.914602 - 0.004817*T - 0.000014*T**2)*math.sin(math.radians(M))
    C += (0.019993 - 0.000101*T)*math.sin(math.radians(2*M))
    C += 0.000289*math.sin(math.radians(3*M))
    true_long = L0 + C
    return true_long % 360

def moon_ecliptic_longitude(jd: float) -> float:
    T = (jd - J2000) / T_CENT
    L0 = 218.3164477 + 481267.88123421*T - 0.0015786*T**2
    M = 357.5291092 + 35999.0502909*T - 0.0001536*T**2
    M_ = 134.9633964 + 477198.8675055*T + 0.0087414*T**2
    D = 297.8501921 + 445267.1114034*T - 0.0018819*T**2
    F = 93.2720950 + 483202.0175233*T - 0.0036539*T**2
    lon = L0 + 6.289*math.sin(math.radians(M_))
    lon += 1.274*math.sin(math.radians(2*D - M_))
    lon += 0.658*math.sin(math.radians(2*D))
    lon += 0.214*math.sin(math.radians(2*M_))
    lon -= 0.186*math.sin(math.radians(M))
    return lon % 360

def elongacja_slonca_ksiezyca(jd: float) -> float:
    sun = sun_ecliptic_longitude(jd)
    moon = moon_ecliptic_longitude(jd)
    elong = (moon - sun + 360) % 360
    if elong > 180:
        elong = 360 - elong
    return elong

def jasnosc_ksiezyca(jd: float) -> float:
    elong = elongacja_slonca_ksiezyca(jd)
    return (1 + math.cos(math.radians(elong))) / 2
