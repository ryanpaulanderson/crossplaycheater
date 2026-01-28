# Crossplay Cheater

Scrabble board analyzer using computer vision.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
# Analyze a board screenshot
python -m crossplaycheater screenshot.png

# JSON output
python -m crossplaycheater screenshot.png -o json

# Verbose logging
python -m crossplaycheater screenshot.png -v
```
