from core.market_universe import DEFAULT_UNIVERSE


def test_canonical_universe_is_unique_and_contains_focus_exposure():
    assert len(DEFAULT_UNIVERSE) == 276
    assert len(DEFAULT_UNIVERSE) == len(set(DEFAULT_UNIVERSE))
    assert {"TLN", "AMAT", "LMT", "WM", "SMH", "ITA"}.issubset(DEFAULT_UNIVERSE)
    assert "BRK.B" not in DEFAULT_UNIVERSE
    assert "SQ" not in DEFAULT_UNIVERSE
    assert "BRK-B" in DEFAULT_UNIVERSE
    assert "XYZ" in DEFAULT_UNIVERSE


def test_universe_is_not_mutated_by_a_consumer_copy():
    consumer = list(DEFAULT_UNIVERSE)
    consumer.append("TEST")
    assert "TEST" not in DEFAULT_UNIVERSE
