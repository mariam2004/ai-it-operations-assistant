import pytest
from analytics import normalize_flag, safe_percent


@pytest.mark.parametrize(("value", "expected"), [
    ("1", True), ("TRUE", True), ("yes", True), ("breached", True),
    ("0", False), ("false", False), ("No", False), (None, None),
    ("Unknown Label", None),
])
def test_normalize_flag_only_interprets_known_values(value, expected):
    assert normalize_flag(value) is expected


def test_safe_percent():
    assert safe_percent(1, 4) == 25.0
    assert safe_percent(3, 0) is None


def test_analytics_do_not_treat_unknown_flag_as_false():
    assert normalize_flag("Pending Review") is None
