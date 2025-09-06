#!/usr/bin/env python3
"""
highlights_to_json.py

CSV の `highlights.csv` を読み込み、書名（Book）をキーにしてハイライトを配列にまとめ、
`highlights.json` に書き出します。

出力フォーマット例:
{
  "本の題名": [
    {"location": "123", "section": "章名", "highlight": "…", "note": "…"},
    ...
  ],
  ...
}

このスクリプトは日本語を含む UTF-8 を想定しています。
"""

import csv
import json
from collections import defaultdict
from pathlib import Path


CSV_PATH = Path(__file__).parent.parent / '_out' / 'highlights.csv'
JSON_PATH = Path(__file__).parent.parent / '_out' / 'highlights.json'


def normalize_cell(s):
    if s is None:
        return ''
    return s.strip()


def csv_to_grouped_json(csv_path: Path):
    grouped = defaultdict(list)

    # open with utf-8-sig to tolerate BOM
    with csv_path.open('r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            book = normalize_cell(row.get('Book'))
            if not book:
                # skip rows without a book title
                continue

            highlight = normalize_cell(row.get('Highlight'))
            note = normalize_cell(row.get('Note'))
            section = normalize_cell(row.get('Section'))
            location = normalize_cell(row.get('Location'))

            # use highlight text if present, otherwise fallback to note
            content = highlight or note
            if not content:
                # nothing useful to store
                continue

            # minimal item: only 'h' (highlight text)
            item = {'h': content}
            grouped[book].append(item)

    return grouped


def main():
    if not CSV_PATH.exists():
        print(f"CSV file not found: {CSV_PATH}")
        return 2

    grouped = csv_to_grouped_json(CSV_PATH)

    # Optionally sort books by title
    out = {book: grouped[book] for book in sorted(grouped.keys())}

    # write minified JSON (compact) with ensure_ascii=False for Japanese
    with JSON_PATH.open('w', encoding='utf-8') as j:
        json.dump(out, j, ensure_ascii=False, separators=(',',':'))

    print(f'Wrote {len(out)} books to {JSON_PATH}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
