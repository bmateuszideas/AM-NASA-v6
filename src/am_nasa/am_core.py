from __future__ import annotations

# am_core.py — rdzeń AM ↔ JD bez żadnych korekt, deterministyczny

# >>> KLUCZOWA STAŁA <<<
# Empirycznie zweryfikowana na Twoich testach współczesnych dat:
# 2025-10-09: JD=2460958.5 i AM=739288.5 => JD − AM = 1_721_670.0
AM_EPOCH_JD: float = 1721670.0

def am_from_jd(jd: float, _year: float | int | None = None) -> float:
    """
    Konwersja JD -> AM.
    Brak jakichkolwiek poprawek (ΔT, strefy, fazy, itp.). Czysta arytmetyka.
    """
    return jd - AM_EPOCH_JD

def jd_from_am(am: float, _year: float | int | None = None) -> float:
    """
    Konwersja AM -> JD.
    Brak jakichkolwiek poprawek. Czysta arytmetyka.
    """
    return am + AM_EPOCH_JD

def jd_am_roundtrip(am: float) -> float:
    return am_from_jd(jd_from_am(am))
