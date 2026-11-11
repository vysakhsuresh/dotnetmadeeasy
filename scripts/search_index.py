#!/usr/bin/env python3
"""Rebuild search-index.json (word -> lesson numbers) from the lesson files.
    python3 scripts/search_index.py

Text comes from each lesson's <main>, minus the standalone lesson header. Words
are lower-cased, start with a letter, are at least three characters long, and
skip the common words in scripts/search-stopwords.json.
"""
import collections
import html
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN = re.compile(r"[a-z][a-z0-9.'#+]*[a-z0-9#+]")
MAX_LESSONS = 120  # a word found in more lessons than this is too common to help


def lesson_text(path):
    s = open(path, encoding='utf-8').read()
    m = re.search(r'<main[^>]*>(.*?)</main>', s, re.S)
    s = m.group(1) if m else s
    s = re.sub(r'<div class="standalone-lesson-header">.*?</div>\s*', ' ', s, count=1, flags=re.S)
    s = re.sub(r'<(script|style)[^>]*>.*?</\1>', ' ', s, flags=re.S)
    s = re.sub(r'<[^>]+>', ' ', s)
    return html.unescape(s).lower()


def main():
    content = os.path.join(ROOT, 'Content')
    stop = set(json.load(open(os.path.join(ROOT, 'scripts', 'search-stopwords.json'), encoding='utf-8')))
    found = collections.defaultdict(list)
    for name in sorted(os.listdir(content)):
        if re.match(r'\d{3}-.*\.html$', name):
            for word in {t for t in TOKEN.findall(lesson_text(os.path.join(content, name))) if len(t) >= 3}:
                found[word].append(name[:3])
    index = {w: sorted(n) for w, n in sorted(found.items()) if w not in stop and len(n) <= MAX_LESSONS}
    with open(os.path.join(ROOT, 'search-index.json'), 'w', encoding='utf-8') as fh:
        fh.write(json.dumps(index, separators=(',', ':')))
    print(f'search-index.json: {len(index)} words')


if __name__ == '__main__':
    main()
