import pytest

from tests.conftest import FakeLLMClient


def test_parse_json_safe_handles_plain_json():
    result = FakeLLMClient._parse_json_safe('{"a": 1}')
    assert result == {"a": 1}


def test_parse_json_safe_strips_markdown_fence():
    text = '```json\n{"a": 1, "b": [1, 2]}\n```'
    result = FakeLLMClient._parse_json_safe(text)
    assert result == {"a": 1, "b": [1, 2]}


def test_parse_json_safe_strips_bare_fence():
    text = '```\n{"a": 1}\n```'
    result = FakeLLMClient._parse_json_safe(text)
    assert result == {"a": 1}


def test_parse_json_safe_extracts_embedded_json():
    text = 'Sure, here you go:\n{"a": 1}\nHope that helps!'
    result = FakeLLMClient._parse_json_safe(text)
    assert result == {"a": 1}


def test_parse_json_safe_raises_on_garbage():
    with pytest.raises(ValueError):
        FakeLLMClient._parse_json_safe("not json at all")


def test_generate_json_appends_json_instruction_and_parses():
    client = FakeLLMClient(responses=[{"result": "ok"}])
    result = client.generate_json("Analyze this", system_instruction="You are helpful")

    assert result == {"result": "ok"}
    call = client.calls[0]
    assert "JSON" in call["prompt"]
    assert "JSON" in call["system_instruction"]
    assert call["config"] == {"temperature": 0.0}
