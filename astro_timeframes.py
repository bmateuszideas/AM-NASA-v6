
import math

SECONDS_PER_DAY = 86400.0
J2000 = 2451545.0
T_CENT = 36525.0

def julian_centuries(jd):
    """Oblicza liczbę stuleci juliańskich od epoki J2000."""
    return (jd - J2000) / T_CENT

def precession_iau2006(T):
    """Zwraca kąty precesji IAU 2006 (zeta, z, theta) w radianach."""
    zeta = (2306.2181 + 1.39656*T - 0.000139*T**2) * T
    z = zeta
    theta = (2004.3109 - 0.85330*T - 0.000217*T**2) * T
    return math.radians(zeta/3600), math.radians(z/3600), math.radians(theta/3600)


# Funkcja tt_to_ut usunięta — brak korekt ΔT w wersji deterministycznej

def tdb_from_tt(jd_tt):
    """Konwertuje czas TT na TDB wg wzoru IAU 2010."""
    T = julian_centuries(jd_tt)
    M = math.radians((357.5277233 + 35999.05034*T) % 360)
    return jd_tt + (0.001658*math.sin(M) + 0.000014*math.sin(2*M)) / SECONDS_PER_DAY