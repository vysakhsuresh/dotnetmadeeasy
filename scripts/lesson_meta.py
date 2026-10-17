#!/usr/bin/env python3
"""Compute reading time for every lesson -> lesson-meta.json (repo root).

The course player fetches lesson-meta.json to show "N min read" on each
lesson and "time left" per part and tier; build.py reads it for the
contents page. Re-run after editing lessons:

    python3 scripts/lesson_meta.py

Estimate: prose at 210 words/min, code at 70 words/min (read ~3x slower),
plus 45 seconds per quiz question. Minimum 3 minutes.
"""
import json, re, html, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
course = json.load(open(os.path.join(ROOT, 'src', 'course.json'), encoding='utf-8'))

def strip(s):
    s = re.sub(r'<script.*?</script>|<style.*?</style>|<!--.*?-->', '', s, flags=re.S)
    return re.sub(r'<header class="standalone-site-header".*?</header>|<div class="standalone-lesson-header".*?\n</div>|<nav class="standalone-lesson-nav".*?</nav>|<footer class="standalone-site-footer".*?</footer>', '', s, flags=re.S)

meta = {}
for b in course['books']:
    for p in b['parts']:
        for l in p['lessons']:
            raw = open(os.path.join(ROOT, l['href'].lstrip('/')), encoding='utf-8').read()
            body = strip(raw.split('<body>', 1)[1] if '<body>' in raw else raw)
            code = re.findall(r'<pre.*?</pre>', body, flags=re.S)
            code_words = sum(len(html.unescape(re.sub(r'<[^>]+>', ' ', c)).split()) for c in code)
            prose_words = len(html.unescape(re.sub(r'<[^>]+>', ' ', re.sub(r'<pre.*?</pre>', ' ', body, flags=re.S))).split())
            quiz = len(re.findall(r'class="quiz-question"', body))
            minutes = max(3, int(round(prose_words / 210 + code_words / 70 + quiz * 0.75)))
            meta[l['id']] = {'minutes': minutes, 'words': prose_words, 'quiz': quiz}

json.dump(meta, open(os.path.join(ROOT, 'lesson-meta.json'), 'w', encoding='utf-8'), separators=(',', ':'))
total = sum(m['minutes'] for m in meta.values())
print(f'lesson-meta.json: {len(meta)} lessons, {total} minutes (~{total/60:.0f} h)')
