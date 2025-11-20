from __future__ import annotations

from pathlib import Path
import csv
from datetime import date
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import HTMLResponse

from am_nasa.api import convert_calendar_date, info_from_jd

# Ścieżka do AMJD_EVENT_INDEX.csv
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "amjd"
EVENT_INDEX_PATH = DATA_DIR / "AMJD_EVENT_INDEX.csv"

app = FastAPI(
    title="AM-NASA v6 – user API",
    description="Prostsza, codzienna wersja API nad silnikiem AM-NASA",
    version="0.1.0",
)


def load_event_index() -> List[Dict[str, Any]]:
    if not EVENT_INDEX_PATH.exists():
        raise RuntimeError(f"Brak pliku AMJD_EVENT_INDEX.csv: {EVENT_INDEX_PATH}")
    with EVENT_INDEX_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    """
    Proste UI HTML – formularz do konwersji daty i linki do endpointów.
    """
    return """
<!DOCTYPE html>
<html lang="pl">
<head>
  <meta charset="utf-8" />
  <title>AM-NASA v6 – user API</title>
  <style>
    body { font-family: system-ui, sans-serif; margin: 2rem; max-width: 900px; }
    h1 { margin-bottom: 0.5rem; }
    label { display: block; margin-top: 0.5rem; }
    input, select { padding: 0.25rem 0.4rem; margin-top: 0.1rem; }
    button { margin-top: 0.8rem; padding: 0.4rem 0.8rem; cursor: pointer; }
    pre { background: #111; color: #eee; padding: 0.8rem; border-radius: 6px; white-space: pre-wrap; }
    .row { display: flex; gap: 1.5rem; flex-wrap: wrap; }
    .card { border: 1px solid #ccc; border-radius: 8px; padding: 1rem; margin-top: 1rem; }
    a { color: #1565c0; }
  </style>
</head>
<body>
  <h1>AM-NASA v6 – prosty interfejs</h1>
  <p>To jest ludzka nakładka na silnik AM/JD + efemerydy. Na szybko:</p>
  <ul>
    <li><code>GET /convert</code> – konwersja daty cywilnej do JD/AM</li>
    <li><code>GET /from-jd</code> – info o danym JD</li>
    <li><code>GET /events</code> – lista zdarzeń z AMJD_EVENT_INDEX</li>
    <li><code>GET /events/{key}</code> – szczegóły konkretnego zdarzenia</li>
  </ul>

  <div class="row">
    <div class="card" style="flex: 1 1 260px;">
      <h2>Konwersja daty → JD/AM</h2>
      <form id="convert-form">
        <label>
          System kalendarza:
          <select name="system">
            <option value="gregorian">gregorian</option>
            <option value="julian">julian</option>
            <option value="hebrew">hebrew</option>
          </select>
        </label>
        <label>
          Data (YYYY-MM-DD):
          <input type="date" name="date" value="2025-10-09" />
        </label>
        <label>
          Długość geograficzna (stopnie, +E):
          <input type="number" step="0.0001" name="lon" value="19.9" />
        </label>
        <button type="submit">Przelicz</button>
      </form>
      <pre id="convert-result">{ wynik pojawi się tutaj }</pre>
    </div>

    <div class="card" style="flex: 1 1 260px;">
      <h2>Event z indeksu AMJD</h2>
      <form id="event-form">
        <label>
          Klucz zdarzenia (key):
          <input type="text" name="key" placeholder="np. HALLEY_1066_peri" />
        </label>
        <button type="submit">Pobierz</button>
      </form>
      <pre id="event-result">{ wynik pojawi się tutaj }</pre>
    </div>
  </div>

  <script>
    const convForm = document.getElementById("convert-form");
    const convResult = document.getElementById("convert-result");
    convForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const data = new FormData(convForm);
      const system = data.get("system");
      const dateStr = data.get("date");
      const lon = data.get("lon");
      if (!dateStr) {
        convResult.textContent = "Podaj datę.";
        return;
      }
      const url = `/convert?system=${encodeURIComponent(system)}&date=${encodeURIComponent(dateStr)}&lon=${encodeURIComponent(lon)}`;
      convResult.textContent = "[...]";
      try {
        const res = await fetch(url);
        const json = await res.json();
        convResult.textContent = JSON.stringify(json, null, 2);
      } catch (err) {
        convResult.textContent = "Błąd: " + err;
      }
    });

    const eventForm = document.getElementById("event-form");
    const eventResult = document.getElementById("event-result");
    eventForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const data = new FormData(eventForm);
      const key = data.get("key");
      if (!key) {
        eventResult.textContent = "Podaj key zdarzenia.";
        return;
      }
      const url = `/events/${encodeURIComponent(key)}`;
      eventResult.textContent = "[...]";
      try {
        const res = await fetch(url);
        const json = await res.json();
        eventResult.textContent = JSON.stringify(json, null, 2);
      } catch (err) {
        eventResult.textContent = "Błąd: " + err;
      }
    });
  </script>
</body>
</html>
    """


@app.get("/convert")
async def convert(
    system: str = Query("gregorian", description="System: gregorian/julian/hebrew/..."),
    date_str: str = Query(..., alias="date", description="Data w formacie YYYY-MM-DD"),
    lon: float = Query(0.0, description="Długość geograficzna w stopniach (+E)"),
) -> Dict[str, Any]:
    """
    Prosty endpoint:
    GET /convert?system=gregorian&date=2025-10-09&lon=19.9

    Zwraca to samo co convert_calendar_date, tylko w GET.
    """
    try:
        y, m, d = map(int, date_str.split("-"))
        _ = date.fromisoformat(date_str)  # walidacja
    except Exception:
        raise HTTPException(status_code=400, detail=f"Nieprawidłowa data: {date_str!r}")

    result = convert_calendar_date(system=system, year=y, month=m, day=d, lon=lon)
    return result


@app.get("/from-jd")
async def from_jd(
    jd: float = Query(..., description="Julian Day (JD)"),
    lon: float = Query(0.0, description="Długość geograficzna w stopniach (+E)"),
) -> Dict[str, Any]:
    """
    GET /from-jd?jd=2460958.5&lon=19.9

    Zwraca strukturę info_from_jd (data cywilna, AM, Księżyc, geometria).
    """
    result = info_from_jd(jd=jd, lon=lon)
    return result


@app.get("/events")
async def list_events(
    kind: Optional[str] = Query(None, description="Filtr po kind, np. 'volcano', 'solar_eclipse'"),
    status_am: Optional[str] = Query(None, description="Filtr po status_AM, np. 'OK', 'WARN'"),
    limit: int = Query(50, ge=1, le=500, description="Max liczba zwróconych eventów"),
) -> Dict[str, Any]:
    """
    Zwraca listę eventów z AMJD_EVENT_INDEX.csv, z prostym filtrowaniem.
    """
    rows = load_event_index()
    filtered: List[Dict[str, Any]] = []

    for r in rows:
        if kind is not None:
            if (r.get("kind") or "").lower() != kind.lower():
                continue
        if status_am is not None:
            # status_AM albo status_am – zabezpieczenie
            raw_status = r.get("status_am") or r.get("status_AM") or ""
            if raw_status.upper() != status_am.upper():
                continue
        filtered.append(r)
        if len(filtered) >= limit:
            break

    return {
        "count": len(filtered),
        "items": filtered,
    }


@app.get("/events/{key}")
async def event_detail(key: str) -> Dict[str, Any]:
    """
    Szczegóły konkretnego eventu po key.
    """
    rows = load_event_index()
    for r in rows:
        if (r.get("key") or "") == key:
            return r
    raise HTTPException(status_code=404, detail=f"Nie znaleziono eventu o key={key!r}")
