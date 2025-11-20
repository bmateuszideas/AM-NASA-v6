import csv
from typing import Iterable, Tuple

from .am_core import am_from_jd, jd_from_am
from .faza_ksiezyca import moon_phase, moon_phase_value


def generate_report(
    dataset: Iterable[Tuple[str, float, int]],
    filename: str = "epoch_report.csv",
) -> str:
    """
    Tworzy raport CSV z porównaniem JD_NASA vs JD_AM dla podanych kotwic.

    dataset: iterowalne (name, jd_nasa, year)
    """
    with open(filename, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "Nazwa",
                "JD_NASA",
                "JD_AM",
                "Różnica [dni]",
                "Faza Księżyca",
                "Faza [0-1]",
            ]
        )
        for name, jd_nasa, year in dataset:
            am = am_from_jd(jd_nasa, year)
            jd_am = jd_from_am(am, year)
            diff = jd_am - jd_nasa
            phase_name = moon_phase(jd_nasa)
            phase_val = moon_phase_value(jd_nasa)
            w.writerow([name, jd_nasa, jd_am, diff, phase_name, f"{phase_val:.4f}"])
    return filename


def generate_html_report(
    dataset: Iterable[Tuple[str, float, int]],
    filename: str = "epoch_report.html",
) -> str:
    """
    Generuje prosty raport HTML na podstawie tego samego datasetu.
    """
    rows = []
    for name, jd_nasa, year in dataset:
        am = am_from_jd(jd_nasa, year)
        jd_am = jd_from_am(am, year)
        diff = jd_am - jd_nasa
        phase_name = moon_phase(jd_nasa)
        phase_val = moon_phase_value(jd_nasa)
        rows.append(
            (
                name,
                jd_nasa,
                jd_am,
                diff,
                phase_name,
                phase_val,
            )
        )

    html = [
        "<html><head><meta charset='utf-8'><title>Epoch Report</title></head><body>",
        "<h1>Epoch Report AM ↔ JD</h1>",
        "<table border='1' cellspacing='0' cellpadding='4'>",
        "<tr><th>Nazwa</th><th>JD_NASA</th><th>JD_AM</th><th>Różnica [dni]</th><th>Faza</th><th>Faza [0-1]</th></tr>",
    ]
    for name, jd_nasa, jd_am, diff, phase_name, phase_val in rows:
        html.append(
            f"<tr>"
            f"<td>{name}</td>"
            f"<td>{jd_nasa:.5f}</td>"
            f"<td>{jd_am:.5f}</td>"
            f"<td>{diff:+.6f}</td>"
            f"<td>{phase_name}</td>"
            f"<td>{phase_val:.4f}</td>"
            f"</tr>"
        )
    html.append("</table></body></html>")

    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(html))

    return filename
