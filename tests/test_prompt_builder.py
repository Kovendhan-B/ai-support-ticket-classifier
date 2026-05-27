import pytest
from ai_ticket_classifier import prompt_builder


def test_load_prompt_v1():
    prompt = prompt_builder.load_prompt("v1")
    assert isinstance(prompt, str)
    assert "Category definitions" in prompt or "Categories:" in prompt

def test_load_prompt_v2():
    prompt = prompt_builder.load_prompt("v2")
    assert isinstance(prompt, str)
    assert "Category definitions" in prompt or "Categories:" in prompt

def test_build_prompt_injects_ticket_text():
    ticket = "Test ticket text for injection."
    version = "v1"
    prompt = prompt_builder.build_prompt(ticket, version)
    assert ticket in prompt


def test_load_prompt_file_not_found():
    with pytest.raises(FileNotFoundError) as excinfo:
        prompt_builder.load_prompt("nonexistent")
    assert "Prompt template not found" in str(excinfo.value)
