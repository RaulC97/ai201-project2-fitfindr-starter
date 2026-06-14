"""
toolstests.py

Manual tests for each FitFindr tool. Run this file directly to verify
each tool works before wiring them into the agent loop.

Usage:
    python tests/toolstests.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.data_loader import get_example_wardrobe, get_empty_wardrobe
from tools import search_listings, suggest_outfit, create_fit_card


def divider(label: str):
    print("\n" + "=" * 50)
    print(f"  TEST: {label}")
    print("=" * 50)


# ── search_listings tests ─────────────────────────────────────────────────────

def test_search_listings_normal():
    """Should find graphic tees in size M under $30."""
    divider("search_listings — vintage graphic tee, size M, max $30")
    results = search_listings(
        description="vintage graphic tee",
        size="M",
        max_price=30.0,
    )
    print(f"\nReturned {len(results)} result(s)")
    for i, item in enumerate(results):
        print(f"  [{i}] {item['title']} | size {item['size']} | ${item['price']:.2f} | {item['platform']}")
    assert isinstance(results, list), "Should return a list"
    print("\nPASSED")


def test_search_listings_no_size_no_price():
    """Should return results using only the description."""
    divider("search_listings — no size or price filter")
    results = search_listings(description="denim jacket")
    print(f"\nReturned {len(results)} result(s)")
    for i, item in enumerate(results):
        print(f"  [{i}] {item['title']} | size {item['size']} | ${item['price']:.2f}")
    assert isinstance(results, list), "Should return a list"
    print("\nPASSED")


def test_search_listings_no_match():
    """Should return an empty list when nothing matches."""
    divider("search_listings — no match expected")
    results = search_listings(
        description="astronaut spacesuit",
        size="XS",
        max_price=5.0,
    )
    print(f"\nReturned {len(results)} result(s)")
    assert results == [], f"Expected [], got {results}"
    print("PASSED")


def test_search_listings_impossible_query():
    """Ballgown size XXS under $5 — confirms empty list without exception."""
    divider("search_listings — designer ballgown, size XXS, max $5")
    results = search_listings(
        description="designer ballgown",
        size="XXS",
        max_price=5.0,
    )
    print(f"\nReturned {len(results)} result(s)")
    assert results == [], f"Expected [], got {results}"
    print("PASSED — empty list returned, no exception raised")


def test_search_listings_price_only():
    """Should return all listings under $20 matching the description."""
    divider("search_listings — sneakers, max $20")
    results = search_listings(description="sneakers", max_price=20.0)
    print(f"\nReturned {len(results)} result(s)")
    for item in results:
        print(f"  {item['title']} | ${item['price']:.2f}")
        assert item["price"] <= 20.0, f"Price ${item['price']} exceeds max $20"
    print("\nPASSED")


# ── suggest_outfit tests ──────────────────────────────────────────────────────

# Grab a real listing to use as new_item across all suggest_outfit tests
_SAMPLE_ITEM = search_listings(description="vintage graphic tee", size="M", max_price=30.0)
_NEW_ITEM = _SAMPLE_ITEM[0] if _SAMPLE_ITEM else {
    "title": "Fallback Graphic Tee",
    "description": "A cool vintage graphic tee",
    "style_tags": ["graphic tee", "vintage", "streetwear"],
    "colors": ["white", "black"],
    "category": "tops",
    "price": 20.0,
    "platform": "depop",
}


def test_suggest_outfit_with_wardrobe():
    """Should return a 1-2 sentence outfit using items from the wardrobe."""
    divider("suggest_outfit — with example wardrobe")
    wardrobe = get_example_wardrobe()
    result = suggest_outfit(new_item=_NEW_ITEM, wardrobe=wardrobe)
    print(f"\nSuggestion:\n  {result}")
    assert isinstance(result, str), "Should return a string"
    assert len(result) > 0, "Should not return an empty string"
    print("\nPASSED")


def test_suggest_outfit_empty_wardrobe():
    """Should return general styling advice when wardrobe is empty."""
    divider("suggest_outfit — empty wardrobe")
    wardrobe = get_empty_wardrobe()
    result = suggest_outfit(new_item=_NEW_ITEM, wardrobe=wardrobe)
    print(f"\nSuggestion:\n  {result}")
    assert isinstance(result, str), "Should return a string"
    assert len(result) > 0, "Should not return an empty string"
    print("\nPASSED")


# ── create_fit_card tests ─────────────────────────────────────────────────────

def test_create_fit_card_normal():
    """Should return a caption using a real outfit suggestion and item."""
    divider("create_fit_card — normal path")
    outfit = suggest_outfit(new_item=_NEW_ITEM, wardrobe=get_example_wardrobe())
    result = create_fit_card(outfit=outfit, new_item=_NEW_ITEM)
    print(f"\nCaption:\n  {result}")
    assert isinstance(result, str), "Should return a string"
    assert len(result) > 0, "Should not return an empty string"
    print("\nPASSED")


def test_create_fit_card_empty_outfit():
    """Should return a fun fallback caption when outfit string is empty."""
    divider("create_fit_card — empty outfit fallback")
    result = create_fit_card(outfit="", new_item=_NEW_ITEM)
    print(f"\nCaption:\n  {result}")
    assert isinstance(result, str), "Should return a string"
    assert len(result) > 0, "Should not return an empty string"
    print("\nPASSED")


def test_create_fit_card_none_outfit():
    """Should return a fun fallback caption when outfit is None — no exception."""
    divider("create_fit_card — None outfit fallback")
    result = create_fit_card(outfit=None, new_item=_NEW_ITEM)
    print(f"\nCaption:\n  {result}")
    assert isinstance(result, str), "Should return a string"
    assert len(result) > 0, "Should not return an empty string"
    print("\nPASSED")


# ── Run all tests ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\nRunning search_listings tests...\n")
    test_search_listings_normal()
    test_search_listings_no_size_no_price()
    test_search_listings_no_match()
    test_search_listings_impossible_query()
    test_search_listings_price_only()
    print("\n" + "=" * 50)
    print("  All search_listings tests complete!")
    print("=" * 50 + "\n")

    print("\nRunning suggest_outfit tests...\n")
    test_suggest_outfit_with_wardrobe()
    test_suggest_outfit_empty_wardrobe()
    print("\n" + "=" * 50)
    print("  All suggest_outfit tests complete!")
    print("=" * 50 + "\n")

    print("\nRunning create_fit_card tests...\n")
    test_create_fit_card_normal()
    test_create_fit_card_empty_outfit()
    test_create_fit_card_none_outfit()
    print("\n" + "=" * 50)
    print("  All create_fit_card tests complete!")
    print("=" * 50 + "\n")
