from __future__ import annotations

from typing import Dict, Any

from .konwersja_wielosystemowa import konwertuj
from .am_core import am_from_jd
from .geo_time import local_time_from_jd, local_date_string
from .ephemeris_nasa import sun_moon_state_from_jd, moon_phase_name_from_nasa
from .eclipses import solar_eclipse_visibility, lunar_eclipse_visibility


def convert_calendar_date(
    system: str,
    year: int,
    month: int,
    day: float,
    lon: float = 0.0,
) -> Dict[str, Any]:
    """High-level: data w dowolnym kalendarzu -> JD, AM + info astro (NASA)."""

    payload = {
        "system": system.lower(),
        "year": year,
        "month": month,
        "day": day,
    }

    base = konwertuj(payload)
    jd = float(base["JD"])
    am = float(base["AM"])

    jd_local, local_hours = local_time_from_jd(jd, lon)
    local_dt_str = local_date_string(jd, lon)

    nasa_state = sun_moon_state_from_jd(jd)
    phase_name = moon_phase_name_from_nasa(jd)

    return {
        "input": {
            "system": system,
            "year": year,
            "month": month,
            "day": day,
            "lon": lon,
        },
        "time": {
            "JD": jd,
            "AM": am,
            "local_hours": local_hours,
            "local_datetime": local_dt_str,
        },
        "moon": {
            "phase_name": phase_name,
            "phase_angle_deg": nasa_state["phase_angle_deg"],
            "illumination": nasa_state["illumination"],
        },
        "geometry": {
            "elongation_deg": nasa_state["elongation_deg"],
            "sun_ecliptic_lon_deg": nasa_state["sun"]["ecliptic_lon_deg"],
            "moon_ecliptic_lon_deg": nasa_state["moon"]["ecliptic_lon_deg"],
        },
    }


def info_from_jd(
    jd: float,
    year: int,
    lon: float = 0.0,
) -> Dict[str, Any]:
    """JD -> AM + info astro na bazie NASA (bez kalendarza wejściowego)."""

    am = am_from_jd(jd, year)

    jd_local, local_hours = local_time_from_jd(jd, lon)
    local_dt_str = local_date_string(jd, lon)

    nasa_state = sun_moon_state_from_jd(jd)
    phase_name = moon_phase_name_from_nasa(jd)

    return {
        "input": {
            "JD": jd,
            "year": year,
            "lon": lon,
        },
        "time": {
            "JD": jd,
            "AM": am,
            "local_hours": local_hours,
            "local_datetime": local_dt_str,
        },
        "moon": {
            "phase_name": phase_name,
            "phase_angle_deg": nasa_state["phase_angle_deg"],
            "illumination": nasa_state["illumination"],
        },
        "geometry": {
            "elongation_deg": nasa_state["elongation_deg"],
            "sun_ecliptic_lon_deg": nasa_state["sun"]["ecliptic_lon_deg"],
            "moon_ecliptic_lon_deg": nasa_state["moon"]["ecliptic_lon_deg"],
        },
    }


def eclipse_visibility(
    jd: float,
    eclipse_type: str,
    lat_deg: float,
    lon_deg: float,
    elevation_m: float = 0.0,
) -> Dict[str, Any]:
    """Wrapper pod API: widoczność zaćmienia Słońca/Księżyca dla lokalizacji."""

    eclipse_type = eclipse_type.lower()
    if eclipse_type == "solar":
        return solar_eclipse_visibility(jd, lat_deg, lon_deg, elevation_m=elevation_m)
    elif eclipse_type == "lunar":
        return lunar_eclipse_visibility(jd, lat_deg, lon_deg, elevation_m=elevation_m)
    else:
        raise ValueError(f"Nieznany typ zaćmienia: {eclipse_type}")
