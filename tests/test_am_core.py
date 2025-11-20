import math

from am_nasa.am_core import AM_EPOCH_JD, am_from_jd, jd_from_am


def test_epoch_zero():
    """AM=0 powinno dawać JD=AM_EPOCH_JD."""
    jd = jd_from_am(0.0)
    assert math.isclose(jd, AM_EPOCH_JD, abs_tol=1e-6)


def test_roundtrip_simple():
    """Prosty roundtrip JD -> AM -> JD."""
    jd = 2460958.5  # 2025-10-09
    am = am_from_jd(jd, 2025)
    jd2 = jd_from_am(am, 2025)
    assert math.isclose(jd, jd2, abs_tol=1e-6)


def test_pre_epoch_roundtrip():
    """Test poprawności dla dat przed epoką AM."""
    jd = 1000000.5
    am = am_from_jd(jd, -2300)
    jd2 = jd_from_am(am, -2300)
    # Starsze daty dopuszczamy z trochę większą tolerancją
    assert math.isclose(jd, jd2, abs_tol=1.0)


def test_epoch_constant_difference():
    """Średnia różnica JD - (JD zroundtripowany przez AM) powinna być ~0."""
    jd_values = [1439595.5, 1507920.5, 2440423.5, 2460958.5]
    diffs = [jd - jd_from_am(am_from_jd(jd)) for jd in jd_values]
    mean_diff = sum(diffs) / len(diffs)
    assert math.isclose(mean_diff, 0.0, abs_tol=1e-5)
