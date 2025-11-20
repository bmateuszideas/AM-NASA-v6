# scripts/amjd_eclipse_visibility_grid.py

import argparse
import os
from typing import List

import pandas as pd
import requests


DEFAULT_MASTER_PATH = os.path.join(
    "data", "amjd", "AMJD_VALIDACJA_MASTER_AM_validated.csv"
)
DEFAULT_TOPO_PATH = os.path.join(
    "data", "amjd", "AMJD_TOPO_30_CITIES.csv"
)
DEFAULT_API_URL = "http://127.0.0.1:8000/api/eclipse/visibility"


def load_master(path: str, eclipse_type: str) -> pd.DataFrame:
    """
    Ładuje zwalidowany MASTER i filtruje rekordy zaćmień.

    eclipse_type: 'lunar' albo 'solar'
      - lunar -> key zaczyna się od 'LE_'
      - solar -> key zaczyna się od 'SE_'
    """
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Nie znaleziono MASTER: {path}. "
            f"Najpierw uruchom: python -m scripts.amjd_validate_master"
        )

    df = pd.read_csv(path)

    if "key" not in df.columns:
        raise ValueError(
            f"W pliku {path} nie ma kolumny 'key'. "
            f"Sprawdź strukturę CSV (powinno być: key, ..., JD_UT, ...)."
        )

    if "JD_UT" not in df.columns:
        raise ValueError(
            f"W pliku {path} nie ma kolumny 'JD_UT'. "
            f"To jest JD UT z GSFC – bez tego nie policzymy widoczności."
        )

    if eclipse_type == "lunar":
        mask = df["key"].str.startswith("LE_") | df["key"].str.contains("LunarEcl", na=False)
    elif eclipse_type == "solar":
        mask = df["key"].str.startswith("SE_") | df["key"].str.contains("SolarEcl", na=False)
    else:
        raise ValueError(f"Nieznany eclipse_type: {eclipse_type!r}")

    eclipses = df.loc[mask].copy()

    if eclipses.empty:
        raise ValueError(
            f"Brak rekordów zaćmień typu {eclipse_type} w {path}. "
            f"Sprawdź, czy klucze mają prefix LE_/SE_."
        )

    # Bierzemy tylko potrzebne kolumny
    cols = ["key", "label", "JD_UT"]
    for c in cols:
        if c not in eclipses.columns:
            # label opcjonalny – jak nie ma, to przeżyjemy
            if c == "label":
                eclipses["label"] = eclipses["key"]
            else:
                raise ValueError(
                    f"W MASTER brakuje oczekiwanej kolumny: {c!r}"
                )

    eclipses = eclipses[cols]
    return eclipses.reset_index(drop=True)


def load_topo_sites(path: str) -> pd.DataFrame:
    """
    Ładuje siatkę lokalizacji topocentrycznych.

    Zakładana struktura CSV (minimum):
      - site_name
      - lat_deg
      - lon_deg

    Opcjonalnie:
      - elev_m (domyślnie 0 jeśli brak)
    """
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Nie znaleziono pliku z lokalizacjami: {path}. "
            f"Spodziewany jest np. AMJD_TOPO_30_CITIES.csv."
        )

    df = pd.read_csv(path)

    required = ["site_name", "lat_deg", "lon_deg"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(
            f"W pliku {path} brakuje kolumn: {missing}. "
            f"Minimalny zestaw to: {required}."
        )

    if "elev_m" not in df.columns:
        df["elev_m"] = 0.0

    # Tnij do potrzebnych kolumn żeby było czysto
    df = df[["site_name", "lat_deg", "lon_deg", "elev_m"]].copy()
    return df.reset_index(drop=True)


def query_eclipse_visibility(
    api_url: str,
    jd: float,
    eclipse_type: str,
    lat_deg: float,
    lon_deg: float,
    elev_m: float,
) -> dict:
    """
    Odpala zapytanie do lokalnego API AM-NASA:
      POST /api/eclipse/visibility
      body: { jd, eclipse_type, lat_deg, lon_deg, elevation_m }

    Zwraca dict z sekcji 'result' (jeśli jest), inaczej cały JSON.
    """
    payload = {
        "jd": float(jd),
        "eclipse_type": eclipse_type,
        "lat_deg": float(lat_deg),
        "lon_deg": float(lon_deg),
        "elevation_m": float(elev_m),
    }

    resp = requests.post(api_url, json=payload, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    # Spodziewana struktura:
    # { "input": {...}, "result": {...} }
    if isinstance(data, dict) and "result" in data:
        return data["result"]
    return data


def build_visibility_grid(
    eclipses: pd.DataFrame,
    sites: pd.DataFrame,
    eclipse_type: str,
    api_url: str,
) -> pd.DataFrame:
    """
    Dla każdej kotwicy zaćmienia i każdego punktu topo
    liczy widoczność (przez API) i buduje jedną dużą tabelę.
    """
    rows: List[dict] = []

    for _, e_row in eclipses.iterrows():
        key = e_row["key"]
        label = e_row["label"]
        jd = float(e_row["JD_UT"])

        for _, s_row in sites.iterrows():
            site_name = s_row["site_name"]
            lat = float(s_row["lat_deg"])
            lon = float(s_row["lon_deg"])
            elev = float(s_row["elev_m"])

            try:
                res = query_eclipse_visibility(
                    api_url=api_url,
                    jd=jd,
                    eclipse_type=eclipse_type,
                    lat_deg=lat,
                    lon_deg=lon,
                    elev_m=elev,
                )
            except Exception as ex:
                # Nie zabijaj całego grida jednym błędem – zapisz status.
                rows.append(
                    {
                        "key": key,
                        "label": label,
                        "eclipse_type": eclipse_type,
                        "JD_UT": jd,
                        "site_name": site_name,
                        "lat_deg": lat,
                        "lon_deg": lon,
                        "elev_m": elev,
                        "visible": None,
                        "classification": None,
                        "sun_alt_deg": None,
                        "sun_az_deg": None,
                        "moon_alt_deg": None,
                        "moon_az_deg": None,
                        "illumination": None,
                        "phase_angle_deg": None,
                        "elongation_deg": None,
                        "error": str(ex),
                    }
                )
                continue

            # Staramy się być kompatybilni z JSONem, który już widziałeś
            row = {
                "key": key,
                "label": label,
                "eclipse_type": eclipse_type,
                "JD_UT": jd,
                "site_name": site_name,
                "lat_deg": lat,
                "lon_deg": lon,
                "elev_m": elev,
                "visible": res.get("visible"),
                "classification": res.get("classification"),
                "sun_alt_deg": res.get("sun_alt_deg"),
                "sun_az_deg": res.get("sun_az_deg"),
                "moon_alt_deg": res.get("moon_alt_deg"),
                "moon_az_deg": res.get("moon_az_deg"),
                "illumination": res.get("illumination"),
                "phase_angle_deg": res.get("phase_angle_deg"),
                "elongation_deg": res.get("elongation_deg"),
                "error": None,
            }
            rows.append(row)

    return pd.DataFrame(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="AM-JD — siatka widoczności zaćmień dla zestawu miast."
    )
    parser.add_argument(
        "--master",
        default=DEFAULT_MASTER_PATH,
        help=f"Ścieżka do AMJD_VALIDACJA_MASTER_AM_validated.csv "
             f"(domyślnie: {DEFAULT_MASTER_PATH})",
    )
    parser.add_argument(
        "--topo",
        default=DEFAULT_TOPO_PATH,
        help=f"Ścieżka do AMJD_TOPO_30_CITIES.csv (domyślnie: {DEFAULT_TOPO_PATH})",
    )
    parser.add_argument(
        "--eclipse-type",
        choices=["lunar", "solar"],
        required=True,
        help="Typ zaćmienia: 'lunar' albo 'solar'.",
    )
    parser.add_argument(
        "--api-url",
        default=DEFAULT_API_URL,
        help=f"URL lokalnego API do widoczności zaćmień "
             f"(domyślnie: {DEFAULT_API_URL})",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Ścieżka wyjścia CSV. "
             "Jeśli pusta → data/amjd/AMJD_TOPO_VISIBILITY_<type>.csv",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    master_path = args.master
    topo_path = args.topo
    eclipse_type = args.eclipse_type
    api_url = args.api_url

    if args.out is None:
        out_name = f"AMJD_TOPO_VISIBILITY_{eclipse_type.upper()}.csv"
        out_path = os.path.join("data", "amjd", out_name)
    else:
        out_path = args.out

    print(f"[INFO] Ładuję MASTER z: {master_path}")
    eclipses = load_master(master_path, eclipse_type=eclipse_type)
    print(f"[INFO] Załadowano {len(eclipses)} kotwic typu {eclipse_type}.")

    print(f"[INFO] Ładuję lokalizacje topo z: {topo_path}")
    sites = load_topo_sites(topo_path)
    print(f"[INFO] Załadowano {len(sites)} lokalizacji topocentrycznych.")

    print(f"[INFO] Liczę siatkę widoczności przez API: {api_url}")
    grid = build_visibility_grid(
        eclipses=eclipses,
        sites=sites,
        eclipse_type=eclipse_type,
        api_url=api_url,
    )

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    grid.to_csv(out_path, index=False, encoding="utf-8")

    print(f"[DONE] Zapisano siatkę widoczności do: {out_path}")
    print(f"[DONE] Wierszy: {len(grid)} "
          f"(eclipse × sites = {len(eclipses)} × {len(sites)})")


if __name__ == "__main__":
    main()
