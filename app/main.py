from __future__ import annotations

from pathlib import Path
import csv
from datetime import date
from typing import Optional, List, Dict, Any
import sys
import re

# --- USTAWIENIE PYTHONPATH NA src/ TAK, ŻEBY am_nasa ZAWSZE SIĘ ZNALAZŁO ---

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# --- RESZTA IMPORTÓW ---

from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import HTMLResponse

from am_nasa.api import convert_calendar_date, info_from_jd

# Ścieżka do AMJD_EVENT_INDEX.csv
DATA_DIR = ROOT / "data" / "amjd"
EVENT_INDEX_PATH = DATA_DIR / "AMJD_EVENT_INDEX.csv"

app = FastAPI(
    title="AM-NASA v6",
    description="Silnik AM ↔ JD ↔ NASA + interfejs użytkownika",
    version="0.5.0",
)

# ====== MAPY MIESIĘCY – TEKST → NUMER ======

MONTHS: Dict[str, Dict[str, int]] = {
    # Gregoriański – klasyczne miesiące po angielsku / skróty
    "gregorian": {
        "january": 1,
        "february": 2,
        "march": 3,
        "april": 4,
        "may": 5,
        "june": 6,
        "july": 7,
        "august": 8,
        "september": 9,
        "october": 10,
        "november": 11,
        "december": 12,
        "jan": 1,
        "feb": 2,
        "mar": 3,
        "apr": 4,
        "jun": 6,
        "jul": 7,
        "aug": 8,
        "sep": 9,
        "sept": 9,
        "oct": 10,
        "nov": 11,
        "dec": 12,
    },

    # placeholder – nadpiszemy niżej gregoriańskimi
    "julian": {},
    "auc": {},

    # Hebrajski – Twój case „14 Nisan 3790”
    "hebrew": {
        "nisan": 1,
        "nissan": 1,
        "iyyar": 2,
        "iyar": 2,
        "sivan": 3,
        "tammuz": 4,
        "av": 5,
        "elul": 6,
        "tishri": 7,
        "tishrei": 7,
        "cheshvan": 8,
        "marcheshvan": 8,
        "kislev": 9,
        "tevet": 10,
        "shevat": 11,
        "adar": 12,
        "adar1": 12,
        "adar2": 13,
    },

    # Islamski (Hijri)
    "islamic": {
        "muharram": 1,
        "safar": 2,
        "rabi al-awwal": 3,
        "rabi al awwal": 3,
        "rabi i": 3,
        "rabi al-thani": 4,
        "rabi al thani": 4,
        "rabi ii": 4,
        "jumada al-awwal": 5,
        "jumada al awwal": 5,
        "jumada i": 5,
        "jumada al-thani": 6,
        "jumada al thani": 6,
        "jumada ii": 6,
        "rajab": 7,
        "shaban": 8,
        "sha'ban": 8,
        "ramadan": 9,
        "shawwal": 10,
        "dhu al-qadah": 11,
        "dhu al hijjah": 12,
        "dhu al-hijjah": 12,
    },

    # Perski (Solar Hijri)
    "persian": {
        "farvardin": 1,
        "ordibehesht": 2,
        "khordad": 3,
        "tir": 4,
        "mordad": 5,
        "shahrivar": 6,
        "mehr": 7,
        "aban": 8,
        "azar": 9,
        "dey": 10,
        "bahman": 11,
        "esfand": 12,
    },

    # Francuski rewolucyjny
    "french_rev": {
        "vendemiaire": 1,
        "brumaire": 2,
        "frimaire": 3,
        "nivose": 4,
        "pluviose": 5,
        "ventose": 6,
        "germinal": 7,
        "floreal": 8,
        "prairial": 9,
        "messidor": 10,
        "thermidor": 11,
        "fructidor": 12,
    },

    # Koptyjski
    "coptic": {
        "thout": 1,
        "paopi": 2,
        "hathor": 3,
        "koiak": 4,
        "tobi": 5,
        "meshir": 6,
        "pamenot": 7,
        "parmouti": 8,
        "pashons": 9,
        "paoni": 10,
        "epip": 11,
        "mesori": 12,
        "nasie": 13,
    },

    # Etiopski
    "ethiopian": {
        "meskerem": 1,
        "tikimt": 2,
        "hidar": 3,
        "tahsas": 4,
        "tir": 5,
        "yekatit": 6,
        "megabit": 7,
        "miyazya": 8,
        "genbot": 9,
        "sene": 10,
        "hamle": 11,
        "nehase": 12,
        "pagume": 13,
    },
}

# Julian / AUC używają tych samych nazw miesięcy co gregoriański.
for _sys in ("julian", "auc"):
    MONTHS[_sys] = MONTHS["gregorian"]


def _normalize_iso_like(text: str) -> Optional[str]:
    """
    2025-1-9 / 2025-01-09 -> 2025-01-09.
    Jak nie wygląda jak data, zwraca None.
    """
    text = text.strip()
    m = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", text)
    if not m:
        return None
    y, mo, d = m.groups()
    return f"{y}-{int(mo):02d}-{int(d):02d}"


def parse_text_date(system: str, text: str) -> str:
    """
    Parser daty tekstowej -> 'YYYY-MM-DD' dla kalendarzy, które mają nazwy miesięcy.

    Obsługuje:
      - 2025-10-09
      - 14 nisan 3790
      - nisan 14 3790
      - 5 rajab 1447
      itd.
    """
    text = text.strip().lower()

    # 1) ISO / prawie ISO
    iso = _normalize_iso_like(text)
    if iso:
        return iso

    # 2) tokeny
    parts = re.split(r"[\s/,-]+", text)
    parts = [p for p in parts if p]
    if len(parts) < 3:
        # niech backend zgłosi błąd
        return text

    months_map = MONTHS.get(system, {})
    if not months_map:
        # system bez obsługi nazw – traktujemy jak surowe
        return text

    # case A: "14 nisan 3790"
    if parts[0].isdigit() and parts[-1].isdigit():
        day = int(parts[0])
        year = parts[-1]
        month_name = " ".join(parts[1:-1])
        if month_name in months_map:
            m = months_map[month_name]
            return f"{year}-{m:02d}-{day:02d}"

    # case B: "nisan 14 3790"
    if parts[-1].isdigit() and parts[-2].isdigit():
        year = parts[-1]
        day = int(parts[-2])
        month_name = " ".join(parts[:-2])
        if month_name in months_map:
            m = months_map[month_name]
            return f"{year}-{m:02d}-{day:02d}"

    # jak nie ogarnął – zwraca tekst, a /convert rzuci 400
    return text


def load_event_index() -> List[Dict[str, Any]]:
    if not EVENT_INDEX_PATH.exists():
        raise RuntimeError(f"Brak pliku AMJD_EVENT_INDEX.csv: {EVENT_INDEX_PATH}")
    with EVENT_INDEX_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


# ====== UI HTML + JS ======

@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    rows = load_event_index()

    # lista key do selecta (pierwsze 100)
    key_options = "\n".join(
        f'<option value="{r.get("key","")}">{r.get("key","")}</option>'
        for r in rows[:100]
        if r.get("key")
    )

    # unikalne kind / status_am do dropdownów
    kinds = sorted(
        {(r.get("kind") or "").strip() for r in rows if (r.get("kind") or "").strip()}
    )
    statuses = sorted(
        {
            (r.get("status_am") or r.get("status_AM") or "").strip()
            for r in rows
            if (r.get("status_am") or r.get("status_AM") or "").strip()
        }
    )

    kind_options = "\n".join(f'<option value="{k}">{k}</option>' for k in kinds)
    status_options = "\n".join(f'<option value="{s}">{s}</option>' for s in statuses)

    html = f"""<!DOCTYPE html>
<html lang="pl">
<head>
  <meta charset="utf-8" />
  <title>AM-NASA v6 – panel</title>
  <style>
    body {{
      font-family: system-ui, sans-serif;
      margin: 2rem;
      max-width: 980px;
    }}
    h1 {{ margin-bottom: 0.2rem; }}
    h2 {{ margin-top: 1.2rem; }}
    label {{ display: block; margin-top: 0.5rem; }}
    input, select {{ padding: 0.25rem 0.4rem; margin-top: 0.1rem; }}
    button {{ margin-top: 0.8rem; padding: 0.4rem 0.8rem; cursor: pointer; }}
    pre {{
      background: #111;
      color: #eee;
      padding: 0.8rem;
      border-radius: 6px;
      white-space: pre-wrap;
      font-size: 0.85rem;
    }}
    .row {{ display: flex; gap: 1.5rem; flex-wrap: wrap; }}
    .card {{
      border: 1px solid #ccc;
      border-radius: 8px;
      padding: 1rem;
      margin-top: 1rem;
      flex: 1 1 260px;
    }}
    small {{ display: block; color: #666; margin-top: 0.25rem; }}
  </style>
</head>
<body>
  <h1>AM-NASA v6</h1>
  <p>Silnik AM/JD + efemerydy. Pełny panel: konwersja + indeks AMJD.</p>

  <div class="row">
    <div class="card">
      <h2>Konwersja daty / czasu</h2>
      <form id="convert-form">
        <label>
          System:
          <select name="system">
            <option value="gregorian">gregorian</option>
            <option value="julian">julian</option>
            <option value="jd">julian_day (JD)</option>
            <option value="am">am (Anno Mundi)</option>
            <option value="hebrew">hebrew</option>
            <option value="islamic">islamic</option>
            <option value="persian">persian</option>
            <option value="french_rev">french_rev</option>
            <option value="coptic">coptic</option>
            <option value="ethiopian">ethiopian</option>
            <option value="chinese">chinese</option>
            <option value="hindu">hindu</option>
            <option value="maya">maya</option>
          </select>
          <small>Przykłady: "2025-10-09", "14 nisan 3790", "5 rajab 1447".</small>
        </label>
        <label>
          Data:
          <input type="text" name="date" value="2025-10-09" />
          <small>Możesz wpisać ISO albo nazwę miesiąca (tam, gdzie obsługujemy nazwy).</small>
        </label>
        <label>
          Długość geograficzna (+E):
          <input type="number" step="0.0001" name="lon" value="19.9" />
        </label>
        <button type="submit">Przelicz</button>
      </form>
      <pre id="convert-result">{{
  "hint": "Wynik konwersji pojawi się tutaj"
}}</pre>
    </div>

    <div class="card">
      <h2>Event z indeksu AMJD</h2>
      <form id="event-form">
        <label>
          Key (ręcznie):
          <input type="text" name="key" placeholder="np. HALLEY_1066_peri" />
        </label>
        <label>
          Albo wybierz z listy:
          <select id="key-select">
            <option value="">-- wybierz key --</option>
            {key_options}
          </select>
        </label>
        <button type="submit">Pobierz</button>
      </form>
      <pre id="event-result">{{
  "hint": "Szczegóły eventu pojawią się tutaj"
}}</pre>
    </div>
  </div>

  <div class="card">
    <h2>Szybka lista eventów</h2>
    <form id="events-form">
      <label>
        Kind:
        <select name="kind">
          <option value="">-- dowolny --</option>
          {kind_options}
        </select>
      </label>
      <label>
        Status_AM:
        <select name="status_am">
          <option value="">-- dowolny --</option>
          {status_options}
        </select>
      </label>
      <label>
        Limit:
        <input type="number" name="limit" value="20" min="1" max="500" />
      </label>
      <button type="submit">Pobierz listę</button>
    </form>
    <pre id="events-result">{{
  "hint": "Lista eventów pojawi się tutaj"
}}</pre>
  </div>

  <script>
    async function fetchJson(url) {{
      const res = await fetch(url);
      if (!res.ok) throw new Error("HTTP " + res.status);
      return await res.json();
    }}

    // --- KONWERSJA DATY / CZASU ---
    const convForm = document.getElementById("convert-form");
    const convResult = document.getElementById("convert-result");
    convForm.addEventListener("submit", async (e) => {{
      e.preventDefault();
      const data = new FormData(convForm);
      const system = data.get("system");
      const dateStr = data.get("date");
      const lon = data.get("lon") || "0";
      let url = "";
      if (system === "jd") {{
        url = `/from-jd?jd=${{encodeURIComponent(dateStr)}}&lon=${{encodeURIComponent(lon)}}`;
      }} else {{
        url = `/convert?system=${{encodeURIComponent(system)}}&date=${{encodeURIComponent(dateStr)}}&lon=${{encodeURIComponent(lon)}}`;
      }}
      convResult.textContent = "[...]";
      try {{
        const json = await fetchJson(url);
        convResult.textContent = JSON.stringify(json, null, 2);
      }} catch (err) {{
        convResult.textContent = "Błąd: " + err;
      }}
    }});

    // --- EVENT Z INDEKSU AMJD ---
    const eventForm = document.getElementById("event-form");
    const eventResult = document.getElementById("event-result");
    const keySelect = document.getElementById("key-select");

    keySelect.addEventListener("change", () => {{
      const input = eventForm.querySelector('input[name="key"]');
      if (keySelect.value) {{
        input.value = keySelect.value;
      }}
    }});

    eventForm.addEventListener("submit", async (e) => {{
      e.preventDefault();
      const data = new FormData(eventForm);
      const key = data.get("key");
      if (!key) {{
        eventResult.textContent = "Podaj key zdarzenia albo wybierz z listy.";
        return;
      }}
      const url = `/events/${{encodeURIComponent(key)}}`;
      eventResult.textContent = "[...]";
      try {{
        const json = await fetchJson(url);
        eventResult.textContent = JSON.stringify(json, null, 2);
      }} catch (err) {{
        eventResult.textContent = "Błąd: " + err;
      }}
    }});

    // --- SZYBKA LISTA EVENTÓW ---
    const eventsForm = document.getElementById("events-form");
    const eventsResult = document.getElementById("events-result");

    eventsForm.addEventListener("submit", async (e) => {{
      e.preventDefault();
      const data = new FormData(eventsForm);
      const kind = data.get("kind");
      const status = data.get("status_am");
      const limit = data.get("limit") || "20";
      const params = new URLSearchParams();
      if (kind) params.set("kind", kind);
      if (status) params.set("status_am", status);
      params.set("limit", limit);
      const url = `/events?${{params.toString()}}`;
      eventsResult.textContent = "[...]";
      try {{
        const json = await fetchJson(url);
        eventsResult.textContent = JSON.stringify(json, null, 2);
      }} catch (err) {{
        eventsResult.textContent = "Błąd: " + err;
      }}
    }});
  </script>
</body>
</html>
"""
    return HTMLResponse(content=html)


# ====== API-ENDPOINTY ======

@app.get("/convert")
async def convert(
    system: str = Query("gregorian"),
    date_str: str = Query(..., alias="date"),
    lon: float = Query(0.0),
) -> Dict[str, Any]:
    """
    /convert – przyjmuje system kalendarza + datę tekstową (z nazwą miesiąca)
    i zwraca wynik convert_calendar_date().
    """
    parsed = parse_text_date(system, date_str)

    # wyciągamy year, month, day bez używania date.fromisoformat (bo kalendarze mają swoje zasady)
    try:
        parts = parsed.split("-")
        if len(parts) != 3:
            raise ValueError(f"Nie mogę rozbić '{parsed}' na Y-M-D")
        y = int(parts[0])
        m = int(parts[1])
        d = float(parts[2])  # float, bo dzień może być z .5 itd.
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=400,
            detail=f"Nie mogę zinterpretować daty '{date_str}' (po parsowaniu: '{parsed}')",
        ) from exc

    try:
        result = convert_calendar_date(system=system, year=y, month=m, day=d, lon=lon)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=400,
            detail=(
                f"Błąd w convert_calendar_date(system={system!r}, "
                f"year={y}, month={m}, day={d}): {exc}"
            ),
        ) from exc

    return result


@app.get("/from-jd")
async def from_jd(
    jd: float = Query(...),
    lon: float = Query(0.0),
) -> Dict[str, Any]:
    """
    /from-jd – bierze czysty JD i zwraca info_from_jd().
    """
    return info_from_jd(jd=jd, lon=lon)


@app.get("/events")
async def list_events(
    kind: Optional[str] = Query(None),
    status_am: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
) -> Dict[str, Any]:
    """
    /events – lista eventów z indeksu AMJD z filtrami kind / status_am.
    """
    rows = load_event_index()
    out: List[Dict[str, Any]] = []

    for r in rows:
        if kind:
            if (r.get("kind") or "").lower() != kind.lower():
                continue
        if status_am:
            raw = r.get("status_am") or r.get("status_AM") or ""
            if raw.upper() != status_am.upper():
                continue
        out.append(r)
        if len(out) >= limit:
            break

    return {"count": len(out), "items": out}


@app.get("/events/{key}")
async def event_detail(key: str) -> Dict[str, Any]:
    """
    /events/{key} – szczegóły pojedynczego eventu z indeksu AMJD.
    """
    rows = load_event_index()
    for r in rows:
        if (r.get("key") or "") == key:
            return r
    raise HTTPException(status_code=404, detail=f"Nie znaleziono eventu o key={key!r}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
