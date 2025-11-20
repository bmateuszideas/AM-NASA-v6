# AM‑JD — BIAŁA KSIĘGA (v1.0)

**Cel**: Jedno spójne źródło prawdy o systemie AM‑JD — co to jest, jak liczy, jakie przyjmuje konwencje, jak go testować, jak go falsyfikować i jak integrować z efemerydami NASA/JPL. Zero mgły, sama mechanika.

_Wersja:_ 1.0 · _Zbudowano:_ 2025-11-02T08:30:48Z · _Autor systemu:_ Mateusz (AM) · _Format:_ Markdown

---

## 0) TL;DR — o co chodzi w AM‑JD
- **AM** = dowolna skala „Anno Mundi/Anno Mateusz” z przesunięciem względem JD: `AM = JD + C` (stała `C`).  
- **JD** = Julian Day (ciągły licznik dni, doba liczona od **południa** UT).  
- **Idea:** Mapujesz **cywilny zapis daty** → `JD_record`, a **astronomiczne zjawisko** → `JD_ephem`. Porównujesz `ΔJD = JD_record − JD_ephem`. Jeśli |ΔJD| ≤ **tolerancja**, zapis jest **spójny**.
- **Inwariancja offsetu:** stała `C` **znosi się** w różnicy (`(JD+C)-(JD'+C)=JD-JD'`). Dlatego spory o „epoki/etykiety” są poza matematyką rdzenia.

---

## 1) Kanon konwencji (AM‑JD Canon)
**Po co kanon?** Żeby wszyscy liczyli tak samo i wyniki były replikowalne.

1. **Skala czasu:** UT (dla dat cywilnych). Do efemeryd możesz użyć TT/TDB (zwracaj uwagę na ΔT).
2. **Epoka JD:** `midnight` w praktyce raportowania → 00:00 UT ma ułamek **.5** (bo „prawdziwy” JD zmienia się w południe).  
3. **Numeracja lat:** **astronomiczna** (1 BCE = 0; 2 BCE = −1; …).  
4. **Kalendarz cywilny:** do 1582‑10‑15 **juliański**, potem **gregoriański** (z lokalnym dniem przyjęcia, jeśli istotne).  
5. **Styl doby:** jeśli źródło liczy dobę **od północy** → dodaj `jd_offset = +0.5`. Jeśli od **zachodu** → zastosuj właściwą frakcję w zależności od godziny zachodu (jeśli brak — oceń tolerancją ±1 d).  
6. **Tolerancje:** `OK` |ΔJD| ≤ 0.5 d; `WARN` 0.5–5 d; `FAIL` > 5 d.  
7. **Zasada jawności:** publikuj ścieżkę: **kalendarz → (y,m,d) → JDN → JD + offset**, oraz **godzinę**, jeśli ją znasz.

> ***Gwiazdkowa ściąga błędów***  
> ★ Południe vs północ JD → ustaw epokę raportową **midnight** (00:00 UT ⇒ +0.5).  
> ★ Rok 0 → w astronomii **istnieje**; w historii nie. Licz na numeracji astronomicznej.  
> ★ Kalendarz → **juliański** dla starożytności; proleptyczny gregoriański daje przesunięcia.  
> ★ Święta hebrajskie → mapuj **Hebrew → (lokalny) juliański → JD** i jawnie deklaruj ΔT/widzialność.

---

## 2) Definicje i warstwy
- **JD/JDN**: JDN = część całkowita JD. JD to JDN ± frakcja doby (południowy start).
- **Warstwa roczna** (dendro/¹⁴C/lód) → mówi „rok/okno/sezon”.  
- **Warstwa kalendarzowa** → reguły kulturowe (proleptyka, interkalacje, początek doby/roku).  
- **Warstwa dzienna** → redukcja zapisu do `JD_record`.  
- **Weryfikacja** → efemeryda (`JD_ephem`) vs `JD_record`: liczysz `ΔJD`.

**Zakaz**: mieszania rocznej z dzienną **bez** przejścia przez warstwę kalendarzową — to tworzy pseudo‑konflikty.

---

## 3) Algorytm mapowania „zapis → JD_record”
**Wejście:** `(calendar, year, month, day, jd_offset)`  
**Wyjście:** `JD_record = JDN(calendar, y,m,d) + jd_offset`

**Fliegel–Van Flandern (JDN):**
```text
# Gregoriański
a = (14 - m) // 12
y2 = y + 4800 - a
m2 = m + 12a - 3
JDN = d + (153m2 + 2)//5 + 365y2 + y2//4 - y2//100 + y2//400 - 32045

# Juliański
a = (14 - m) // 12
y2 = y + 4800 - a
m2 = m + 12a - 3
JDN = d + (153m2 + 2)//5 + 365y2 + y2//4 - 32083
```

**Epoka raportowa `midnight`:** Jeśli wpis jest „00:00 UT (cywilnie)”, dodaj **+0.5** do JDN, by dostać JD.

**Inwariancja offsetu (dowód w 1 linijce):**  
`(JD_record + C) − (JD_ephem + C) = JD_record − JD_ephem` → różnice **nie zależą** od wyboru epoki/etykiet.

---

## 4) Walidacja na efemerydach NASA/JPL
**Cel:** nie „wiara”, lecz **liczby**. Procedura minimalna:
1. Z mapowanego zapisu wylicz `JD_record` (zgodnie z Kanonem).  
2. Z **JPL Horizons/GSFC** pobierz czasy zjawiska (UT/TT) i przelicz na `JD_ephem`.  
3. Policz `ΔJD` i oceń względem tolerancji.  
4. Udokumentuj: skala czasu (UT/TT/TDB), ΔT jeśli użyte, lokalizacja obserwatora.

**Przykładowe kotwice:**
- **0033‑04‑03 (jul.)** — częściowe **zaćmienie Księżyca** (maks. ~14:55:49 UT) → `JD_ephem ≈ 1733204.622`.  
- **0066‑01‑26 (jul.)** — peryhelium **komety Halleya** (powrót 66 CE); obserwacje do marca/kwietnia.  
- **Potrójna koniunkcja Jowisz–Saturn, 7 BCE** — trzy okna (maj, wrzesień, grudzień).

---

## 5) Harness testowy (replikowalność)
**Format wejścia CSV:** `id,event,calendar,year,month,day,jd_ephem,jd_offset,notes`  
- `calendar`: „Julian”/„Gregorian” (jawnie, bez magii 1582).  
- `year`: **astronomiczny**.  
- `jd_offset`: zwykle `0.5` gdy doba „od północy”.

**Statusy:** `PASS` jeśli |ΔJD| ≤ tolerancja; `MISSING_EPHEM` gdy brak `jd_ephem`; inaczej `FAIL`.

**Linie komend (pojedyncze, zgodnie z Twoją preferencją):**
- **PowerShell:** `python .\am_jd_test_harness.py .\cases.csv .\results.csv 1.0`  
- **CMD:** `python am_jd_test_harness.py cases.csv results.csv 1.0`  
- **Bash/WSL:** `python am_jd_test_harness.py cases.csv results.csv 1.0`  
- **VS Code:** `python am_jd_test_harness.py cases.csv results.csv 1.0`

**Kryterium zaliczenia:** ≥ **90% PASS** przy progu |ΔJD| ≤ **1.0 d**.

---

## 6) Przykłady (z gwiazdkami — *na co uważać*)
> Uwaga: poniżej **schemat** prezentacji. Tabele referencyjne i pełne wyprowadzenia masz w plikach „Raport poprawiony” i „Errata & Kanon”.

### 6.1 Narodziny (5 XII 7 BCE, jul. 00:00 UT)
- `JD_record = 1719205.0` (midnight ⇒ +0.5)  
- Etykieta „oczekiwana” była `1719570.5` → **ΔJD = −365.5 d**  
- ★ **Uwaga (rok 0):** 7 BCE = **astron. −6**. Licz w **juliańskim** dla starożytności.  
- **Dlaczego juliański:** bo to ściśle cywilny kalendarz epoki; proleptyczny gregoriański fałszuje dzień.

### 6.2 Ukrzyżowanie a zaćmienie (0033‑04‑03, jul.)
- `JD_ephem (max LUN eclipse) ≈ 1733204.622` (GSFC/JPL)  
- Jeśli chcesz dowiązać wydarzenie — data cywilna musi przejść przez **reguły żydowskie** → lokalny juliański → JD.  
- ★ **Uwaga (epoki/TT):** do porównań z efemerydą dokumentuj **UT/TT/TDB** i ΔT.

### 6.3 Halley 66 CE (okno widoczności a TP)
- `TP` (peryhelium) ~ **66‑01‑26 (jul.)**, obserwacje także **marzec–kwiecień**.  
- Wpis **25‑03‑66** leży w oknie po TP → sensowne `ΔJD`.

### 6.4 Zdarzenia nie‑astronomiczne (np. 70 CE)
- JPL nie „potwierdza” dat historycznych bez zjawisk; tu stosujesz tylko **warstwę kalendarzową** i spójność AM↔JD.

---

## 7) Test „w ciemno” dla krytyków (jak zamknąć dyskusję)
1. Przygotuj ≥ 15 **nowych** zapisów dziennych (zaćmienia, komety).  
2. Wypełnij CSV/JSON (klucze jak wyżej).  
3. Odpal harness i **wklej results.csv** z kolumnami: `JD_record, JD_ephem, ΔJD, OffsetInvarianceCheck, Status`.  
4. Jeśli FAIL → wskaż **który krok** (kalendarz, interkalacja, styl doby) i zaproponuj alternatywę; licz ponownie.  
5. Jeśli ≥90% PASS → warstwa **dzienna** przechodzi; kolejne spory przenoszą się na **warstwę roczną** (dendro/¹⁴C/lód).

**Statement do cytowania:** „**Kiedy liczę — AM/JD wygrywa; kiedy wierzę — przegrywa.**”

---

## 8) FAQ / Debug
- **ΔJD ≈ ±0.5 d?** → epoka JD (południe/północ). Ustaw `midnight` i raportuj `+0.5`.
- **ΔJD ≈ ±365 d?** → **rok 0**/numeracja BCE vs astronomiczna.
- **ΔJD w dniach 1–40?** → **kalendarz** (juliański vs proleptyczny gregoriański).
- **Brak zgodności z JPL?** → sprawdź **skalę czasu** (UT/TT/TDB) i **ΔT**; ew. lokalizację obserwatora.
- **Święta żydowskie (14 Nisan etc.)?** → jawny model interkalacji i widzialności + ΔT.

---

## 9) Schemat danych (CSV/JSON)
**CSV kolumny:** `id,event,calendar,year,month,day,jd_ephem,jd_offset,notes`  
**JSON:** lista obiektów z tymi samymi kluczami. `year` w **astronomicznej** numeracji.

---

## 10) Minimalne wymagania publikacji AM‑JD
- Publiczny **kanon konwencji** (ten dokument).  
- **Repo z harness’em** i przykładowymi pakietami sprawdzającymi.  
- **Załączone results.csv** dla zewnętrznych zestawów (≥ 15 rekordów).  
- Opis **różnic** (ΔJD) i ich przyczyn (gwiazdki), bez ideologii — tylko liczby.

---

## 11) Słowniczek
- **JD/JDN** — Julian Day/Number.  
- **UT/TT/TDB** — skale czasu (cywilna/atomowa/barycentryczna).  
- **ΔT** — różnica TT−UT.  
- **Proleptyczny gregoriański** — rozszerzenie kalendarza gregoriańskiego wstecz przed 1582 (nie używaj do starożytności).

---

## 12) Credits i wersjonowanie
- Koncepcja/autor: **Mateusz** (AM).  
- Niniejsza biała księga syntezuje: **kanon**, **erratę**, **raport z przykładami** oraz **protokół testów**.  
- Wersja 1.0 — stabilna pod testy „w ciemno”.

---

**Koniec dokumentu.**
