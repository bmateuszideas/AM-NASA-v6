from __future__ import annotations

from typing import Dict, Any

from skyfield.api import wgs84

from .ephemeris_nasa import _load_ephemeris, sun_moon_state_from_jd


def _sun_moon_altaz(
    jd: float,
    lat_deg: float,
    lon_deg: float,
    elevation_m: float = 0.0,
) -> Dict[str, float]:
    """Zwraca wysokości i azymuty Słońca i Księżyca dla danej lokalizacji i JD."""
    eph, ts = _load_ephemeris()
    t = ts.tt_jd(jd)

    earth = eph["earth"]
    topos = wgs84.latlon(lat_deg, lon_deg, elevation_m=elevation_m)
    location = earth + topos

    sun_app = location.at(t).observe(eph["sun"]).apparent()
    moon_app = location.at(t).observe(eph["moon"]).apparent()

    alt_sun, az_sun, _ = sun_app.altaz()
    alt_moon, az_moon, _ = moon_app.altaz()

    return {
        "sun_alt_deg": alt_sun.degrees,
        "sun_az_deg": az_sun.degrees,
        "moon_alt_deg": alt_moon.degrees,
        "moon_az_deg": az_moon.degrees,
    }


def _solar_disk_coverage_fraction(jd: float, lat_deg: float, lon_deg: float, elevation_m: float = 0.0) -> float:
    """Przybliżony procent zakrycia tarczy Słońca (0–1) dla danej lokalizacji i JD.

    Liczymy:
    - promienie kątowe Słońca i Księżyca,
    - separację kątową ich środków,
    - pole części wspólnej dwóch kół / pole koła Słońca.
    """
    import math

    eph, ts = _load_ephemeris()
    t = ts.tt_jd(jd)

    earth = eph["earth"]
    topos = wgs84.latlon(lat_deg, lon_deg, elevation_m=elevation_m)
    location = earth + topos

    sun_app = location.at(t).observe(eph["sun"]).apparent()
    moon_app = location.at(t).observe(eph["moon"]).apparent()

    # separacja kątowa środków tarcz
    center_sep_deg = sun_app.separation_from(moon_app).degrees
    center_sep = math.radians(center_sep_deg)

    # promienie kątowe (radiany)
    sun_radius = sun_app.angular_radius().radians
    moon_radius = moon_app.angular_radius().radians

    # jeśli bardzo daleko od siebie -> brak zakrycia
    if center_sep >= sun_radius + moon_radius:
        return 0.0

    # jeśli Księżyc całkowicie zakrywa tarczę Słońca -> 100%
    if moon_radius >= sun_radius and center_sep <= abs(moon_radius - sun_radius):
        return 1.0

    # jeśli tarcza Księżyca w całości w tarczy Słońca -> procent < 100%
    if sun_radius >= moon_radius and center_sep <= abs(sun_radius - moon_radius):
        # stosunek pól
        return (moon_radius**2) / (sun_radius**2)

    # część wspólna dwóch okręgów
    r, R, d = sun_radius, moon_radius, center_sep

    # zabezpieczenie numerów
    if d <= 0:
        # środki pokrywają się
        return min(1.0, (min(r, R) ** 2) / (r ** 2))

    alpha = 2 * math.acos((d * d + r * r - R * R) / (2 * d * r))
    beta = 2 * math.acos((d * d + R * R - r * r) / (2 * d * R))

    area1 = 0.5 * r * r * (alpha - math.sin(alpha))
    area2 = 0.5 * R * R * (beta - math.sin(beta))
    overlap_area = area1 + area2

    sun_area = math.pi * r * r
    frac = overlap_area / sun_area if sun_area > 0 else 0.0
    return max(0.0, min(1.0, frac))


def classify_solar_eclipse_from_state(state: Dict[str, Any]) -> str | None:
    """Prosta klasyfikacja typu zaćmienia Słońca na podstawie globalnej geometrii.

    Uproszczone:
    - jeśli iluminacja > ~0.4 -> nie nów, więc brak globalnego zaćmienia,
    - jeśli elongacja > ~2°  -> za daleko, brak globalnego zaćmienia,
    - jeśli elongacja < 0.5° -> 'centralne' (totalne/obrączkowe/hybrydowe),
    - jeśli 0.5°–2°         -> 'częściowe'.
    """
    illum = state["illumination"]         # 0 = nów, 1 = pełnia (wg naszej definicji)
    elong = state["elongation_deg"]

    if illum > 0.4:
        return None
    if elong > 2.0:
        return None
    if elong < 0.5:
        return "centralne"
    return "częściowe"


def solar_eclipse_visibility(
    jd: float,
    lat_deg: float,
    lon_deg: float,
    elevation_m: float = 0.0,
) -> Dict[str, Any]:
    """Czy zaćmienie Słońca jest widoczne z danej lokalizacji o podanym JD?

    Zakładamy, że JD to czas maksymalnego zaćmienia (np. z NASA/GSFC).
    """

    state = sun_moon_state_from_jd(jd)
    altaz = _sun_moon_altaz(jd, lat_deg, lon_deg, elevation_m=elevation_m)

    global_class = classify_solar_eclipse_from_state(state)

    sun_up = altaz["sun_alt_deg"] > 0.0
    moon_up = altaz["moon_alt_deg"] > 0.0

    # lokalny procent zakrycia
    coverage_frac = 0.0
    if sun_up and moon_up and global_class is not None:
        coverage_frac = _solar_disk_coverage_fraction(jd, lat_deg, lon_deg, elevation_m=elevation_m)

    visible = global_class is not None and sun_up and moon_up and coverage_frac > 0.0

    return {
        "jd": jd,
        "type": "solar",
        "visible": visible,
        "classification_global": global_class,  # None / 'centralne' / 'częściowe'
        "coverage_fraction": coverage_frac,
        "coverage_percent": coverage_frac * 100.0,
        "sun_alt_deg": altaz["sun_alt_deg"],
        "sun_az_deg": altaz["sun_az_deg"],
        "moon_alt_deg": altaz["moon_alt_deg"],
        "moon_az_deg": altaz["moon_az_deg"],
        "illumination": state["illumination"],
        "phase_angle_deg": state["phase_angle_deg"],
        "elongation_deg": state["elongation_deg"],
        "sun_ecliptic_lon_deg": state["sun"]["ecliptic_lon_deg"],
        "moon_ecliptic_lon_deg": state["moon"]["ecliptic_lon_deg"],
    }


def lunar_eclipse_visibility(
    jd: float,
    lat_deg: float,
    lon_deg: float,
    elevation_m: float = 0.0,
) -> Dict[str, Any]:
    """Czy zaćmienie Księżyca jest widoczne z danej lokalizacji o podanym JD?

    Uproszczone podejście:
    - Zakładamy, że JD to moment maksymalny zaćmienia (z NASA/GSFC).
    - Księżyc musi być powyżej horyzontu (alt > 0).
    - Illuminacja ~1 (pełnia), kąt fazy blisko 180°.
    """

    state = sun_moon_state_from_jd(jd)
    altaz = _sun_moon_altaz(jd, lat_deg, lon_deg, elevation_m=elevation_m)

    illum = state["illumination"]        # ~1 przy pełni, ~0 przy nowiu
    phase_angle = state["phase_angle_deg"]

    # heurystyka: pełnia i przeciwległa geometria
    near_full = illum > 0.9
    near_opposition = phase_angle > 150.0

    moon_up = altaz["moon_alt_deg"] > 0.0

    visible = near_full and near_opposition and moon_up

    # Tu nie rozróżniamy częściowe/całkowite – do tego potrzebne są Besseliany.
    classification = "możliwe" if visible else None

    return {
        "jd": jd,
        "type": "lunar",
        "visible": visible,
        "classification": classification,
        "sun_alt_deg": altaz["sun_alt_deg"],
        "sun_az_deg": altaz["sun_az_deg"],
        "moon_alt_deg": altaz["moon_alt_deg"],
        "moon_az_deg": altaz["moon_az_deg"],
        "illumination": state["illumination"],
        "phase_angle_deg": state["phase_angle_deg"],
        "elongation_deg": state["elongation_deg"],
        "sun_ecliptic_lon_deg": state["sun"]["ecliptic_lon_deg"],
        "moon_ecliptic_lon_deg": state["moon"]["ecliptic_lon_deg"],
    }
