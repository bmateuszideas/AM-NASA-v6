# AM-NASA v6 – Astronomiczny silnik kalendarzowy AM ↔ JD ↔ NASA

Projekt łączy autorski system czasu **AM** (Anno Mundi) z oficjalnymi efemerydami i danymi NASA:

- pełna konwersja między **AM ↔ JD (Julian Day) ↔ kalendarze cywilne** (julian, gregorian, hebrajskie/lunisolarne),
- wykorzystanie efemeryd JPL (**DE430 / DE442**) do liczenia **realnych pozycji Słońca i Księżyca**, 
- obsługa **zaćmień Słońca i Księżyca**, faz Księżyca i geometrii topocentrycznej,
- warstwa danych **AMJD** z walidacją na katalogach NASA (GSFC), erupcjami wulkanów i siatką obserwacji topocentrycznych,
- komplet skryptów do walidacji, przetwarzania CSV i generowania zbiorczych raportów.

Repozytorium jest przygotowane jako **projekt portfolio** – pokazuje zarówno inżynierię (kod + testy), jak i pracę B+R (walidacja na danych NASA).

---

## 1. Struktura repozytorium

Główne katalogi:

```text
AM-NASA-v6/
├─ app/                 # FastAPI – API HTTP nad silnikiem AM i efemerydami
│  └─ main.py
├─ src/
│  └─ am_nasa/
│     ├─ am_core.py                 # silnik AM ↔ JD
│     ├─ astro_sync.py              # synchronizacja AM z fizycznym JD (NASA)
│     ├─ astro_timeframes.py        # przedziały czasowe, epoki
│     ├─ astro_validate.py          # walidacja obliczeń
│     ├─ kalendarze_lunisolarne.py  # dodatkowe kalendarze (m.in. hebrajski)
│     ├─ konwersja_wielosystemowa.py# jedna funkcja: cywilna data → JD/AM
│     ├─ planetary_positions.py     # JPL DE430/DE442 – Słońce, Księżyc, planety
│     ├─ faza_ksiezyca.py           # faza Księżyca z efemeryd
│     ├─ geo_time.py                # lokalny czas, strefy, lon/lat
│     ├─ epoch_report.py            # raportowanie epok / kotwic
│     ├─ am_logger.py               # logowanie i debug
│     └─ api.py                     # funkcje wykorzystywane przez FastAPI
├─ scripts/             # skrypty CLI do walidacji i przetwarzania danych AMJD
│  ├─ amjd_validate_master.py       # walidacja MASTER vs NASA/AM
│  ├─ amjd_raw_to_master_like.py    # standaryzacja RAW → MASTER-like
│  ├─ amjd_volcano_process.py       # przetwarzanie erupcji wulkanów
│  ├─ amjd_portfolio_summary.py     # zbiorcze statystyki wszystkich CSV
│  └─ amjd_event_index.py           # master index eventów AMJD
├─ data/
│  └─ amjd/             # wszystkie dane używane w warstwie AMJD
│     ├─ AMJD_MASTER_GSFC_BATCH6.csv
│     ├─ AMJD_VALIDACJA_GSFC_v1.csv
│     ├─ AMJD_VALIDACJA_MASTER_AM_validated.csv
│     ├─ AMJD_RAW_DATA.csv
│     ├─ AMJD_RAW_DATA_MASTERLIKE.csv
│     ├─ AMJD_VOLCANO_RAW.csv
│     ├─ AMJD_VOLCANO_PROCESSED.csv
│     ├─ AMJD_TOPO_VISIBILITY_SOLAR.csv
│     ├─ AMJD_TOPO_VISIBILITY_LUNAR.csv
│     ├─ AMJD_EVENT_INDEX.csv
│     └─ ... (inne pomocnicze CSV)
├─ tests/
│  ├─ test_am_core.py
│  ├─ test_astro_sync.py
│  └─ test_full_pipeline.py
├─ pyproject.toml       # konfiguracja projektu + pytest
└─ README.md            # ten plik
```

---

## 2. Instalacja i uruchomienie

### Wymagania

- Python **3.12**
- Windows / Linux / macOS
- W repozytorium znajdują się:
  - pliki efemeryd JPL (`de430.bsp`, `de442.bsp`) – wykorzystywane przez `planetary_positions.py`,
  - katalog `data/amjd/` z danymi wejściowymi i wynikami walidacji.

### 2.1. Utworzenie virtualenv i instalacja zależności

W katalogu głównym projektu:

```bash
# Windows (PowerShell)
cd "C:\Users\<user>\Desktop\CV PORTFOLIO\AM-NASA-v6"
python -m venv .venv
.\.venv\Scripts\activate.bat

# instalacja zależności (wg pyproject)
pip install -U pip
pip install -e .
```

*(Jeśli korzystasz z Poetry, można użyć `poetry install`, ale w repo jest też klasyczny tryb `pip install -e .`.)*

### 2.2. Uruchomienie testów jednostkowych

```bash
# w aktywnym virtualenv
pytest -v
```

Oczekiwany wynik: **9 passed** – testy dla:

- `am_core` (konwersje AM ↔ JD),
- `astro_sync` (spójność z NASA),
- pełny pipeline (kalendarze, JD, AM, walidacja).

---

## 3. FastAPI – API nad silnikiem AM/NASA

Serwer HTTP udostępniający silnik AM i część funkcji astronomicznych stoi w `app/main.py`.

Podstawowe uruchomienie:

```bash
# w katalogu głównym, z aktywnym .venv
uvicorn app.main:app --reload
```

Domyślnie serwer startuje na `http://127.0.0.1:8000/`.

Przykładowe typy endpointów (zależnie od implementacji w `app/main.py`):

- `/api/time/convert` – konwersja daty cywilnej (system: gregorian/julian/hebrew/…) → JD + AM + info o Księżycu,
- `/api/time/from_jd` – informacje o danym JD (data cywilna, AM, faza Księżyca, geometria),
- `/api/eclipse/visibility` – obliczenie widoczności zaćmienia dla danego JD i lokalizacji (lat/lon/elev).

API korzysta bezpośrednio z funkcji z `src/am_nasa/api.py`, które zawijają logikę z `am_core`, `konwersja_wielosystemowa`, `planetary_positions` itd.

### Przykład: konwersja daty cywilnej → JD + AM (API)

Request:

```http
POST /api/time/convert
Content-Type: application/json

{
  "system": "gregorian",
  "year": 2025,
  "month": 10,
  "day": 9,
  "lon": 19.9
}

---

## 4. Warstwa danych AMJD

### 4.1. Dane NASA / GSFC

#### `AMJD_MASTER_GSFC_BATCH6.csv`

- ok. 20 rekordów,
- klucz `key` / `tag` – identyfikator zdarzenia (`SE_-0762_BurSagale`, `SE_-0584_Thales`, `SN_1006_first`, itp.),
- dane z katalogów NASA (GSFC):
  - `calendar`, `date_Y/M/D`,
  - `TT_time`, `UT_time`, `DeltaT_s`,
  - `JD_TT`, `JD_UT`,
  - dodatkowe pola opisowe.

To jest "surowy" pakiet wzorcowych zdarzeń z GSFC (zaćmienia, komety, supernowe).

#### `AMJD_VALIDACJA_GSFC_v1.csv`

- kilka kluczowych kotwic (np. zaćmienia księżyca 4 BCE, 32 CE, 33 CE, Halley 66 CE, SN 1054),
- precyzyjny zestaw: `calendar`, `julian_date`, `UT_time`, `JD_UT`, `JD_TT`, `DeltaT_s`,
- wykorzystywany jako wejście do walidacji silnika AM.

---

### 4.2. Walidacja AM ↔ NASA: `AMJD_VALIDACJA_MASTER_AM_validated.csv`

Tworzony przez:

```bash
python -m scripts.amjd_validate_master
```

Skrypt:

- bierze zestaw MASTER (GSFC),
- liczy JD na podstawie dat cywilnych przez `konwersja_wielosystemowa`,
- liczy AM z użyciem `am_core` / `astro_sync`,
- porównuje:
  - **JD_UT z katalogów NASA** vs JD z wyliczeń,
  - **AM_expected** vs AM policzone przez kod.

Wyniki (na przykładowym biegu):

- `rows: 28`
- `status_JD: NA=11, WARN=17`
- `status_AM: OK=21, WARN=2, NA=5`
- `max_abs_delta_JD_days: 1.0` (różnice 1 dnia dla części historycznych dat GSFC),
- `max_abs_delta_AM_days: ~3.3e-06` (~0.3 sekundy – dokładność silnika AM względem kotwic AM).

Plik zawiera m.in.:

- `key`, `label`,
- `JD_UT`, `JD_from_calendar`, `delta_JD_days`, `status_JD`,
- `AM_expected`, `AM_from_code_adjusted`, `delta_AM_days`, `status_AM`.

---

### 4.3. Dane RAW: `AMJD_RAW_DATA.csv` → `AMJD_RAW_DATA_MASTERLIKE.csv`

Konwersja:

```bash
python -m scripts.amjd_raw_to_master_like
```

`AMJD_RAW_DATA.csv` zawiera m.in.:

- dane C14 / krzywych,
- siatkę `TOPO_30_CITIES` (lokacje geograficzne),
- różne źródła (`source_group`, `site_name`, `country`, lat/lon).

Skrypt:

- standaryzuje struktury do formatu "MASTER-like":
  - `key`, `label`, `calendar`, `Y`, `M`, `D`, `UT_time`,
  - `JD_UT_src`, `JD_UT_calc`, `delta_JD_days`, `status_JD`, `error`,
  - wszystkie oryginalne kolumny są zachowane.
- wiersze bez daty (`TOPO_30_CITIES`) dostają `error = "Brak daty (Y/M/D) – nie można policzyć JD"`.

`AMJD_RAW_DATA_MASTERLIKE.csv` jest bazą pod dalszą analizę i łączenie z innymi zbiorami.

---

### 4.4. Erupcje wulkaniczne: `AMJD_VOLCANO_RAW.csv` → `AMJD_VOLCANO_PROCESSED.csv`

Przetwarzanie:

```bash
python -m scripts.amjd_volcano_process
```

Wejście: `AMJD_VOLCANO_RAW.csv` (dane wulkaniczne, m.in. GVP, daty, przedziały JD).

Wyjście: `AMJD_VOLCANO_PROCESSED.csv`, w którym dla każdego zdarzenia:

- jeśli jest pełna data (`year/month/day`):
  - liczony jest JD przez `konwersja_wielosystemowa`,
  - różnica względem `jd_ut` / `jd_min/jd_max`,
  - `delta_status` (`OK` / `WARN` / `FAIL`).
- jeśli jest zakres (`jd_min/jd_max`) bez konkretnego roku:
  - liczony jest **środek przedziału** jako `jd_ut_final`,
  - z niego wyznaczana jest przybliżona data cywilna (`civil_date_astro`) i czas UT,
  - `date_mode = "range_midpoint"`.

Przykładowy stan (po uruchomieniu):

- `rows: 14`
- `delta_status: RANGE=8, OK=5, WARN=1`
- `date_mode: range_midpoint=8, exact=6`

Dzięki temu zdarzenia wulkaniczne są wpięte w ten sam timeline JD/AM co reszta danych.

---

### 4.5. Topocentryczna widoczność zaćmień

Pliki:

- `AMJD_TOPO_VISIBILITY_SOLAR.csv`
- `AMJD_TOPO_VISIBILITY_LUNAR.csv`

Struktura (przykładowa):

- `key`, `label`, `eclipse_type`,
- `JD_UT`, `site_name`, `lat_deg`, `lon_deg`, `elev_m`,
- `visible` (True/False),
- `classification` (np. `total`, `partial`, `penumbral`, `none`),
- `sun_alt_deg`, `moon_alt_deg`, `moon_illumination`, itd.

Te pliki są generowane na podstawie:

- efemeryd JPL (pozycje Słońca i Księżyca),
- geometrii lokalnej (`geo_time`, długość/szerokość geograficzna),
- listy lokalizacji (`TOPO_30_CITIES` / inne).

W aktualnej wersji repozytorium logika widoczności była powiązana z API HTTP (FastAPI). W dalszym kroku można całkowicie przepiąć ją na bezpośrednie wywołanie funkcji Python (bez HTTP), analogicznie jak przy innych skryptach.

---

### 4.6. Zbiorcze podsumowanie: `AMJD_PORTFOLIO_SUMMARY.csv`

Tworzone przez:

```bash
python -m scripts.amjd_portfolio_summary
```

Skrypt zbiera statystyki ze wszystkich kluczowych CSV i zapisuje je w formacie:

```text
dataset,metric,value
AMJD_VALIDACJA_MASTER_AM_validated,rows,28
AMJD_VALIDACJA_MASTER_AM_validated,status_JD.WARN,17
AMJD_VALIDACJA_MASTER_AM_validated,status_AM.OK,21
AMJD_VOLCANO_PROCESSED,rows,14
AMJD_VOLCANO_PROCESSED,delta_status.RANGE,8
...
```

Dodatkowo wypisuje czytelny raport w konsoli, np.:

- ile rekordów ma każdy zbiór,
- ile jest statusów `OK/WARN/NA`,
- jakie są maksymalne różnice `delta_JD` / `delta_AM`.

---

### 4.7. Master index eventów: `AMJD_EVENT_INDEX.csv`

Tworzony przez:

```bash
python -m scripts.amjd_event_index
```

To jest centralny **index wszystkich zdarzeń** w projekcie AMJD.

Dla każdego `key` (zaćmienia, wulkan, kotwica GSFC, itp.) zawiera m.in.:

- podstawowe dane:
  - `key`, `label`, `kind`,
  - `calendar`, `civil_date`, `julian_date`,
  - `jd_ut`, `jd_ut_source`.
- statusy walidacji:
  - `status_jd`,
  - `am_from_code_adjusted`, `delta_am_days`, `status_am`.
- informacje domenowe:
  - dla wulkanów: `volcano_name`, `volcano_vei`, `volcano_date_mode`,
  - dla RAW: `raw_present`, `raw_source_group`.
- topocentryka:
  - `topo_solar_sites`, `topo_solar_visible`,
  - `topo_lunar_sites`, `topo_lunar_visible`.

Ten plik jest idealnym punktem wyjścia do:

- budowy wykresów i wizualizacji,
- filtrowania eventów po rodzaju (`kind`, `volcano`, `solar_eclipse`, itp.),
- prezentacji projektu (jeden spójny timeline oparty na AM + danych NASA).

---

## 5. Typowy workflow (pod rekrutację)

1. **Zainstaluj projekt i odpal testy**  
   ```bash
   .\.venv\Scripts\activate.bat
   pytest -v
   ```

2. **Przelicz dane AMJD (jeśli trzeba odświeżyć)**  
   ```bash
   python -m scripts.amjd_validate_master
   python -m scripts.amjd_raw_to_master_like
   python -m scripts.amjd_volcano_process
   # ewentualnie skrypt do TOPO visibility, jeśli jest odseparowany od HTTP
   ```

3. **Zrób zbiorcze podsumowanie**  
   ```bash
   python -m scripts.amjd_portfolio_summary
   python -m scripts.amjd_event_index
   ```

4. **Odpal API** (opcjonalnie)  
   ```bash
   uvicorn app.main:app --reload
   ```

5. **Analiza / prezentacja**  
   - otwarcie `data/amjd/AMJD_EVENT_INDEX.csv` w narzędziu typu pandas/Excel,
   - filtrowanie po rodzajach eventów,
   - pokazanie w README / portfolio:
     - fragmentów CSV (np. `AMJD_VALIDACJA_MASTER_AM_validated.csv`),
     - wykresów błędów `delta_JD` / `delta_AM`,
     - przykładowych odpowiedzi API.

---

## 6. Podsumowanie

Projekt **AM-NASA v6** to:

- kompletny, przetestowany **silnik kalendarzowo-astronomiczny** (AM ↔ JD ↔ kalendarze cywilne),
- spinający się z **efemerydami JPL** (realne pozycje Słońca, Księżyca, planet),
- zweryfikowany na **danych NASA/GSFC** (zaćmienia, supernowe, kometa Halleya),
- rozszerzony o **dane wulkaniczne, RAW i topocentryczne**, 
- wyposażony w **skrypty walidacyjne** i **warstwę analityczną AMJD**.

Całość jest gotowa do użycia jako **case study** pokazujące:

- umiejętność pracy z danymi naukowymi (NASA, GSFC),
- projektowanie i implementację własnego systemu czasu,
- integrację Python + FastAPI + dane CSV + testy jednostkowe.
