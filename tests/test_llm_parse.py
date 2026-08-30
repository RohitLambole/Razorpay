import pytest
from app.llm import parse_action


def test_parse_valid_action():
    txt = '''{
  "action": "compute_quote",
  "params": {"merchant_id": "m1", "items": []},
  "explain": "test"
}'''
    out = parse_action(txt)
    assert out["action"] == "compute_quote"


def test_parse_invalid_json():
    with pytest.raises(ValueError):
        parse_action("not a json")
