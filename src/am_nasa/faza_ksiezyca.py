import math
J2000 = 2451545.0
T_CENT = 36525.0

def moon_phase(jd: float) -> str:
    T = (jd - J2000) / T_CENT
    D = (297.8501921 + 445267.1114034*T - 0.0018819*T**2 + T**3 / 545868 - T**4 / 113065000) % 360
    M = (357.5291092 + 35999.0502909*T - 0.0001536*T**2 + T**3 / 24490000) % 360
    M_ = (134.9633964 + 477198.8675055*T + 0.0087414*T**2 + T**3 / 69699 - T**4 / 14712000) % 360
    F = (93.2720950 + 483202.0175233*T - 0.0036539*T**2 - T**3 / 3526000 + T**4 / 863310000) % 360
    elong = 180 - D - 6.289 * math.sin(math.radians(M_)) + 2.100 * math.sin(math.radians(M)) \
        - 1.274 * math.sin(math.radians(2*D - M_)) - 0.658 * math.sin(math.radians(2*D)) \
        - 0.214 * math.sin(math.radians(2*M_)) - 0.110 * math.sin(math.radians(D))
    phase_value = (1 - math.cos(math.radians(elong))) / 2
    if phase_value < 0.03:
        return "nów"
    elif 0.03 <= phase_value < 0.25:
        return "wzrastający sierp"
    elif 0.25 <= phase_value < 0.47:
        return "pierwsza kwadra"
    elif 0.47 <= phase_value < 0.53:
        return "pełnia"
    elif 0.53 <= phase_value < 0.75:
        return "ostatnia kwadra"
    elif 0.75 <= phase_value < 0.97:
        return "malejący sierp"
    else:
        return "nów"

def moon_phase_value(jd: float) -> float:
    T = (jd - J2000) / T_CENT
    D = (297.8501921 + 445267.1114034*T) % 360
    M_ = (134.9633964 + 477198.8675055*T) % 360
    elong = 180 - D - 6.289 * math.sin(math.radians(M_))
    return (1 - math.cos(math.radians(elong))) / 2
