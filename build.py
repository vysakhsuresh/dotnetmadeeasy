#!/usr/bin/env python3
"""Build the static pages of dotnetmadeeasy.com.

    python3 build.py

Sources:
  src/pages/<name>.html   page body, starting with a JSON meta comment:
                          <!-- meta {"title": "...", "description": "...",
                                     "path": "/name.html", "nav": "start-here",
                                     "robots": "index, follow", "jsonld": {...}} -->
  src/partials/*.html     shared header and footer
  src/course.json         books -> parts -> lessons (drives lessons.html and
                          the {{LESSON_COUNT}} placeholder)
  assets/site.css         shared styles (linked, not inlined)

Outputs are written to the repository root and committed, because GitHub
Pages serves the repository as-is. The course player (index.html) and the
lesson files under Content/ are not built by this script.
"""
import json, os, re, html, datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = 'https://dotnetmadeeasy.com'
ADSENSE = '<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-6072772587431629" crossorigin="anonymous"></script>'
FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com" /><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin /><link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Fira+Code:wght@400;500&display=swap" rel="stylesheet" />'

course = json.load(open(os.path.join(ROOT, 'src', 'course.json'), encoding='utf-8'))
LESSON_COUNT = sum(len(p['lessons']) for b in course['books'] for p in b['parts'])
YEAR = str(datetime.date.today().year)

def read(p): return open(os.path.join(ROOT, p), encoding='utf-8').read()
def esc(t): return html.escape(t, quote=True)

def fill(s):
    return s.replace('{{LESSON_COUNT}}', str(LESSON_COUNT)).replace('{{YEAR}}', YEAR)

HEADER = fill(read('src/partials/header.html'))
FOOTER = fill(read('src/partials/footer.html'))

def header_for(nav):
    if not nav: return HEADER
    return HEADER.replace(f'data-nav="{nav}"', f'data-nav="{nav}" aria-current="page"')

def head(meta):
    url = SITE + meta['path']
    title = meta['title']
    desc = meta['description']
    robots = meta.get('robots', 'index, follow')
    h = [
        '<!DOCTYPE html>', '<html lang="en">', '<head>',
        '    <meta charset="UTF-8" />',
        '    <meta name="viewport" content="width=device-width, initial-scale=1.0" />',
        f'    <title>{esc(title)}</title>',
        f'    <meta name="description" content="{esc(desc)}" />',
        f'    <link rel="canonical" href="{url}" />',
        f'    <meta name="robots" content="{robots}" />',
        '    <meta name="theme-color" content="#0A0C10" />',
        '    <link rel="icon" type="image/svg+xml" href="/favicon.svg" />',
        '    <link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png" />',
        '    <link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png" />',
        '    <link rel="apple-touch-icon" href="/apple-touch-icon.png" />',
        '    <link rel="manifest" href="/manifest.json" />',
        '    <meta property="og:type" content="website" />',
        '    <meta property="og:site_name" content=".NET Made Easy" />',
        f'    <meta property="og:title" content="{esc(meta.get("og_title", title))}" />',
        f'    <meta property="og:description" content="{esc(desc)}" />',
        f'    <meta property="og:url" content="{url}" />',
        f'    <meta property="og:image" content="{SITE}/og-image.png" />',
        '    <meta name="twitter:card" content="summary_large_image" />',
        f'    <meta name="twitter:title" content="{esc(meta.get("og_title", title))}" />',
        f'    <meta name="twitter:description" content="{esc(desc)}" />',
        f'    <meta name="twitter:image" content="{SITE}/og-image.png" />',
        '    ' + FONTS,
        '    <link rel="stylesheet" href="/assets/site.css" />',
        '    ' + ADSENSE,
    ]
    if meta.get('jsonld'):
        h.append('    <script type="application/ld+json">' + json.dumps(meta['jsonld'], ensure_ascii=False).replace('</', '<\\/') + '</script>')
    if meta.get('head_extra'):
        h.append('    ' + meta['head_extra'])
    h += ['</head>', '<body>']
    return '\n'.join(h) + '\n'

def build_page(src_name):
    src = read(os.path.join('src', 'pages', src_name))
    m = re.match(r'\s*<!--\s*meta\s*(\{.*?\})\s*-->\s*', src, re.S)
    if not m:
        raise SystemExit(f'{src_name}: missing meta comment')
    meta = json.loads(m.group(1))
    body = fill(src[m.end():])
    out = head(meta) + header_for(meta.get('nav')) + body.rstrip() + '\n' + FOOTER + '</body>\n</html>\n'
    dest = os.path.join(ROOT, meta['path'].lstrip('/'))
    open(dest, 'w', encoding='utf-8').write(out)
    return meta['path']

def build_lessons_index():
    BLURB = {
        'C# Foundations': 'Start here if you have never written C#. Syntax, types, control flow, and object-oriented programming, built up one concept at a time with nothing assumed.',
        'C# In Practice': 'The idioms a working .NET developer uses every day: generics, collections, LINQ, async and await, dependency injection, data access, and testing.',
        'Production .NET': 'How .NET behaves under real load: language internals, memory and performance, architecture, distributed systems, cloud deployment, security, observability, and production debugging, closing with a full capstone build.',
    }
    ANCHOR = {'foundations': 'foundations', 'intermediate': 'intermediate', 'advanced': 'advanced'}
    parts_total = sum(len(b['parts']) for b in course['books'])
    sec = []
    for b in course['books']:
        count = sum(len(p['lessons']) for p in b['parts'])
        anchor = ANCHOR.get(b['id'], b['id'])
        s = [f'<section class="book" id="{anchor}">', f'    <h2>{esc(b["title"])}</h2>',
             f'    <p class="lede" style="margin-bottom:6px">{esc(BLURB.get(b["title"], ""))}</p>',
             f'    <p class="small muted" style="text-transform:uppercase;letter-spacing:.5px;font-weight:600">{count} lessons &middot; {len(b["parts"])} parts</p>']
        for p in b['parts']:
            s.append(f'    <h3 id="{esc(p["id"])}">{esc(p["title"])}</h3>')
            s.append('    <ol class="lesson-list">')
            for l in p['lessons']:
                s.append(f'        <li><a href="{esc(l["href"])}">{esc(l["title"])}</a></li>')
            s.append('    </ol>')
        s.append('</section>')
        sec.append('\n'.join(s))
    jsonld = {"@context": "https://schema.org", "@type": "Course",
              "name": ".NET Made Easy — Free C# and .NET Course",
              "description": f"A free, written C# and .NET course: {LESSON_COUNT} lessons across three tiers, from your first line of code through production systems.",
              "url": SITE + "/lessons.html", "isAccessibleForFree": True, "inLanguage": "en",
              "provider": {"@type": "Organization", "name": "Layerbit", "url": "https://layerbit.co.in/"},
              "hasCourseInstance": {"@type": "CourseInstance", "courseMode": "online", "courseWorkload": "PT150H"},
              "numberOfCredits": 0, "educationalLevel": "Beginner to Advanced",
              "teaches": [b['title'] for b in course['books']],
              "hasPart": [{"@type": "Course", "name": b['title'], "url": f"{SITE}/lessons.html#{ANCHOR.get(b['id'], b['id'])}"} for b in course['books']]}
    meta = {'title': f'Full Course Contents — All {LESSON_COUNT} C# and .NET Lessons | .NET Made Easy',
            'og_title': f'Full Course Contents — All {LESSON_COUNT} Lessons',
            'description': f'The complete syllabus for the free .NET Made Easy course: all {LESSON_COUNT} C# and .NET lessons across three tiers, from your first line of code through production systems.',
            'path': '/lessons.html', 'nav': 'lessons', 'jsonld': jsonld}
    body = f'''<main class="page">
    <span class="eyebrow">Syllabus</span>
    <h1>Full Course Contents</h1>
    <p class="lede">Every lesson in the free .NET Made Easy course, in order. Each one is a complete, self-contained written lesson &mdash; open any of them directly, or use the <a href="/">interactive course player</a> to track your progress as you go.</p>
    <p>The course runs in three tiers. If you are new to C#, start at the top of Foundations and work down &mdash; or read the <a href="/start-here.html">Start Here guide</a> for a week-by-week plan. If you already write C# professionally, skip to Production .NET.</p>
    <div class="stat-row">
        <div class="stat"><div class="num">{LESSON_COUNT}</div><div class="label">Lessons</div></div>
        <div class="stat"><div class="num">{len(course["books"])}</div><div class="label">Tiers</div></div>
        <div class="stat"><div class="num">{parts_total}</div><div class="label">Parts</div></div>
        <div class="stat"><div class="num">Free</div><div class="label">No signup</div></div>
    </div>
    <div class="toc"><div class="toc-title">Jump to a tier</div><ol>
        <li><a href="#foundations">C# Foundations</a></li>
        <li><a href="#intermediate">C# In Practice</a></li>
        <li><a href="#advanced">Production .NET</a></li>
    </ol></div>
{chr(10).join(sec)}
</main>
'''
    out = head(meta) + header_for('lessons') + body + FOOTER + '</body>\n</html>\n'
    open(os.path.join(ROOT, 'lessons.html'), 'w', encoding='utf-8').write(out)
    return '/lessons.html'

if __name__ == '__main__':
    built = [build_lessons_index()]
    for f in sorted(os.listdir(os.path.join(ROOT, 'src', 'pages'))):
        if f.endswith('.html'):
            built.append(build_page(f))
    print('built:', ', '.join(built))
