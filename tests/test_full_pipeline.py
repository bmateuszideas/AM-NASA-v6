import math
import os

from am_nasa.astro_sync import sync_jd_to_am_physical
from am_nasa.astro_validate import validate_am_jd
from am_nasa.epoch_report import generate_report, generate_html_report
from am_nasa.konwersja_wielosystemowa import konwertuj


def test_gregorian():
    data = {"system": "gregorian", "year": 2025, "month": 10, "day": 9}
    result = konwertuj(data)
    assert "JD" in result and "AM" in result
    assert math.isfinite(result["JD"])
    assert math.isfinite(result["AM"])


def test_all_systems_basic():
    systems = [
        "gregorian",
        "julian",
        "islamic",
        "persian",
        "chinese",
        "hindu",
        "coptic",
        "ethiopian",
        "french_rev",
        "maya",
        "am",
    ]

    for system in systems:
        if system == "am":
            data = {"system": system, "year": 2025, "month": 1, "day": 739288.5}
        else:
            data = {"system": system, "year": 2025, "month": 10, "day": 9}
        result = konwertuj(data)
        assert "JD" in result and "AM" in result
        assert math.isfinite(result["JD"])
        assert math.isfinite(result["AM"])


def test_full_pipeline_validation_and_reports(tmp_path):
    # Przykładowe kotwice (nazwa, JD_NASA, rok)
    dataset = [
        ("Apollo 11 landing", 2440423.5, 1969),
        ("Nowoczesna data testowa", 2460958.5, 2025),
    ]

    # AM z fizycznej synchronizacji
    am_values = [sync_jd_to_am_physical(jd, year) for (_, jd, year) in dataset]
    nasa_jd_values = [jd for (_, jd, _) in dataset]

    result = validate_am_jd(am_values, nasa_jd_values)

    csv_path = tmp_path / "epoch_report_test.csv"
    html_path = tmp_path / "epoch_report_test.html"
    generate_report(dataset, filename=str(csv_path))
    generate_html_report(dataset, filename=str(html_path))

    assert result["max"] < 0.6  # max różnica < 0.6 dnia
    assert csv_path.exists()
    assert html_path.exists()
