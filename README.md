# Arknights Lore Reader

Arknights Lore Reader is a desktop application for downloading, organizing, translating and reading story content from **Arknights**.

The application reconstructs story chapters from the game scripts, including dialogue, backgrounds, CGs and character portraits, and generates readable story collections as **EPUB** and optionally **HTML**.

It can also download and translate operator information and Operator Records.

> This is an unofficial fan project and is not affiliated with Hypergryph or Yostar.

## Features

### Story reader

- Downloads Arknights story scripts from `arknights.timo.beer`.
- Groups chapters into their corresponding stories and events.
- Supports:
  - Main Story
  - Side Stories
  - Vignettes
  - Integrated Strategies
- Reconstructs scenes from the original AVG scripts.
- Downloads and caches backgrounds and CGs.
- Detects character expressions and subvariants.
- Generates speaker portraits automatically from the original character sprites.
- Tracks `charslot` state so portraits remain correct when a script changes focus without repeating the character ID.

### Translation

Stories can be translated from English to **European Spanish (`es-ES`)** using the OpenAI API.

The translator preserves:

- character names and codenames;
- dialogue structure;
- line order;
- intentional ambiguity;
- pauses and interruptions;
- character-specific speaking style;
- Arknights terminology.

A separate context pass can analyze the complete story before translation to provide useful information about characters, factions, locations and terminology.

Translation results and context are cached locally to avoid unnecessary API calls.

Translation can also be disabled completely with **Solo descargar**, which downloads and builds the original English story.

## Output formats

### EPUB

EPUB is the primary output format and is enabled by default.

Generated EPUBs contain:

- cover;
- table of contents;
- one XHTML document per chapter;
- dialogue;
- speaker portraits;
- backgrounds and CGs;
- embedded images;
- EPUB-specific styling.

All required images are stored inside the EPUB, so the file can be copied to another device without the local `assets` directory.

WebP source images are converted when necessary to formats with broad ebook-reader compatibility.

### HTML

HTML output is optional and can be enabled together with EPUB.

The following combinations are supported:

```text
EPUB only
HTML only
EPUB + HTML
```

At least one output format must always be enabled.

HTML is useful for testing, debugging and reading the generated story directly in a browser.

## Operators

The application can also process operator content.

Current operator support includes:

- operator profiles;
- files;
- modules;
- Operator Records;
- operator portraits;
- story backgrounds and CGs used by Operator Records;
- speaker portraits;
- translation with shared context across related operator content.

Operator output currently uses HTML.

## Character portraits

Story scripts do not provide small dialogue portraits directly, so Arknights Lore Reader generates them from the original AVG character sprites.

The portrait system:

1. loads a neutral character variant;
2. analyzes the alpha channel;
3. detects the upper character mass;
4. estimates the head and shoulder area;
5. calculates a square crop;
6. reuses the same crop for the character's other expressions;
7. generates a circular PNG portrait.

This keeps expressions visually aligned instead of recalculating the crop for every sprite.

Both common character formats and less usual script forms such as:

```text
char_xxx
char_xxx#4
char_xxx#4$2
avg_npc_xxx$1
```

are normalized to their corresponding asset filenames.

## Interface

The application uses **PySide6**.

The main options are divided into two sections.

### Download and translation

- Solo descargar
- Translation model
- Context model
- Regenerate context
- Ignore translation cache

Translation-related controls are disabled while **Solo descargar** is active.

### Output format

- EPUB
- HTML
- Send EPUB to Kindle

EPUB is enabled by default.

The Kindle option is only available when EPUB generation is enabled.

## Requirements

- Python 3.10 or newer
- PySide6
- Requests
- Pillow
- OpenAI Python SDK
- python-dotenv

Install the Python dependencies in a virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1

pip install PySide6 requests Pillow openai python-dotenv
```

## Configuration

Create a `.env` file in the project root.

```dotenv
OPENAI_API_KEY=your_openai_api_key
```

The API key is loaded when the application starts.

The `.env` file must **never be committed to Git**.

The repository includes `.env.example` as a template for configuration that can safely be versioned.

### Kindle server configuration

The project is being integrated with a separate `kindle-manga` server pipeline.

The intended configuration is:

```dotenv
KINDLE_SERVER_HOST=
KINDLE_SERVER_PORT=22
KINDLE_SERVER_USER=
KINDLE_SERVER_INCOMING_DIR=
```

The Lore Reader will only be responsible for delivering the generated EPUB to the server.

The server handles:

- mail size validation;
- EPUB splitting when required;
- SMTP delivery;
- retries;
- delivery state;
- cleanup after successful delivery.

Generated Arknights EPUBs enter that pipeline as already-converted books and do not pass through KCC.

## Running

Activate the virtual environment:

```powershell
.venv\Scripts\Activate.ps1
```

Then run:

```powershell
python main.py
```

The application will load the available story catalog and display the supported categories in the interface.

## Project structure

```text
arknights_lore_reader/
├── api/
│   └── client.py
│
├── app/
│   └── runner.py
│
├── media/
│   ├── background_manager.py
│   ├── character_manager.py
│   └── cover_manager.py
│
├── models/
│   └── category.py
│
├── operators/
│   ├── client.py
│   ├── manager.py
│   ├── portrait_manager.py
│   └── html_generator.py
│
├── story/
│   ├── catalog_resolver.py
│   ├── sanitizer.py
│   ├── html_generator.py
│   ├── compendium_generator.py
│   ├── epub_generator.py
│   ├── styles/
│   └── templates/
│
├── translation/
│   ├── cache_manager.py
│   ├── context_builder.py
│   ├── openai_translator.py
│   └── openai_translator_operator_chain.py
│
├── ui/
│   ├── main_window.py
│   └── worker.py
│
├── assets/
├── output/
├── .env.example
└── main.py
```

## Local data and cache

The application stores downloaded and generated files locally.

Typical generated directories include:

```text
assets/
output/
translation/cache/
translation/context/
```

These directories should normally remain outside version control.

Downloaded character sprites and scene images are cached so they do not need to be downloaded again every time a story is generated.

Translation caches can also be reused unless **Ignorar caché de traducciones** is selected.

## Data source

Story scripts, catalogs and game assets used by the reader are obtained from the Arknights data hosted by **arknights.timo.beer**.

The application does not modify the source scripts. It parses them into an internal scene representation used by the HTML and EPUB generators.

## Current status

The main story pipeline is functional:

```text
Catalog
   ↓
Story scripts
   ↓
Script parser
   ↓
Scene reconstruction
   ↓
Optional OpenAI translation
   ↓
EPUB / HTML
```

Character variants, scene backgrounds, CGs, speaker portraits, translation caching and EPUB generation are implemented.

The optional automatic handoff of generated EPUBs to the Kindle server pipeline is the remaining integration step.
