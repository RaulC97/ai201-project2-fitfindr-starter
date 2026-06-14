"""
agent.py

The FitFindr planning loop. Orchestrates the three tools in response to a
natural language user query, passing state between them via a session dict.

Complete tools.py and test each tool in isolation before implementing this file.

Usage (once implemented):
    from agent import run_agent
    from utils.data_loader import get_example_wardrobe

    result = run_agent(
        query="vintage graphic tee under $30, size M",
        wardrobe=get_example_wardrobe(),
    )
    print(result["fit_card"])
    print(result["error"])   # None on success
"""

import json

from tools import search_listings, suggest_outfit, create_fit_card, _get_groq_client


# ── session state ─────────────────────────────────────────────────────────────

def _new_session(query: str, wardrobe: dict) -> dict:
    """
    Initialize and return a fresh session dict for one user interaction.

    The session dict is the single source of truth for everything that happens
    during a run — it stores the original query, parsed parameters, tool results,
    and any error that caused early termination.

    You may add fields to this dict as needed for your implementation.
    """
    return {
        "query": query,              # original user query
        "parsed": {},                # extracted description / size / max_price
        "search_results": [],        # list of matching listing dicts
        "selected_item": None,       # top result, passed into suggest_outfit
        "wardrobe": wardrobe,        # user's wardrobe dict
        "outfit_suggestion": None,   # string returned by suggest_outfit
        "fit_card": None,            # string returned by create_fit_card
        "error": None,               # set if the interaction ended early
    }


# ── query parser ─────────────────────────────────────────────────────────────

def _parse_query(query: str) -> dict:
    """
    Use the Groq LLM to extract description, size, and max_price from a
    natural language query. Returns a dict with those three keys.
    Falls back to the full query as description if JSON parsing fails.
    """
    print(f"[agent] Parsing query: '{query}'")

    prompt = f"""You are a fashion search assistant. Extract the following from the user's query and return ONLY valid JSON, no explanation:
- "description": the clothing item keywords (e.g. "vintage graphic tee")
- "size": the size if mentioned (e.g. "M", "XL", "W28"), or null if not mentioned
- "max_price": the maximum price as a number if mentioned (e.g. 30.0), or null if not mentioned

User query: "{query}"

Return only a JSON object like: {{"description": "...", "size": "...", "max_price": 30.0}}"""

    try:
        client = _get_groq_client()
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=100,
        )
        raw = response.choices[0].message.content.strip()
        # Strip markdown code fences if the LLM wraps the JSON
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        parsed = json.loads(raw)
    except Exception as e:
        print(f"[agent] WARNING: query parsing failed ({e}) — using full query as description")
        parsed = {"description": query, "size": None, "max_price": None}

    print(f"[agent] Parsed -> description='{parsed.get('description')}', "
          f"size={parsed.get('size')}, max_price={parsed.get('max_price')}")
    return parsed


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Main agent entry point. Runs the FitFindr planning loop for a single
    user interaction and returns the completed session dict.

    Args:
        query:    Natural language user request
                  (e.g., "vintage graphic tee under $30, size M")
        wardrobe: User's wardrobe dict — use get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py

    Returns:
        The session dict after the interaction completes. Check session["error"]
        first — if it is not None, the interaction ended early and the other
        output fields (outfit_suggestion, fit_card) will be None.

    TODO — implement this function using the planning loop you designed in planning.md:

        Step 1: Initialize the session with _new_session().

        Step 2: Parse the user's query to extract a description, size, and
                max_price. You can use regex, string splitting, or ask the LLM
                to parse it — document your choice in planning.md.
                Store the result in session["parsed"].

        Step 3: Call search_listings() with the parsed parameters.
                Store results in session["search_results"].
                If no results: set session["error"] to a helpful message and
                return the session early. Do NOT proceed to suggest_outfit
                with empty input.

        Step 4: Select the item to use (e.g., the top result).
                Store it in session["selected_item"].

        Step 5: Call suggest_outfit() with the selected item and wardrobe.
                Store the result in session["outfit_suggestion"].

        Step 6: Call create_fit_card() with the outfit suggestion and selected item.
                Store the result in session["fit_card"].

        Step 7: Return the session.

    Before writing code, complete the Planning Loop and State Management sections
    of planning.md — your implementation should match what you described there.
    """
    # TODO: implement the planning loop
    # session = _new_session(query, wardrobe)
    # session["error"] = "Planning loop not yet implemented."
    # return session

    print("\n" + "=" * 50)
    print("[agent] Starting FitFindr agent")
    print(f"[agent] Query: '{query}'")
    print("=" * 50 + "\n")

    # Step 1: Initialize session
    session = _new_session(query, wardrobe)

    # Step 2: Parse the natural language query into structured fields
    parsed = _parse_query(query)
    session["parsed"] = parsed

    # Step 3: Search listings — hard stop if nothing found
    print("\n[agent] Step 1/3 — Searching listings...")
    search_results = search_listings(
        description=parsed["description"],
        size=parsed.get("size"),
        max_price=parsed.get("max_price"),
    )
    session["search_results"] = search_results

    if not search_results:
        session["error"] = (
            f"No listings found for '{parsed['description']}'"
            + (f" in size {parsed['size']}" if parsed.get("size") else "")
            + (f" under ${parsed['max_price']:.2f}" if parsed.get("max_price") else "")
            + ". Try broadening your search."
        )
        print(f"[agent] No results found — stopping early.")
        print(f"[agent] Error: {session['error']}")
        return session

    # Step 4: Select the top result
    session["selected_item"] = search_results[0]
    print(f"\n[agent] Selected item: '{session['selected_item']['title']}' "
          f"(${session['selected_item']['price']:.2f}) "
          f"from {session['selected_item']['platform']}")

    # Step 5: Generate outfit suggestion using the item and wardrobe
    print("\n[agent] Step 2/3 — Generating outfit suggestion...")
    session["outfit_suggestion"] = suggest_outfit(
        new_item=session["selected_item"],
        wardrobe=session["wardrobe"],
    )

    # Step 6: Create a social media fit card from the suggestion
    print("\n[agent] Step 3/3 — Creating fit card...")
    session["fit_card"] = create_fit_card(
        outfit=session["outfit_suggestion"],
        new_item=session["selected_item"],
    )

    print("\n[agent] Done! All steps completed successfully.")
    print("=" * 50 + "\n")
    return session


# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

    print("=== Happy path: graphic tee ===\n")
    session = run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    )
    if session["error"]:
        print(f"Error: {session['error']}")
    else:
        print(f"Found: {session['selected_item']['title']}")
        print(f"\nOutfit: {session['outfit_suggestion']}")
        print(f"\nFit card: {session['fit_card']}")

    print("\n\n=== No-results path ===\n")
    session2 = run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )
    print(f"Error message: {session2['error']}")
