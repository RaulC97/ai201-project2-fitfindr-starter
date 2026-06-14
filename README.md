# FitFindr — Starter Kit

This starter kit contains everything you need to begin Project 2.

## What's Included

```
ai201-project2-fitfindr-starter/
├── data/
│   ├── listings.json          # 40 mock secondhand listings
│   └── wardrobe_schema.json   # Wardrobe format + example wardrobe
├── tests/
│   ├── test_tools.py          # pytests
│   └── toolstests.py          # testsing all different secenario prints to screen
├── utils/
│   └── data_loader.py         # Helper functions for loading the data
├── planning.md                # Your planning template — fill this out first
├── tools.py                   # Tools uses by LLM
└── requirements.txt           # Python dependencies
```

## Setup

```bash
pip install -r requirements.txt
```

Set your Groq API key in a `.env` file (get a free key at [console.groq.com](https://console.groq.com)):
```
GROQ_API_KEY=your_key_here
```

## The Mock Listings Dataset

`data/listings.json` contains 40 mock secondhand listings across categories (tops, bottoms, outerwear, shoes, accessories) and styles (vintage, y2k, grunge, cottagecore, streetwear, and more).

Each listing has: `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`.

Load it with:
```python
from utils.data_loader import load_listings
listings = load_listings()
```

## The Wardrobe Schema

`data/wardrobe_schema.json` defines the format your agent uses to represent a user's existing wardrobe. It includes:

- `schema`: field definitions for a wardrobe item
- `example_wardrobe`: a sample wardrobe with 10 items you can use for testing
- `empty_wardrobe`: a starting template for a new user

Load an example wardrobe with:
```python
from utils.data_loader import get_example_wardrobe
wardrobe = get_example_wardrobe()
```

## Where to Start

1. **Read `planning.md` and fill it out before writing any code.**
2. Verify the data loads correctly by running `python utils/data_loader.py`.
3. Build and test each tool individually before connecting them through your planning loop.

Your implementation files go in this same directory. There's no required file structure for your agent code — organize it however makes sense for your design.

## Tool Inventory

### search_listings

**Description**

Searches the listing data to find matching best fitting clothing item based on users input from description, size, and price. If not matching clothing found returns an empty list and stop the program if appropriate message

**Inputs**

- `description` (str): description of the clothing
- `size` (str): size of the product. example: M for medium, XL extra large, W28 for waist 28
- `max_price` (float): Max price of a piece of clothing the search should go up to.

**What it returns**

Returns a list of dictionaries of the best clothing that matches the input, with the best matching at the top. the dictionary format is in the following order: id, title, description, category, style_tags (list), size,
     condition, price (float), colors (list), brand, platform

If no appropriate listing found given input, return an empty list


### suggest_outfit

**Description**

Takes a clothing item and the user wardrobe and LLM creates an outfit suggestions, or way to style the new clothing item if user has no wardrobe. 

**Inputs**

- `new_item` (dict): New clothing item that was recieved from search_listings.data is in format     
                    id, title, description, category, style_tags (list), size,
                    condition, price (float), colors (list), brand, platform
- `wardrobe` (dict): User's wardrobe 

**What it returns**

Returns a string description of what the LLM can create from the new clothing item and wardrobe. It 1-2 sentences long. If the users wardrobe is empty, the LLM gives suggestion on how to style the new clothing item.

### create_fit_card

**Description**

Creates a shor description that could be placed on a social media post about the outfi suggestion and highlights the new clothing item that was given.

**Inputs**
- `outfit` (str): Outfit suggestion, short description about the outfit you can use with new clothing item
- `new_item` (dict): new clothing item that will be highlighting in the return


**What it returns**
Short string description that highlights the new clothing item that fits a social media post. If the suggestion outfit data is incomplete, LLM try descripiting something fun about the new item to post online.

## Planning Loop

Each of the tools are called in this order: search_listings -> sugguest_outfit -> create_fit_card.

The only time an early error can stop the planning loop is when we receive an empty list in the return of search_listings. Here no matching clothing item could be found using users input. At this point, the interface will suggust to broaden the search.

When successful clothing items list are returned, the best matching clothing is then used along with wardrobe to sugguest an outfit. If the user doesnt have a wardrobe, LLM suggest a way to style the new clothing item.

Finally once a suggestion is written, create_fit_card gets both the suggestion, and new clothing item to create a fun social media post caption. If there is not suggestion or its incomplete, the LLM create a fun post about the new clothing item.

## State Management

- Search Listing: Stores the best matching clothing items that best fit the user input, sorted best to worse. Best matching clothing item is passed along
- Suggest Outfit: using the best clothing item, and the user's wardrobe, create a outfit suggestion 1-2 sentences long. Best matching clothing item and outfit suggestion is passed along
- Fit Card: Using the outfit suggestion and new clothing item, a caption is create to fit a social media post that highlights the new clothing item.

# Error Handling 

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query | return empty list, and no matching clothing message, exit loop|
| suggest_outfit | Wardrobe is empty | suggest different ways to style new clothing item|
| create_fit_card | Outfit input is missing or incomplete | describe something fun or cool about the new clothing item|

After the implementation of each tool, and different inputs were used, a test was created to make sure changes to the code would not give us different results.

Tests include: No maching clothing item, user has no wardrobe, no suggestion was made, etc

Example of testing result same new clothing item with and without wardrobe from user:

```
==================================================
  TEST: suggest_outfit — with example wardrobe
==================================================
[suggest_outfit] Generating outfit suggestion for: 'Y2K Baby Tee — Butterfly Print'
[suggest_outfit] Wardrobe has 10 items — finding outfit combinations
[suggest_outfit] Suggestion generated (381 chars)

Suggestion:
  Pair the Y2K Baby Tee with the Baggy straight-leg jeans and Chunky white sneakers for a fun, nostalgic look, or layer it under the Vintage black denim jacket and pair with the Wide-leg khaki trousers and Black combat boots for a chic, eclectic vibe. The Y2K Baby Tee also looks great with the Brown leather belt and Black crossbody bag added to either outfit for a pop of contrast.

PASSED

==================================================
  TEST: suggest_outfit — empty wardrobe
==================================================
[suggest_outfit] Generating outfit suggestion for: 'Y2K Baby Tee — Butterfly Print'
[suggest_outfit] Wardrobe is empty — will give general styling advice
[suggest_outfit] Suggestion generated (367 chars)

Suggestion:
  This adorable Y2K baby tee is perfect for creating a sweet, nostalgic look - pair it with high-waisted jeans or a flowy skirt for a vintage-inspired vibe that's totally on-trend with the cottagecore aesthetic. To really make the butterfly graphic pop, try layering it under a cardigan or denim jacket for a casual, everyday look that's equal parts cute and laid-back.

PASSED
```

## Spec Reflection

The planning.md and functions docstrings were reall helpful for understand was was nessacry and how my return structure was suppose to look like. In the rung_agent function
there were multiple ways that we could parse the users input. For my implmentation I chose Groq LLM to extract the descriptino size, and max price.

## AI usage

When implementing the parse_query function i was going to use regex approach to try to be faster than Groq LLM approach due to the speed it would take but ran into some issues where it was giving the following issues:

1. No findings when there should be.
2. Bad matching findings given user description.


As a way to resolve the not finding approriate clothing, I switched the implementation from regex to Groq LLM to extrat the description, size and price. Although the time was a bit longer, than using regex, provided with more acurate results

For bad matching I input "big hat" and the best result was a t-shirt. From this I implemented a scoring system instead of just pure how many similar the input is.

