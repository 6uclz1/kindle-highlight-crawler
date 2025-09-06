#!/usr/bin/env python3
"""Simple profiler for highlights.csv

Outputs a human-readable report to stdout and writes
 - reports/highlights_profile.txt
 - reports/book_counts.csv
"""
import csv
import os
from collections import Counter, defaultdict
import math
import re

ROOT = os.path.dirname(os.path.dirname(__file__))
CSV_PATH = os.path.join(ROOT, '_out', 'highlights.csv')
OUT_DIR = os.path.join(ROOT, '_out', 'reports')
os.makedirs(OUT_DIR, exist_ok=True)

def tokenize_jp_en(text):
    if not text:
        return []
    # capture Japanese chars (kanji/hiragana/katakana) and latin words/numbers
    tokens = re.findall(r'[\u4E00-\u9FFF\u3040-\u309F\u30A0-\u30FF0-9A-Za-z]+', text)
    # filter short tokens
    return [t for t in tokens if len(t) >= 2]

def stats(lengths):
    if not lengths:
        return {}
    n = len(lengths)
    s = sum(lengths)
    mean = s / n
    lengths_sorted = sorted(lengths)
    p50 = lengths_sorted[n//2]
    p90 = lengths_sorted[int(n*0.9)-1 if n*0.9>=1 else -1]
    return {'count': n, 'sum': s, 'mean': mean, 'min': lengths_sorted[0], 'p50': p50, 'p90': p90, 'max': lengths_sorted[-1]}

def main():
    rows = []
    with open(CSV_PATH, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        # normalize fieldnames to remove BOM and surrounding whitespace
        if reader.fieldnames:
            norm = [fn.replace('\ufeff', '').strip() for fn in reader.fieldnames]
            reader.fieldnames = norm
        for r in reader:
            # also normalize keys in each row dict
            nr = { (k.replace('\ufeff','').strip() if k is not None else k): v for k,v in r.items() }
            rows.append(nr)

    total_rows = len(rows)
    columns = reader.fieldnames or []

    # missing counts
    missing = Counter()
    for r in rows:
        for c in columns:
            if r.get(c, '') is None or r.get(c, '').strip() == '':
                missing[c] += 1

    # per-book aggregation
    book_counts = Counter()
    book_notes = defaultdict(list)
    for r in rows:
        book = (r.get('Book') or '').strip()
        highlight = (r.get('Highlight') or '').strip()
        note = (r.get('Note') or '').strip()
        # consider a row a highlight if Highlight or Note non-empty
        if highlight or note:
            book_counts[book] += 1
            if highlight:
                book_notes[book].append(highlight)
            elif note:
                book_notes[book].append(note)

    unique_books = len([b for b in book_counts if b])

    # duplicates
    seen = Counter()
    dup_count = 0
    for r in rows:
        book = (r.get('Book') or '').strip()
        highlight = (r.get('Highlight') or '').strip()
        note = (r.get('Note') or '').strip()
        key = (book, highlight)
        seen[key] += 1
    duplicates = {k:v for k,v in seen.items() if k[0] and k[1] and v > 1}

    # highlight lengths
    lengths = []
    text_samples = []
    for r in rows:
        text = (r.get('Highlight') or '').strip()
        if not text:
            text = (r.get('Note') or '').strip()
        if text:
            l = len(text)
            lengths.append(l)
            if len(text_samples) < 10:
                text_samples.append((l, text[:200].replace('\n', ' ')))

    length_stats = stats(lengths)

    # frequent tokens
    token_counter = Counter()
    for r in rows:
        text = (r.get('Highlight') or '').strip()
        if not text:
            text = (r.get('Note') or '').strip()
        if text:
            for t in tokenize_jp_en(text):
                token_counter[t] += 1

    top_tokens = token_counter.most_common(40)

    # write outputs
    report_path = os.path.join(OUT_DIR, 'highlights_profile.txt')
    with open(report_path, 'w', encoding='utf-8') as out:
        w = lambda *a, **k: out.write(' '.join(map(str,a)) + (k.get('end','\n')))
        w('highlights.csv profile')
        w('total_rows:', total_rows)
        w('columns:', ', '.join(columns))
        w('missing per column:')
        for c in columns:
            w(f'  {c}: {missing[c]}')
        w('unique books with highlights:', unique_books)
        w('top 15 books by highlight count:')
        for book, cnt in book_counts.most_common(15):
            w(f'  {cnt:5d}  {book[:80]}')
        w('duplicate highlights (book, highlight) count >1 :', len(duplicates))
        if duplicates:
            for (book, hl), cnt in list(duplicates.items())[:20]:
                w(f'  {cnt:3d}x  {book[:60]}  /  {hl[:120]}')
        w('highlight length stats (chars):')
        for k,v in (length_stats or {}).items():
            w(f'  {k}: {v}')
        w('sample highlights (len, prefix):')
        for l, s in text_samples:
            w(f'  {l:4d}  {s}')
        w('top tokens (token, count):')
        for t,cnt in top_tokens[:40]:
            w(f'  {cnt:5d}  {t}')

    # per-book CSV
    book_csv = os.path.join(OUT_DIR, 'book_counts.csv')
    with open(book_csv, 'w', encoding='utf-8', newline='') as bf:
        writer = csv.writer(bf)
        writer.writerow(['book','highlight_count'])
        for book, cnt in book_counts.most_common():
            writer.writerow([book, cnt])

    # also print brief summary to stdout
    print('report written to', report_path)
    print('book counts written to', book_csv)

if __name__ == '__main__':
    main()
