import math

from am_nasa.astro_sync import sync_am_to_jd_physical, sync_jd_to_am_physical


def test_sync_am_to_jd():
    jd = sync_am_to_jd_physical(739288.5, 2025)
    assert math.isclose(jd, 2460958.5, abs_tol=0.5)


def test_sync_jd_to_am():
    am = sync_jd_to_am_physical(2460958.5, 2025)
    assert math.isclose(am, 739288.5, abs_tol=0.5)
