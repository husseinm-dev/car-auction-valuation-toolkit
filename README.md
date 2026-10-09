# 🚗 Car Auction Valuation Toolkit

Bidding on cars at auction means answering one question fast, for dozens of cars at once: **what is this car actually worth?**

This toolkit automates that. Feed it your auction **watchlist as an Excel file** (VIN, trim, odometer) and it drives a real browser through the major valuation sources — **Edmunds** and **Manheim MMR** — then writes the values back into your spreadsheet, so you walk into the auction knowing your max bid for every lane.

## The tools

| Tool | Source | Mode | What it does |
|---|---|---|---|
| [`car_values/`](car_values) | Edmunds appraisal | Batch (Excel) | Walks the full appraisal wizard per VIN — fuzzy-matches the trim, fills colors/mileage/condition — and extracts the Private Party value |
| [`mmr_search/`](mmr_search) | Manheim MMR | Batch (Excel) | After you log in manually, fills **MMR**, **MMR LOW**, and retail values for every VIN on your list |
| [`manually_search_car_values/`](manually_search_car_values) | Edmunds | Single VIN — CLI or Flask web UI | Quick one-off lookup: run from the terminal or spin up a tiny web form |
| [`carfax_search/`](carfax_search) | Carfax | Batch (Excel) | ⚠️ Works, but Carfax aggressively blocks automation — kept for reference, not recommended |

### Highlights

- **Fuzzy trim matching** — auction sheets say `1.8T LIMITED EDITION`, Edmunds says something slightly different. A `SequenceMatcher`-based matcher picks the right dropdown option (exact substring → best similarity ratio).
- **Fast scraping** — images, stylesheets, and plugins are blocked at the Chrome preferences level, so batch runs don't waste time rendering.
- **Resilient waits** — explicit `WebDriverWait` conditions on every step instead of fixed sleeps.
- **Respectful of logins** — Manheim and Carfax flows pause for you to log in manually in the browser; no credentials are ever stored or automated.
- **Non-destructive output** — results are written to a new `*_updated.xlsx`, never over your original watchlist.

## Setup

**Requirements:** Python 3.10+, Google Chrome

```sh
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
```

**ChromeDriver:** download the version matching your Chrome from the [official site](https://googlechromelabs.github.io/chrome-for-testing/) and place the executable inside each tool's folder as `chromedriver` (binaries are intentionally not committed).

## Watchlist format

Each batch tool reads an Excel file (default `./test-watchlist.xlsx` inside the tool's folder) with these columns:

| Column | Example | Used by |
|---|---|---|
| `VIN` | `1VWAT7A30FC113447` | all |
| `Series` | `1.8T LIMITED EDITION` | Edmunds (trim matching) |
| `Odometer` | `82000` | all |
| `MSRP` / `MMR` / `MMR LOW` | *(filled in by the tools)* | output columns |

Extra columns (lane, run number, notes, …) are preserved untouched.

## Usage

### Edmunds batch (`car_values/`)

```sh
cd car_values
python main.py
```

Processes every row, writes `test-watchlist_updated.xlsx` with Private Party values in the `MSRP` column.

### Manheim MMR batch (`mmr_search/`)

```sh
cd mmr_search
python main.py
```

A browser opens to the MMR login page — **log in manually**, then press Enter in the terminal. The tool fills `MMR`, `MMR LOW`, and retail value for every VIN.

### Single lookup — CLI or web (`manually_search_car_values/`)

```sh
cd manually_search_car_values

# CLI mode
python main.py 1VWAT7A30FC113447 82000 "1.8T LIMITED EDITION"

# Web mode (Flask) — then open the form in your browser
python main.py
```

## Limitations

- **Scrapers are brittle.** Edmunds/Manheim can change their page structure at any time; fix by updating the CSS selectors.
- Edmunds condition questions are auto-answered with the first (most favorable) option — treat the result as a ceiling, not gospel.
- Carfax actively blocks automation; expect the `carfax_search` tool to get rate-limited or captcha'd.

## Disclaimer

Personal/educational automation project. These tools drive a real browser through public-facing valuation forms, but automated access may be subject to each site's Terms of Service — use responsibly and at your own discretion. Not affiliated with Edmunds, Manheim, or Carfax.
