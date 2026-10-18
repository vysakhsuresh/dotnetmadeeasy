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
FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com" /><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin /><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Fira+Code:wght@400;500&display=swap" media="print" onload="this.media=\'all\'" /><noscript><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Fira+Code:wght@400;500&display=swap" /></noscript>'

course = json.load(open(os.path.join(ROOT, 'src', 'course.json'), encoding='utf-8'))
LESSON_META = json.load(open(os.path.join(ROOT, 'lesson-meta.json'), encoding='utf-8'))
LESSON_COUNT = sum(len(p['lessons']) for b in course['books'] for p in b['parts'])
COURSE_MINUTES = sum(LESSON_META[l['id']]['minutes'] for b in course['books'] for p in b['parts'] for l in p['lessons'])
COURSE_HOURS = int(round(COURSE_MINUTES / 60 / 5.0) * 5)
YEAR = str(datetime.date.today().year)

def minutes_of(lessons): return sum(LESSON_META[l['id']]['minutes'] for l in lessons)
def fmt_minutes(m):
    if m < 60: return f'{m} min'
    h, r = divmod(m, 60)
    return f'{h}h {r:02d}m' if r else f'{h}h'
def fmt_hours(m): return f'about {int(round(m / 60))} hours'

def read(p): return open(os.path.join(ROOT, p), encoding='utf-8').read()
def esc(t): return html.escape(t, quote=True)

TIER_HOURS = {b['id']: int(round(minutes_of([l for p in b['parts'] for l in p['lessons']]) / 60)) for b in course['books']}

def fill(s):
    s = s.replace('{{LESSON_COUNT}}', str(LESSON_COUNT)).replace('{{YEAR}}', YEAR).replace('{{COURSE_HOURS}}', str(COURSE_HOURS))
    for tier, hours in TIER_HOURS.items():
        s = s.replace('{{HOURS_' + tier + '}}', str(hours))
    return s

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
        '    <link rel="alternate" type="application/atom+xml" title=".NET Made Easy: new and updated lessons" href="/feed.xml" />',
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
    ]
    if meta.get('ads', True):
        # Google's publisher policies forbid ads on error and other no-content
        # pages, so a page can opt out with "ads": false in its meta.
        h.append('    ' + ADSENSE)
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
        book_min = minutes_of([l for p in b['parts'] for l in p['lessons']])
        anchor = ANCHOR.get(b['id'], b['id'])
        s = [f'<section class="book" id="{anchor}">', f'    <h2>{esc(b["title"])}</h2>',
             f'    <p class="lede" style="margin-bottom:6px">{esc(BLURB.get(b["title"], ""))}</p>',
             f'    <p class="small muted" style="text-transform:uppercase;letter-spacing:.5px;font-weight:600">{count} lessons &middot; {len(b["parts"])} parts &middot; {fmt_hours(book_min)}</p>']
        for p in b['parts']:
            s.append(f'    <h3 id="{esc(p["id"])}">{esc(p["title"])} <span class="part-time">{len(p["lessons"])} lessons &middot; {fmt_minutes(minutes_of(p["lessons"]))}</span></h3>')
            s.append('    <ol class="lesson-list">')
            for l in p['lessons']:
                s.append(f'        <li><a href="{esc(l["href"])}">{esc(l["title"])}</a><span class="mins">{LESSON_META[l["id"]]["minutes"]} min</span></li>')
            s.append('    </ol>')
        s.append('</section>')
        sec.append('\n'.join(s))
    jsonld = {"@context": "https://schema.org", "@type": "Course",
              "name": ".NET Made Easy — Free C# and .NET Course",
              "description": f"A free, written C# and .NET course: {LESSON_COUNT} lessons across three tiers, from your first line of code through production systems.",
              "url": SITE + "/lessons.html", "isAccessibleForFree": True, "inLanguage": "en",
              "timeRequired": f"PT{int(round(COURSE_MINUTES / 60))}H",
              "provider": {"@type": "Organization", "name": "Layerbit", "url": "https://layerbit.co.in/"},
              "hasCourseInstance": {"@type": "CourseInstance", "courseMode": "online", "courseWorkload": f"PT{int(round(COURSE_MINUTES / 60))}H"},
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
        <div class="stat"><div class="num">~{COURSE_HOURS} h</div><div class="label">Reading time</div></div>
        <div class="stat"><div class="num">Free</div><div class="label">No signup</div></div>
    </div>
    <p class="small muted">Reading times are estimates for reading at a steady pace, typing the code, and answering the quiz. Most lessons take 15 to 25 minutes; the course player shows the time left in each part as you go.</p>
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


ROADMAP = [
    ('Phase 1: Write real C#', 'Beginner. No programming experience needed.', [
        ('Set up .NET and run your first program', ['f1'], 'Install the .NET SDK and an editor, then write, build and run a console app. Knowing what <code>dotnet run</code> actually does removes a lot of early confusion.', 'You can create and run a C# project from the command line.'),
        ('Learn the language basics', ['f2'], 'Variables, types, strings, operators, <code>if</code> and <code>switch</code>, loops and methods. This is the grammar every later lesson uses, so take it slowly and type every example yourself.', 'You can write a small program that makes decisions and repeats work.'),
        ('Think in objects', ['f3'], 'Classes, objects, properties, constructors, inheritance, polymorphism and interfaces. C# is object-oriented at its core, and most .NET code you will ever read looks like this.', 'You can model a small domain, such as a bank account or a library, with classes.'),
        ('Collections, errors, files and dates', ['f4', 'f5'], 'Arrays, <code>List&lt;T&gt;</code>, <code>Dictionary</code> and friends, then exceptions, files, streams, dates, time zones and JSON. These are the everyday tools of real programs.', 'You can load data from a file, work with it in collections and handle errors properly.'),
        ('Modern C# features', ['f6'], 'Nullable reference types, pattern matching, records, tuples, switch expressions and collection expressions. Modern C# code uses them everywhere, and they make code shorter and safer.', None),
        ('Debug, tidy up and build projects', ['f7'], 'Use the debugger, read stack traces, follow the naming conventions, then build two complete console projects from scratch.', 'You can build and debug a complete console application on your own.'),
    ]),
    ('Phase 2: Build real .NET applications', 'Working developer. You know the C# basics.', [
        ('Object-oriented design and SOLID', ['i1'], 'Abstract classes, sealed types, interface design and the SOLID principles that keep a growing codebase easy to change.', None),
        ('Generics, delegates and lambdas', ['i2', 'i3'], 'Write type-safe reusable code with generics, see how collections really work, and pass behaviour around with delegates, lambdas and events.', None),
        ('Query data with LINQ', ['i4'], 'Query any collection by describing the result you want. LINQ appears in almost every .NET codebase, and deferred execution is a classic interview topic.', None),
        ('Dependency injection, configuration, logging and HTTP', ['i5'], 'The building blocks of every modern .NET app: the DI container, service lifetimes, <code>appsettings.json</code>, the options pattern, <code>ILogger</code> and <code>HttpClient</code>.', None),
        ('Databases with ADO.NET and EF Core', ['i6'], 'Talk to SQL databases safely with parameters and transactions, then use Entity Framework Core for entities, relationships, migrations and queries.', None),
        ('Async and await', ['i7'], 'Tasks, <code>async</code> and <code>await</code>, cancellation, <code>Task.WhenAll</code> and async streams. Async code is the default in ASP.NET Core, so this stage matters to every web developer.', None),
        ('Build intermediate projects', ['i8'], 'Build a REST API, an EF Core data project, a notification service and a background worker, each with a complete solution to compare against.', 'You have practised the skills junior .NET job listings commonly ask for: C#, LINQ, EF Core, ASP.NET Core APIs and async code.'),
    ]),
    ('Phase 3: Run .NET in production', 'Senior track. You build .NET apps and want to run them well.', [
        ('How .NET runs your code', ['a1', 'a2', 'a3'], 'The CLR, the JIT, garbage collection, stack and heap, boxing and reflection, and how delegates, closures and LINQ work underneath.', None),
        ('Concurrency and performance', ['a4', 'a5'], 'The thread pool, synchronization context, locks, channels and race conditions, then <code>Span&lt;T&gt;</code>, pooling and benchmarking for code that must be fast.', None),
        ('Architecture and design patterns', ['a6'], 'SOLID at scale, the classic design patterns in C#, Clean Architecture, hexagonal architecture and domain-driven design.', None),
        ('Production ASP.NET Core', ['a7'], 'Middleware, filters, minimal APIs and controllers, validation, authentication with JWT and OpenID Connect, rate limiting, caching, resilience and observability.', None),
        ('Data at scale', ['a8'], 'EF Core performance, isolation levels, concurrency conflicts, bulk operations and finding slow queries.', None),
        ('Distributed systems', ['a9'], 'Microservices, messaging, Kafka, idempotency, retries, circuit breakers, the outbox pattern and eventual consistency.', None),
        ('Cloud and containers', ['a10'], 'Docker, cloud configuration, secrets, Kubernetes health probes, scaling and .NET Aspire.', None),
        ('Testing and production debugging', ['a11'], 'Unit, integration and API tests and load testing, then diagnosing memory leaks, high CPU, deadlocks and thread pool starvation in production.', None),
        ('Stay current with C# 14', ['a12'], 'Every new C# 14 feature, explained with before-and-after code.', None),
        ('Capstone: build a complete system', ['a13'], 'Put everything together in OrderFlow, a realistic order-management system, from architecture and authorization to messaging, monitoring and deployment.', 'You have designed, built, tested and deployed a distributed .NET system end to end.'),
    ]),
]

def build_roadmap():
    parts = {p['id']: p for b in course['books'] for p in b['parts']}
    path = '/dotnet-developer-roadmap.html'
    title = f'.NET Developer Roadmap {YEAR}: Learn C# and .NET Step by Step'
    desc = f'A step-by-step .NET developer roadmap for {YEAR}: what to learn in C# and .NET, in what order, how long each stage takes, and a free lesson for every skill.'
    rows, sections, n = [], [], 0
    for phase, who, stages in ROADMAP:
        phase_min = minutes_of([l for _, pids, _, _ in stages for pid in pids for l in parts[pid]['lessons']])
        sec = [f'<section class="phase">', f'    <h2>{esc(phase)}</h2>', f'    <p class="phase-who">{esc(who)} About {int(round(phase_min / 60))} hours of lessons.</p>']
        for name, pids, intro, milestone in stages:
            n += 1
            lessons = [l for pid in pids for l in parts[pid]['lessons']]
            mins = minutes_of(lessons)
            anchor = f'stage-{n}'
            rows.append(f'<tr><td>{n}</td><td><a href="#{anchor}">{esc(name)}</a></td><td>{len(lessons)}</td><td>{fmt_minutes(mins)}</td></tr>')
            links = ', '.join(f'<a href="{esc(l["href"])}">{esc(l["title"])}</a>' for l in lessons)
            sec += [f'    <div class="stage" id="{anchor}">',
                    f'        <h3><span class="stage-num">{n}</span>{esc(name)}</h3>',
                    f'        <p class="stage-meta">{len(lessons)} lessons &middot; about {fmt_minutes(mins)} &middot; {" &middot; ".join(esc(parts[pid]["title"].split(" — ", 1)[-1]) for pid in pids)}</p>',
                    f'        <p>{intro}</p>',
                    f'        <p class="stage-lessons"><strong>Lessons:</strong> {links}</p>']
            if milestone:
                sec.append(f'        <p class="stage-milestone"><strong>Checkpoint:</strong> {esc(milestone)}</p>')
            sec.append('    </div>')
        sec.append('</section>')
        sections.append('\n'.join(sec))
    jsonld = {"@context": "https://schema.org", "@graph": [
        {"@type": "TechArticle", "headline": title, "description": desc, "url": SITE + path, "mainEntityOfPage": SITE + path,
         "inLanguage": "en", "isAccessibleForFree": True, "image": {"@type": "ImageObject", "url": SITE + "/og-image.png", "width": 1200, "height": 630},
         "datePublished": "2026-10-18T00:00:00+00:00", "dateModified": file_lastmod('build.py'),
         "author": {"@type": "Organization", "name": "Layerbit", "url": SITE + "/about.html", "sameAs": "https://layerbit.co.in/"},
         "publisher": {"@type": "Organization", "name": ".NET Made Easy", "url": SITE + "/", "logo": {"@type": "ImageObject", "url": SITE + "/apple-touch-icon.png"}},
         "timeRequired": f"PT{int(round(COURSE_MINUTES / 60))}H"},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": ".NET Developer Roadmap"}]}]}
    meta = {'title': title, 'og_title': title, 'description': desc, 'path': path, 'nav': 'roadmap', 'jsonld': jsonld}
    body = f"""<main class="page page-narrow">
    <span class="eyebrow">Roadmap</span>
    <h1>.NET Developer Roadmap {YEAR}</h1>
    <p class="lede">What to learn to become a C# and .NET developer, in the order that makes each step easier than the last. Every stage links to free lessons on this site and shows roughly how long it takes.</p>
    <p>The roadmap has three phases. Phase 1 takes you from nothing to writing complete C# programs. Phase 2 covers the tools you use to build real .NET applications every day. Phase 3 is about running .NET well in production: performance, architecture, distributed systems, the cloud and debugging live problems.</p>
    <div class="callout"><p><strong>Where to start.</strong> New to programming? Start at stage 1 and use the <a href="/start-here.html">week-by-week plan</a>. Already code in another language? Skim Phase 1 and start properly at stage 7. Already ship C#? Jump to Phase 3.</p></div>
    <h2>The roadmap at a glance</h2>
    <div class="table-wrap"><table class="roadmap-table">
        <thead><tr><th>Stage</th><th>What you learn</th><th>Lessons</th><th>Time</th></tr></thead>
        <tbody>
            {(chr(10) + '            ').join(rows)}
        </tbody>
    </table></div>
    <p class="small muted">Times are reading estimates that include typing the code and answering each lesson's quiz. The whole roadmap is about {int(round(COURSE_MINUTES / 60))} hours of lessons. Plan extra time on top for practice: the code you write yourself is where most of the learning happens.</p>
{chr(10).join(sections)}
    <h2>Keep going</h2>
    <p>Track your progress through every stage in the <a href="/">course player</a>, which remembers where you stopped. When you are preparing for interviews, the <a href="/interview-prep.html">C# interview questions</a> page links each answer back to the lesson that explains it, and the <a href="/csharp-cheatsheet.html">C# cheat sheet</a> keeps the everyday syntax on one page.</p>
</main>
"""
    out = head(meta) + header_for('roadmap') + fill(body) + FOOTER + '</body>\n</html>\n'
    open(os.path.join(ROOT, path.lstrip('/')), 'w', encoding='utf-8').write(out)
    return path

SEO = json.load(open(os.path.join(ROOT, 'src', 'lesson-seo.json'), encoding='utf-8'))
DATES = json.load(open(os.path.join(ROOT, 'src', 'lesson-dates.json'), encoding='utf-8'))
TIER_ANCHOR = {'foundations': 'foundations', 'intermediate': 'intermediate', 'advanced': 'advanced'}
NOW = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()

def all_lessons():
    for b in course['books']:
        for p in b['parts']:
            for l in p['lessons']:
                yield b, p, l

def file_lastmod(rel):
    """Last commit date of a file, or now if it has uncommitted changes."""
    import subprocess
    dirty = subprocess.run(['git', '-C', ROOT, 'status', '--porcelain', '--', rel], capture_output=True, text=True).stdout.strip()
    if dirty:
        return NOW
    out = subprocess.run(['git', '-C', ROOT, 'log', '-1', '--format=%cI', '--', rel], capture_output=True, text=True).stdout.strip()
    return out or NOW

def sync_index():
    """Keep index.html's hand-written figures and crawlable lesson list in step with the course data."""
    p = os.path.join(ROOT, 'index.html')
    s = open(p, encoding='utf-8').read()
    for b in course['books']:
        count = sum(len(pt['lessons']) for pt in b['parts'])
        s = re.sub(r'(<div class="tier-count">)' + str(count) + r' lessons &middot; (\d+) parts &middot; about \d+ hours',
                   lambda m: f'{m.group(1)}{count} lessons &middot; {m.group(2)} parts &middot; about {TIER_HOURS[b["id"]]} hours', s)
    s = re.sub(r'"courseWorkload": "PT\d+H"', f'"courseWorkload": "PT{int(round(COURSE_MINUTES / 60))}H"', s)
    # Static copy of the sidebar lesson tree. The player replaces it with the
    # interactive tree on load; without JavaScript (and for crawlers that do
    # not run it) the home page still links to every lesson.
    t = ['<!-- static-tree -->']
    for b in course['books']:
        t.append(f'<details class="book-details" open><summary class="book-summary"><div class="book-header"><div class="book-title-row"><span>{esc(b["title"])}</span></div></div></summary><div class="nav-tree">')
        for k, pt in enumerate(b['parts']):
            t.append(f'<details class="part-details"{" open" if (b is course["books"][0] and k == 0) else ""}><summary><span>{esc(pt["title"])}</span><span class="part-meta">{fmt_minutes(minutes_of(pt["lessons"]))}</span></summary><ul class="lesson-list">')
            t.extend(f'<li><a class="lesson-link" href="{esc(l["href"])}"><span>{esc(l["title"])}</span></a></li>' for l in pt['lessons'])
            t.append('</ul></details>')
        t.append('</div></details>')
    t.append('<!-- /static-tree -->')
    tree = ''.join(t)
    s, n = re.subn(r'<div id="treeRoot">(?:<!-- static-tree -->.*?<!-- /static-tree -->)?</div>', lambda m: f'<div id="treeRoot">{tree}</div>', s, count=1, flags=re.S)
    assert n == 1, 'treeRoot not found in index.html'
    open(p, 'w', encoding='utf-8').write(s)

def build_sitemap(static_paths):
    urls = [(SITE + '/', file_lastmod('index.html'))]
    for path in static_paths:
        if path in ('/404.html',):
            continue
        rel = path.lstrip('/')
        src = os.path.join('src', 'pages', rel)
        urls.append((SITE + path, file_lastmod(src if os.path.exists(os.path.join(ROOT, src)) else rel)))
    if os.path.exists(os.path.join(ROOT, 'uae-pint-ae-e-invoicing-explained.html')):
        urls.append((SITE + '/uae-pint-ae-e-invoicing-explained.html', file_lastmod('uae-pint-ae-e-invoicing-explained.html')))
    for b, p, l in all_lessons():
        urls.append((SITE + l['href'], DATES[l['id']]['modified']))
    x = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, mod in urls:
        x.append(f'  <url><loc>{loc}</loc><lastmod>{mod}</lastmod></url>')
    x.append('</urlset>')
    open(os.path.join(ROOT, 'sitemap.xml'), 'w', encoding='utf-8').write('\n'.join(x) + '\n')
    return len(urls)

def build_feed(limit=50):
    items = sorted(all_lessons(), key=lambda t: (DATES[t[2]['id']]['modified'], DATES[t[2]['id']]['published']), reverse=True)[:limit]
    updated = max(DATES[l['id']]['modified'] for _, _, l in items)
    x = ['<?xml version="1.0" encoding="utf-8"?>', '<feed xmlns="http://www.w3.org/2005/Atom">',
         '  <title>.NET Made Easy: new and updated lessons</title>',
         f'  <subtitle>A free, written C# and .NET course: {LESSON_COUNT} lessons from your first program to production.</subtitle>',
         f'  <link href="{SITE}/feed.xml" rel="self" type="application/atom+xml" />',
         f'  <link href="{SITE}/" rel="alternate" type="text/html" />',
         f'  <id>{SITE}/</id>', f'  <updated>{updated}</updated>',
         '  <author><name>Layerbit</name><uri>https://layerbit.co.in/</uri></author>',
         f'  <icon>{SITE}/favicon-32x32.png</icon>']
    for b, p, l in items:
        url = SITE + l['href']
        d = DATES[l['id']]
        x += ['  <entry>', f'    <title>{esc(SEO[l["id"]]["title"])}</title>', f'    <link href="{url}" rel="alternate" type="text/html" />',
              f'    <id>{url}</id>', f'    <published>{d["published"]}</published>', f'    <updated>{d["modified"]}</updated>',
              f'    <category term="{esc(b["title"])}" />', f'    <summary>{esc(SEO[l["id"]]["description"])}</summary>', '  </entry>']
    x.append('</feed>')
    open(os.path.join(ROOT, 'feed.xml'), 'w', encoding='utf-8').write('\n'.join(x) + '\n')
    return len(items)

def build_llms():
    """llms.txt (https://llmstxt.org/): a plain-text map of the site for AI assistants and AI search."""
    out = ['# .NET Made Easy', '',
           f'> A free, written C# and .NET course from Layerbit: {LESSON_COUNT} lessons in three tiers, from a first program to running .NET in production. No signup and no paywall.',
           '',
           'Every lesson is a standalone HTML page with a plain-English explanation, diagrams, C# code examples, common mistakes and a short quiz. The course targets C# 14 and .NET 10.',
           '', '## Start here', '',
           f'- [Start Here guide]({SITE}/start-here.html): which path to take and a week-by-week plan for beginners and for developers switching to C#',
           f'- [.NET developer roadmap]({SITE}/dotnet-developer-roadmap.html): the skills a .NET developer needs, in order, each linked to its lessons',
           f'- [All lessons]({SITE}/lessons.html): the full syllabus with reading times',
           f'- [C# interview questions]({SITE}/interview-prep.html): common C# and .NET interview questions with direct answers',
           f'- [C# cheat sheet]({SITE}/csharp-cheatsheet.html): everyday C# syntax on one page',
           f'- [C# and .NET glossary]({SITE}/glossary.html): plain-English definitions of .NET terms',
           f'- [Interactive course player]({SITE}/): the same lessons with progress tracking and search', '']
    for b in course['books']:
        out += [f'## {b["title"]}', '']
        for p in b['parts']:
            out += [f'### {p["title"]}', '']
            out += [f'- [{SEO[l["id"]]["title"]}]({SITE}{l["href"]}): {SEO[l["id"]]["description"]}' for l in p['lessons']]
            out.append('')
    out += ['## About', '', f'- [About .NET Made Easy]({SITE}/about.html)', f'- [Contact]({SITE}/contact.html)', f'- [Privacy policy]({SITE}/privacy.html)', '']
    open(os.path.join(ROOT, 'llms.txt'), 'w', encoding='utf-8').write('\n'.join(out))

if __name__ == '__main__':
    built = [build_lessons_index(), build_roadmap()]
    for f in sorted(os.listdir(os.path.join(ROOT, 'src', 'pages'))):
        if f.endswith('.html'):
            built.append(build_page(f))
    sync_index()
    n_urls = build_sitemap(built)
    n_feed = build_feed()
    build_llms()
    print('built:', ', '.join(built))
    print(f'index.html synced; sitemap.xml: {n_urls} URLs; feed.xml: {n_feed} entries; llms.txt written')
