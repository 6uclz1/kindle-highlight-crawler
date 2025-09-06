# Gemini Code Assistant Context

This document provides context for the Gemini code assistant to understand the `kindle-highlight-crawler` project.

## Project Overview

This project is a Python-based toolset for scraping Kindle highlights and library information from Amazon Japan. It uses `playwright` for browser automation and includes scripts for data extraction, conversion, and analysis.

### Key Scripts

- `scrape_notebook_highlight_to_csv/`: Scrapes highlights from the Kindle notebook page.
- `scrape_library_booklist_to_csv/`: Scrapes the book list from the Kindle library page.
- `format_highlights_csv_to_json/`: Converts highlights from CSV to JSON format.
- `debug_notebook_dom/`: A debugging tool for inspecting the notebook page's DOM.
- `analyze_highlights_csv_to_report/`: Analyzes the highlights data and generates a report.
- `setup.sh`: A shell script to set up the development environment using `uv`.
- `cli.py`: A command-line interface to run all the scripts.

## Building and Running

### Setup

The project uses `uv` for environment and package management. To set up the development environment, run the `setup.sh` script:

```bash
./setup.sh
```

This will install the dependencies from `pyproject.toml` and the necessary Playwright browser binaries.

### Running Scripts with the CLI

The `cli.py` script provides a command-line interface to run the different tools.

- **Scraping Highlights:**
  ```bash
  uv run python cli.py scrape-highlights --headful --output _out/highlights.csv
  ```

- **Scraping Library:**
  ```bash
  uv run python cli.py scrape-library
  ```

- **Converting to JSON:**
  ```bash
  uv run python cli.py format-json
  ```

- **Analyzing Highlights:**
  ```bash
  uv run python cli.py analyze
  ```

- **Debugging DOM:**
  ```bash
  uv run python cli.py debug-dom
  ```

## Development Conventions

*   **Dependency Management:** The project uses `uv` for managing Python dependencies, as defined in `pyproject.toml` and `uv.lock`.
*   **Code Style:** The Python code is written with type hints and follows standard Python conventions.
*   **Browser Automation:** The core scraping logic is implemented using `playwright`.
*   **Data Storage:**
    *   Output files are stored in the `_out/` directory.
    *   Browser profile data is stored in the `user_data/` directory, which is excluded from version control.
