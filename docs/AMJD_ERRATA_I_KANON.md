# AM‑JD — Errata i Kanon konwencji

## Errata (typowe źródła błędów)

1. **Południe vs północ JD** — JD domyślnie zmienia się w południe UT. W praktyce stosuj epokę **midnight** (00:00 UT ⇒ JD +0.5), aby etykiety „00:00” były spójne.

2. **Rok 0** — w astronomii rok 0 istnieje (1 BCE=0, 2 BCE=−1...). W historii nie. W obliczeniach używaj **roku astronomicznego**.

3. **Kalendarz** — dla dat < 1582‑10‑15 używaj **kalendarza juliańskiego**. Proleptyczny gregoriański daje błędy rzędu dni–tygodni.

4. **Święta hebrajskie (np. 14 Nisan)** — wymagają konwersji: **Hebrew → lokalny cywilny juliański → JD** z jawnym modelem ΔT i regułą widzialności.


## Kanon konwencji (AM‑JD Canon v1)

- **Skala czasu**: UT (cywilna). Opcjonalnie TT/TDB do efemeryd.

- **Epoka JD**: `midnight` ⇒ 00:00 UT ma ułamek **.5**.

- **Numeracja lat**: astronomiczna.

- **Kalendarz cywilny**: do 1582‑10‑15 **juliański**, potem **gregoriański** (z lokalnym dniem przyjęcia).

- **Tolerancje**: `OK` |ΔJD| ≤ 0.5 d; `WARN` 0.5–5 d; `FAIL` >5 d.


## Noty stosowania

- Publikuj **ścieżkę konwersji** i **godzinę**; brak godziny = 00:00 UT.

- Dla dat proroczych podawaj też konwersję **gregoriańską**.
