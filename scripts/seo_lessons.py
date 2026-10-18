#!/usr/bin/env python3
"""Apply search metadata, structured data and internal links to every lesson.

    python3 scripts/seo_lessons.py

Run it after editing a lesson, after changing src/lesson-seo.json, or after
re-running scripts/lesson_meta.py. It is idempotent: running it twice
produces the same files.

Inputs
  src/course.json         order, short titles, tiers and parts
  src/lesson-seo.json     per lesson: search title (also the page <h1>) and
                          meta description
  lesson-meta.json        reading time and word count per lesson
  related-lessons.json    cross-references between lessons, by lesson number
  src/lesson-dates.json   published / last-updated dates (maintained here)

What it rewrites in each Content/*.html file
  - the <head> metadata: title, description, canonical, Open Graph,
    Twitter card, article dates, fonts, ad script
  - the Article + BreadcrumbList JSON-LD block
  - the standalone header: breadcrumb links, <h1>, "Updated" date
  - the prev/next link labels
  - a "Keep learning" block of related lessons (standalone view only; the
    course player strips it like the other standalone-* blocks)

Dates: a lesson's "published" date is the first commit that added it. Its
"updated" date changes only when the lesson's own content changes (a hash
of the body is stored in src/lesson-dates.json), so re-running this script
or editing metadata never makes a lesson look freshly updated.
"""
import datetime
import hashlib
import html
import json
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://dotnetmadeeasy.com'
BRAND = '.NET Made Easy'
OG_IMAGE = SITE + '/og-image.png'
ADSENSE = '<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-6072772587431629" crossorigin="anonymous"></script>'
FONT_CSS = 'https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Fira+Code:wght@400;500&display=swap'
TIER_ANCHOR = {'foundations': 'foundations', 'intermediate': 'intermediate', 'advanced': 'advanced'}

RELATED_CSS = ('/* related */.standalone-related{margin:48px 0 0;padding:20px 22px 12px;border:1px solid #232838;'
               'border-radius:14px;background:#12151C}body .standalone-related h2{font-size:1.05rem!important;'
               'margin:0 0 6px!important;padding:0!important;border:0!important;letter-spacing:0}'
               '.standalone-related ul{list-style:none;margin:0;padding:0}.standalone-related li{display:flex;'
               'justify-content:space-between;align-items:baseline;gap:14px;padding:9px 0;margin:0;'
               'border-top:1px solid #1C2130}.standalone-related li:first-child{border-top:0}'
               '.standalone-related li span{color:#94A3B8;font-size:13px;white-space:nowrap;flex-shrink:0}')


def path(*p):
    return os.path.join(ROOT, *p)


def load(p):
    return json.load(open(path(p), encoding='utf-8'))


def esc(t):
    return html.escape(t, quote=True)


def git(*args):
    return subprocess.run(['git', '-C', ROOT, *args], capture_output=True, text=True).stdout.strip()


def full_title(seo_title):
    # Google shows the site name separately and truncates around 60
    # characters, so the brand suffix is added only where it still fits.
    t = f'{seo_title} | {BRAND}'
    return t if len(t) <= 66 else seo_title


def human_date(iso):
    d = datetime.datetime.fromisoformat(iso).date()
    return d.isoformat(), f'{d.day} {d.strftime("%b %Y")}'


def content_hash(body):
    s = re.sub(r'<header class="standalone-site-header".*?</header>', '', body, flags=re.S)
    s = re.sub(r'<div class="standalone-lesson-header">.*?\n</div>', '', s, flags=re.S)
    s = re.sub(r'<aside class="standalone-related".*?</aside>', '', s, flags=re.S)
    s = re.sub(r'<nav class="standalone-lesson-nav".*?</nav>|<footer class="standalone-site-footer".*?</footer>', '', s, flags=re.S)
    return hashlib.sha1(re.sub(r'\s+', ' ', s).strip().encode('utf-8')).hexdigest()[:16]


def main():
    course = load('src/course.json')
    seo = load('src/lesson-seo.json')
    meta = load('lesson-meta.json')
    related = load('related-lessons.json')
    dates_path = path('src', 'lesson-dates.json')
    dates = json.load(open(dates_path, encoding='utf-8')) if os.path.exists(dates_path) else {}
    now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()

    flat = []
    for b in course['books']:
        for p in b['parts']:
            for l in p['lessons']:
                flat.append((b, p, l))
    total = len(flat)
    by_num = {os.path.basename(l['href'])[:3]: l for _, _, l in flat}
    by_href = {l['href']: l for _, _, l in flat}

    changed = 0
    for i, (book, part, l) in enumerate(flat):
        lid, href = l['id'], l['href']
        fpath = path(href.lstrip('/'))
        src = open(fpath, encoding='utf-8').read()
        out = src
        s = seo[lid]
        url = SITE + href
        title, desc = s['title'], s['description']
        tier = book['title']

        # ---- dates -------------------------------------------------------
        body = out.split('<body>', 1)[1]
        h = content_hash(body)
        rec = dates.get(lid)
        if not rec:
            first = git('log', '--follow', '--reverse', '--format=%cI', '--', href.lstrip('/')).splitlines()
            last = git('log', '-1', '--format=%cI', '--', href.lstrip('/'))
            rec = {'published': first[0] if first else now, 'modified': last or now, 'hash': h}
        elif rec['hash'] != h:
            rec = {'published': rec['published'], 'modified': now, 'hash': h}
        dates[lid] = rec
        pub_iso, mod_iso = rec['published'], rec['modified']
        mod_day, mod_human = human_date(mod_iso)

        # ---- <head> metadata ---------------------------------------------
        head = '\n'.join([
            f'  <title>{esc(full_title(title))}</title>',
            f'  <meta name="description" content="{esc(desc)}" />',
            f'  <link rel="canonical" href="{url}" />',
            '  <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1" />',
            '  <meta name="author" content="Layerbit" />',
            '  <meta name="theme-color" content="#0A0C10" />',
            '  <link rel="icon" type="image/svg+xml" href="/favicon.svg" />',
            '  <link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png" />',
            '  <link rel="apple-touch-icon" href="/apple-touch-icon.png" />',
            '  <link rel="manifest" href="/manifest.json" />',
            f'  <link rel="alternate" type="application/atom+xml" title="{BRAND}: new and updated lessons" href="/feed.xml" />',
            '  <meta property="og:type" content="article" />',
            f'  <meta property="og:site_name" content="{BRAND}" />',
            '  <meta property="og:locale" content="en_US" />',
            f'  <meta property="og:title" content="{esc(title)}" />',
            f'  <meta property="og:description" content="{esc(desc)}" />',
            f'  <meta property="og:url" content="{url}" />',
            f'  <meta property="og:image" content="{OG_IMAGE}" />',
            '  <meta property="og:image:width" content="1200" />',
            '  <meta property="og:image:height" content="630" />',
            f'  <meta property="og:image:alt" content="{BRAND}: a free C# and .NET course" />',
            f'  <meta property="article:published_time" content="{pub_iso}" />',
            f'  <meta property="article:modified_time" content="{mod_iso}" />',
            f'  <meta property="article:section" content="{esc(tier)}" />',
            '  <meta name="twitter:card" content="summary_large_image" />',
            f'  <meta name="twitter:title" content="{esc(title)}" />',
            f'  <meta name="twitter:description" content="{esc(desc)}" />',
            f'  <meta name="twitter:image" content="{OG_IMAGE}" />',
            '  <link rel="preconnect" href="https://fonts.googleapis.com" />',
            '  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />',
            f'  <link rel="stylesheet" href="{FONT_CSS}" />',
            '  ' + ADSENSE,
        ])
        out, n = re.subn(r'  <title>.*?(?=\n\s*<style id="standalone-page-reset">)', lambda m: head, out, count=1, flags=re.S)
        assert n == 1, f'{href}: head block not found'

        # Fonts now load through <link> above; @import inside <style> blocks
        # rendering until the stylesheet arrives.
        out = re.sub(r"@import url\('https://fonts\.googleapis\.com/[^']*'\);\n?", '', out)
        if '/* related */' not in out:
            out = out.replace('\n</style>', '\n' + RELATED_CSS + '\n</style>', 1)

        # ---- JSON-LD ------------------------------------------------------
        m = re.search(r'<script type="application/ld\+json">(.*?)</script>', out, re.S)
        ld = json.loads(m.group(1).replace('<\\/', '</'))
        art = next(n for n in ld['@graph'] if n.get('@type') == 'Article')
        art.update({
            'headline': title,
            'description': desc,
            'image': {'@type': 'ImageObject', 'url': OG_IMAGE, 'width': 1200, 'height': 630},
            'datePublished': pub_iso,
            'dateModified': mod_iso,
            'timeRequired': f"PT{meta[lid]['minutes']}M",
            'wordCount': meta[lid]['words'],
            'learningResourceType': 'Lesson',
            'author': {'@type': 'Organization', 'name': 'Layerbit', 'url': SITE + '/about.html', 'sameAs': 'https://layerbit.co.in/'},
            'position': i + 1,
        })
        crumb = next(n for n in ld['@graph'] if n.get('@type') == 'BreadcrumbList')
        crumb['itemListElement'][-1]['name'] = l['title']
        ld_text = json.dumps(ld, ensure_ascii=False).replace('</', '<\\/')
        out = out[:m.start(1)] + ld_text + out[m.end(1):]

        # ---- visible standalone header -------------------------------------
        anchor = TIER_ANCHOR.get(book['id'], book['id'])
        crumb_html = (f'<nav class="ss-crumb" aria-label="Breadcrumb"><a href="/">Home</a><span class="sep">&rsaquo;</span>'
                      f'<a href="/lessons.html">All Lessons</a><span class="sep">&rsaquo;</span>'
                      f'<a href="/lessons.html#{anchor}">{esc(tier)}</a><span class="sep">&rsaquo;</span>'
                      f'<a href="/lessons.html#{esc(part["id"])}">{esc(part["title"])}</a></nav>')
        out, n = re.subn(r'<nav class="ss-crumb".*?</nav>', lambda m: crumb_html, out, count=1, flags=re.S)
        assert n == 1, f'{href}: breadcrumb not found'
        out, n = re.subn(r'<h1 class="ss-title">.*?</h1>', lambda m: f'<h1 class="ss-title">{esc(title)}</h1>', out, count=1, flags=re.S)
        assert n == 1, f'{href}: h1 not found'
        out, n = re.subn(r'<span>\d+ min read</span>', f"<span>{meta[lid]['minutes']} min read</span>", out, count=1)
        assert n == 1, f'{href}: reading time not found'
        updated = f'<span>Updated <time datetime="{mod_day}">{mod_human}</time></span>'
        out, n = re.subn(r'<span>(?:Free written lesson|Updated <time[^>]*>[^<]*</time>)</span>(?=</p>)', lambda m: updated, out, count=1)
        assert n == 1, f'{href}: meta line not found'

        # ---- site navigation: roadmap link ---------------------------------
        if '<a href="/dotnet-developer-roadmap.html">Roadmap</a>' not in out:
            out = out.replace('<a href="/start-here.html">Start Here</a><a href="/interview-prep.html">',
                              '<a href="/start-here.html">Start Here</a><a href="/dotnet-developer-roadmap.html">Roadmap</a><a href="/interview-prep.html">', 1)
        if '<a href="/dotnet-developer-roadmap.html">.NET roadmap</a>' not in out:
            out = re.sub(r'(<div class="ss-footer-links">.*?<a href="/start-here.html">[^<]*</a>)',
                         lambda m: m.group(1) + '<a href="/dotnet-developer-roadmap.html">.NET roadmap</a>', out, count=1, flags=re.S)

        # ---- prev / next labels -------------------------------------------
        def relabel(m):
            target = by_href.get(m.group(1))
            if not target:
                return m.group(0)
            label = esc(target['title'])
            return f'<a href="{m.group(1)}" rel="prev">&larr; {label}</a>' if m.group(2) == 'prev' else f'<a href="{m.group(1)}" rel="next">{label} &rarr;</a>'
        out = re.sub(r'<a href="([^"]+)" rel="(prev|next)">[^<]*</a>', relabel, out)

        # ---- related lessons ------------------------------------------------
        prev_href = flat[i - 1][2]['href'] if i > 0 else None
        next_href = flat[i + 1][2]['href'] if i + 1 < total else None
        skip = {href, prev_href, next_href}
        picks = []
        for num in related.get(os.path.basename(href)[:3], []):
            t = by_num.get(num)
            if t and t['href'] not in skip and t not in picks:
                picks.append(t)
            if len(picks) == 3:
                break
        siblings = part['lessons']
        k = siblings.index(l)
        for t in siblings[k + 2:] + list(reversed(siblings[:max(k - 1, 0)])):
            if len(picks) >= 5:
                break
            if t['href'] not in skip and t not in picks:
                picks.append(t)
        if picks:
            items = '\n'.join(f'    <li><a href="{t["href"]}">{esc(seo[t["id"]]["title"])}</a><span>{meta[t["id"]]["minutes"]} min</span></li>' for t in picks)
            aside = f'<aside class="standalone-related" aria-label="Related lessons">\n  <h2>Keep learning</h2>\n  <ul>\n{items}\n  </ul>\n</aside>\n'
        else:
            aside = ''
        out = re.sub(r'<aside class="standalone-related".*?</aside>\n', '', out, flags=re.S)
        out = out.replace('<nav class="standalone-lesson-nav"', aside + '<nav class="standalone-lesson-nav"', 1)

        if out != src:
            open(fpath, 'w', encoding='utf-8').write(out)
            changed += 1

    ordered = {l['id']: dates[l['id']] for _, _, l in flat}
    open(dates_path, 'w', encoding='utf-8').write(json.dumps(ordered, indent=1) + '\n')
    print(f'seo_lessons: {total} lessons checked, {changed} files updated')


if __name__ == '__main__':
    main()
