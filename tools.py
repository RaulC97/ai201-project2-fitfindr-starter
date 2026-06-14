"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A list of matching listing dicts, sorted by relevance (best match first).
        Returns an empty list if nothing matches — does NOT raise an exception.

    Each listing dict has the following fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand, platform

    TODO:
        1. Load all listings with load_listings().
        2. Filter by max_price and size (if provided).
        3. Score each remaining listing by keyword overlap with `description`.
        4. Drop any listings with a score of 0 (no relevant matches).
        5. Sort by score, highest first, and return the listing dicts.

    Before writing code, fill in the Tool 1 section of planning.md.
    """
    print(f"[search_listings] Searching for: '{description}'"
          + (f", size {size}" if size else "")
          + (f", max ${max_price:.2f}" if max_price is not None else ""))

    listings = load_listings()
    print(f"[search_listings] Loaded {len(listings)} total listings")

    # Filter by price
    if max_price is not None:
        listings = [l for l in listings if l["price"] <= max_price]
        print(f"[search_listings] After price filter (<= ${max_price:.2f}): "
              f"{len(listings)} listings")

    # Filter by size — substring match so "M" matches "S/M", "M/L", etc.
    if size is not None:
        listings = [l for l in listings if l.get("size") and size.upper() in l["size"].upper()]
        print(f"[search_listings] After size filter ({size}): {len(listings)} listings")

    # Extract meaningful keywords from the description
    stop_words = {"a", "an", "the", "for", "in", "with", "and", "or", "of",
                  "is", "i", "am", "looking", "mostly", "wear", "want", "some",
                  "im", "i'm", "me", "my", "find", "need", "get"}
    cleaned = [w.strip(".,!?\"'") for w in description.lower().split()]
    keywords = {w for w in cleaned if w not in stop_words}
    print(f"[search_listings] Keywords extracted: {sorted(keywords)}")

    # Score each listing by weighted keyword overlap (title > tags > category > description)
    scored = []
    for listing in listings:
        title_blob = listing.get("title", "").lower()
        tags_blob  = " ".join(listing.get("style_tags", [])).lower()
        cat_blob   = listing.get("category", "").lower()
        desc_blob  = listing.get("description", "").lower()

        score = 0
        for kw in keywords:
            if kw in title_blob: score += 4
            if kw in tags_blob:  score += 3
            if kw in cat_blob:   score += 2
            if kw in desc_blob:  score += 1

        if score > 0:
            scored.append((score, listing))

    scored.sort(key=lambda x: x[0], reverse=True)

    # Drop results scoring below 30% of the top score (weak / unrelated matches)
    if scored:
        min_score = max(1, scored[0][0] * 0.3)
        scored = [(s, l) for s, l in scored if s >= min_score]

    results = [listing for _, listing in scored]

    if results:
        print(f"[search_listings] Found {len(results)} matching listings")
        print(f"[search_listings] Top result: '{results[0]['title']}' (${results[0]['price']:.2f})")
    else:
        print("[search_listings] No matching listings found")

    return results


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item
        rather than raising an exception or returning an empty string.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If empty: call the LLM with a prompt for general styling ideas
           (what kinds of items pair well, what vibe it suits, etc.).
        3. If not empty: format the wardrobe items into a prompt and ask
           the LLM to suggest specific outfit combinations using the new item
           and named pieces from the wardrobe.
        4. Return the LLM's response as a string.

    Before writing code, fill in the Tool 2 section of planning.md.
    """
    print(f"[suggest_outfit] Generating outfit suggestion for: '{new_item.get('title', 'unknown item')}'")

    wardrobe_items = wardrobe.get("items", [])
    is_empty = len(wardrobe_items) == 0

    if is_empty:
        print("[suggest_outfit] Wardrobe is empty — will give general styling advice")
        prompt = f"""You are a thrift fashion stylist. A user just found this item:

Title: {new_item.get('title', '')}
Description: {new_item.get('description', '')}
Style tags: {', '.join(new_item.get('style_tags', []))}
Colors: {', '.join(new_item.get('colors', []))}
Category: {new_item.get('category', '')}

They don't have a wardrobe saved yet. Give them 1-2 sentences of general styling advice: what kinds of pieces pair well with this item and what vibe or aesthetic it fits. Be specific and casual."""
    else:
        print(f"[suggest_outfit] Wardrobe has {len(wardrobe_items)} items — finding outfit combinations")
        wardrobe_list = "\n".join(
            f"- {item['name']} ({item['category']}, {', '.join(item.get('colors', []))})"
            for item in wardrobe_items
        )
        prompt = f"""You are a thrift fashion stylist. A user just thrifted this item:

Title: {new_item.get('title', '')}
Description: {new_item.get('description', '')}
Style tags: {', '.join(new_item.get('style_tags', []))}
Colors: {', '.join(new_item.get('colors', []))}

Their current wardrobe includes:
{wardrobe_list}

Suggest 1-2 specific outfit combinations using the new item and named pieces from their wardrobe. Be casual and specific — mention the actual piece names. Keep it to 1-2 sentences."""

    client = _get_groq_client()
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=200,
    )
    suggestion = response.choices[0].message.content.strip()
    print(f"[suggest_outfit] Suggestion generated ({len(suggestion)} chars)")
    return suggestion


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.

    The caption should:
    - Feel casual and authentic (like a real OOTD post, not a product description)
    - Mention the item name, price, and platform naturally (once each)
    - Capture the outfit vibe in specific terms
    - Sound different each time for different inputs (use higher LLM temperature)

    TODO:
        1. Guard against an empty or whitespace-only outfit string.
        2. Build a prompt that gives the LLM the item details and the outfit,
           and asks for a caption matching the style guidelines above.
        3. Call the LLM and return the response.

    Before writing code, fill in the Tool 3 section of planning.md.
    """
    print(f"[create_fit_card] Creating fit card for: '{new_item.get('title', 'unknown item')}'")

    has_outfit = bool(outfit and outfit.strip())

    if not has_outfit:
        print("[create_fit_card] WARNING: outfit string is empty — generating fun fallback caption")
        prompt = f"""You are writing a casual, funny Instagram caption for a thrift find. Keep it 2-4 sentences.

The item: {new_item.get('title', 'this amazing thrift find')} — ${new_item.get('price', 0.0):.2f} from {new_item.get('platform', 'thrift')}
Description: {new_item.get('description', '')}

Write a fun or funny caption about this item alone. Mention the price and platform naturally once each. Caption:"""
    else:
        prompt = f"""You are writing a casual, authentic Instagram caption for a thrift find. Keep it 2-4 sentences.

The new item: {new_item.get('title', 'thrifted find')} — ${new_item.get('price', 0.0):.2f} from {new_item.get('platform', 'thrift')}
Outfit suggestion: {outfit}

Write a caption that:
- Feels like a real OOTD post, not a product description
- Mentions the item name, price, and platform once each, naturally
- Captures the specific outfit vibe
- Is casual and fun

Caption:"""

    client = _get_groq_client()
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.9,
        max_tokens=150,
    )
    caption = response.choices[0].message.content.strip().removeprefix("Caption:").strip()
    print(f"[create_fit_card] Fit card created ({len(caption)} chars)")
    return caption
