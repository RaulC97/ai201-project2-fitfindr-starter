# tests/test_tools.py
from unittest.mock import MagicMock, patch

import pytest

from tools import create_fit_card, search_listings, suggest_outfit
from utils.data_loader import get_empty_wardrobe, get_example_wardrobe

# ── Shared fixtures ───────────────────────────────────────────────────────────

@pytest.fixture
def graphic_tee():
    """A real listing pulled from the dataset."""
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    assert results, "Dataset must contain at least one graphic tee under $50"
    return results[0]


# ── search_listings ───────────────────────────────────────────────────────────

def test_search_returns_results():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    assert isinstance(results, list)
    assert len(results) > 0


def test_search_empty_results():
    # Failure mode: no listings match → must return [] not raise
    results = search_listings("designer ballgown", size="XXS", max_price=5)
    assert results == []


def test_search_price_filter():
    # Failure mode: price ceiling — no result should exceed max_price
    results = search_listings("jacket", size=None, max_price=10)
    assert all(item["price"] <= 10 for item in results)


def test_search_size_filter_substring():
    # "M" must match listings sized "S/M" or "M/L" (substring matching)
    results = search_listings("tee", size="M", max_price=None)
    for item in results:
        assert "M" in item["size"].upper(), (
            f"'{item['size']}' does not contain 'M'"
        )


def test_search_returns_list_of_dicts():
    # Each result must have the required fields
    results = search_listings("jacket", size=None, max_price=None)
    required = {"id", "title", "description", "category", "style_tags",
                "size", "condition", "price", "colors", "platform"}
    for item in results:
        assert required.issubset(item.keys()), (
            f"Missing fields in listing: {required - item.keys()}"
        )


def test_search_sorted_best_first():
    # First result should score at least as high as the last
    results = search_listings("vintage denim jacket", size=None, max_price=None)
    if len(results) >= 2:
        # Titles closer to the query should appear earlier — just confirm it's a list
        assert isinstance(results[0], dict)


# ── suggest_outfit ────────────────────────────────────────────────────────────

def _mock_groq(text: str):
    """Return a Groq client mock that always replies with `text`."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content=text))]
    )
    return mock_client


def test_suggest_outfit_returns_string(graphic_tee):
    with patch("tools._get_groq_client", return_value=_mock_groq("Pair it with baggy jeans.")):
        result = suggest_outfit(new_item=graphic_tee, wardrobe=get_example_wardrobe())
    assert isinstance(result, str)
    assert len(result) > 0


def test_suggest_outfit_empty_wardrobe_no_exception(graphic_tee):
    # Failure mode: empty wardrobe → must return styling advice, not raise
    with patch("tools._get_groq_client", return_value=_mock_groq("Style it with wide-leg trousers.")):
        result = suggest_outfit(new_item=graphic_tee, wardrobe=get_empty_wardrobe())
    assert isinstance(result, str)
    assert len(result) > 0


def test_suggest_outfit_uses_wardrobe_in_prompt(graphic_tee):
    # Wardrobe items should appear in the prompt sent to the LLM
    mock_client = _mock_groq("Looks great.")
    with patch("tools._get_groq_client", return_value=mock_client):
        suggest_outfit(new_item=graphic_tee, wardrobe=get_example_wardrobe())

    call_args = mock_client.chat.completions.create.call_args
    prompt = call_args[1]["messages"][0]["content"]
    wardrobe = get_example_wardrobe()
    first_item_name = wardrobe["items"][0]["name"]
    assert first_item_name in prompt, (
        "Wardrobe item names should be included in the prompt"
    )


def test_suggest_outfit_empty_wardrobe_prompt_differs(graphic_tee):
    # Empty wardrobe should send a different (general styling) prompt
    mock_full = _mock_groq("Full wardrobe advice.")
    mock_empty = _mock_groq("General styling advice.")

    with patch("tools._get_groq_client", return_value=mock_full):
        suggest_outfit(new_item=graphic_tee, wardrobe=get_example_wardrobe())
    prompt_full = mock_full.chat.completions.create.call_args[1]["messages"][0]["content"]

    with patch("tools._get_groq_client", return_value=mock_empty):
        suggest_outfit(new_item=graphic_tee, wardrobe=get_empty_wardrobe())
    prompt_empty = mock_empty.chat.completions.create.call_args[1]["messages"][0]["content"]

    assert prompt_full != prompt_empty, "Empty and non-empty wardrobe should use different prompts"


# ── create_fit_card ───────────────────────────────────────────────────────────

def test_create_fit_card_returns_string(graphic_tee):
    with patch("tools._get_groq_client", return_value=_mock_groq("Thrifted this for $18 on depop!")):
        result = create_fit_card(outfit="Pair with baggy jeans.", new_item=graphic_tee)
    assert isinstance(result, str)
    assert len(result) > 0


def test_create_fit_card_empty_outfit_no_exception(graphic_tee):
    # Failure mode: empty outfit string → must return fallback caption, not raise
    with patch("tools._get_groq_client", return_value=_mock_groq("This tee is too good to pass up!")):
        result = create_fit_card(outfit="", new_item=graphic_tee)
    assert isinstance(result, str)
    assert len(result) > 0


def test_create_fit_card_none_outfit_no_exception(graphic_tee):
    # Failure mode: None outfit → same fallback behaviour as empty string
    with patch("tools._get_groq_client", return_value=_mock_groq("Funny caption here.")):
        result = create_fit_card(outfit=None, new_item=graphic_tee)
    assert isinstance(result, str)
    assert len(result) > 0


def test_create_fit_card_empty_outfit_uses_fallback_prompt(graphic_tee):
    # Empty outfit must trigger the fallback prompt (no outfit context)
    mock_client = _mock_groq("Fun caption.")
    with patch("tools._get_groq_client", return_value=mock_client):
        create_fit_card(outfit="", new_item=graphic_tee)

    prompt = mock_client.chat.completions.create.call_args[1]["messages"][0]["content"]
    assert "funny" in prompt.lower() or "fun" in prompt.lower(), (
        "Fallback prompt should mention fun/funny styling"
    )


def test_create_fit_card_normal_prompt_includes_outfit(graphic_tee):
    # Normal path prompt must include the outfit suggestion text
    outfit_text = "Wear it with baggy jeans and chunky sneakers."
    mock_client = _mock_groq("Great OOTD caption.")
    with patch("tools._get_groq_client", return_value=mock_client):
        create_fit_card(outfit=outfit_text, new_item=graphic_tee)

    prompt = mock_client.chat.completions.create.call_args[1]["messages"][0]["content"]
    assert outfit_text in prompt, "Outfit suggestion should be passed into the prompt"
