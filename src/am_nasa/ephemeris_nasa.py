from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Dict, Any

from skyfield.api import load
from skyfield.positionlib import Geocentric
from skyfield.units import Angle


# Root projektu = AM-NASA-v6/
PROJECT_ROOT = Path(__file__).resolve().parents[2]
EPHEMERIS_DIR = PROJECT_ROOT / "data" / "ephemeris"

# Lista kandydatów – bierzemy pierwszy, który istnieje
EPHEMERIS_CANDIDATES = [
    "de442.bsp",   # Twój główny plik
    "de430.bsp",   # fallback, starsze ale długi zakres
]


def _find_ephemeris_file() -> Path:
    """Znajduje pierwszy istniejący plik efemeryd z listy kandydatów."""
    for name in EPHEMERIS_CANDIDATES:
        candidate = EPHEMERIS_DIR / name
        if candidate.exists():
            return candidate
    raise RuntimeError(
        "Nie znaleziono żadnego pliku efemeryd JPL w data/ephemeris.\n"
        "Oczekiwane nazwy (dowolny z nich): "
        + ", ".join(EPHEMERIS_CANDIDATES)
        + "\nPrzykład: wrzuć de442.bsp i/lub de430.bsp do folderu data/ephemeris."
    )


@lru_cache(maxsize=1)
def _load_ephemeris():
    """Ładuje efemerydy JPL i obiekt timescale, z cache'em."""
    eph_path = _find_ephemeris_file()
    eph = load(str(eph_path))
    ts = load.timescale()
    return eph, ts


def _to_time(jd: float):
    """Konwertuje JD -> obiekt czasu skyfield (TT)."""
    eph, ts = _load_ephemeris()
    # zakładamy, że JD przekazywany do API jest blisko TT; ΔT można dodać później
    t = ts.tt_jd(jd)
    return eph, t


def _geocentric_positions(jd: float) -> Dict[str, Geocentric]:
    """Zwraca geocentryczne pozycje Słońca i Księżyca dla danego JD."""
    eph, t = _to_time(jd)
    earth = eph["earth"]
    sun = earth.at(t).observe(eph["sun"]).apparent()
    moon = earth.at(t).observe(eph["moon"]).apparent()
    return {"sun": sun, "moon": moon}


def _ecliptic_longitude_deg(body: Geocentric) -> float:
    """Ekliptyczna długość geocentryczna w stopniach."""
    ecliptic = body.ecliptic_latlon()
    lon: Angle = ecliptic[1]
    return lon.degrees


def _phase_angle_deg(sun: Geocentric, moon: Geocentric) -> float:
    """Kąt fazy Księżyca w STOPNIACH."""
    # kąt między wektorami Ziemia->Słońce a Ziemia->Księżyc
    return sun.separation_from(moon).degrees


def _moon_illumination(phase_angle_deg: float) -> float:
    """Przybliżona iluminacja (0–1) z kąta fazy.

    Tutaj definiujemy:
    - phase_angle ~ 0   => max iluminacja (pełnia)  -> 1.0
    - phase_angle ~ 180 => min iluminacja (nów)     -> 0.0
    """
    import math

    rad = math.radians(phase_angle_deg)
    return 0.5 * (1.0 + math.cos(rad))


def sun_moon_state_from_jd(jd: float) -> Dict[str, Any]:
    """Zwraca pełen stan Słońce/Księżyc oparty o efemerydy JPL.

    Wynik:
        {
            "sun": { "ra_deg": ..., "dec_deg": ..., "ecliptic_lon_deg": ... },
            "moon": { "ra_deg": ..., "dec_deg": ..., "ecliptic_lon_deg": ... },
            "phase_angle_deg": ...,
            "elongation_deg": ...,
            "illumination": ...,
        }
    """
    pos = _geocentric_positions(jd)
    sun = pos["sun"]
    moon = pos["moon"]

    # RA/Dec
    ra_sun, dec_sun, _ = sun.radec()
    ra_moon, dec_moon, _ = moon.radec()

    # ekliptyczne długości
    lam_sun = _ecliptic_longitude_deg(sun)
    lam_moon = _ecliptic_longitude_deg(moon)

    # kąt fazy i elongacja
    phase_angle = _phase_angle_deg(sun, moon)
    elongation = moon.separation_from(sun).degrees  # praktycznie to samo co phase_angle

    illum = _moon_illumination(phase_angle)

    return {
        "sun": {
            "ra_deg": ra_sun.hours * 15.0,
            "dec_deg": dec_sun.degrees,
            "ecliptic_lon_deg": lam_sun,
        },
        "moon": {
            "ra_deg": ra_moon.hours * 15.0,
            "dec_deg": dec_moon.degrees,
            "ecliptic_lon_deg": lam_moon,
        },
        "phase_angle_deg": phase_angle,
        "elongation_deg": elongation,
        "illumination": illum,
    }


def moon_phase_name_from_nasa(jd: float) -> str:
    """Prosty label fazy na podstawie kąta fazy z efemeryd NASA."""
    state = sun_moon_state_from_jd(jd)
    phase = state["phase_angle_deg"]

    # Zgrubne klasy faz na podstawie kąta:
    if phase < 30:
        return "pełnia"
    elif phase < 60:
        return "garb"
    elif phase < 120:
        return "kwadra"
    elif phase < 150:
        return "sierp"
    else:
        return "blisko nowiu"
