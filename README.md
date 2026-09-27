# .NET Made Easy

Source for [dotnetmadeeasy.com](https://dotnetmadeeasy.com) — a free, written C# and .NET course (315 lessons across three tiers), published by [Layerbit](https://layerbit.co.in/).

The site is static and served from this repository by GitHub Pages; the `main` branch is what is live.

## Layout

| Path | What it is |
|---|---|
| `index.html` | The course player: a single-page shell that lists every lesson in a sidebar and loads the lesson file into the reading pane. Progress, theme and reader preferences are kept in the visitor's `localStorage`. |
| `Content/*.html` | The 315 lessons. Each is a complete standalone page (its own header, nav, footer, structured data) *and* the fragment the course player injects. Blocks meant only for the standalone view carry a `standalone-*` class and are stripped on injection. |
| `lessons.html`, `start-here.html`, `interview-prep.html`, `glossary.html`, `csharp-cheatsheet.html`, `about.html`, `contact.html`, `privacy.html`, `terms.html`, `404.html` | Static pages, **generated** — do not edit these directly. |
| `src/pages/*.html` | Sources for the static pages: a JSON meta comment followed by the page body. |
| `src/partials/` | Shared header and footer. |
| `src/course.json` | The course structure (books → parts → lessons). Drives `lessons.html` and the lesson count shown across the site. |
| `assets/site.css` | Shared stylesheet for the static pages. |
| `build.py` | Builds the static pages from `src/`. |
| `search-index.json`, `related-lessons.json` | Prebuilt indexes used by the course player's search and related-lessons features. |
| `sitemap.xml`, `robots.txt`, `ads.txt`, `manifest.json`, `CNAME` | Hosting, indexing and advertising configuration. |

## Editing

- **A lesson:** edit the file in `Content/`. Keep the `standalone-*` blocks and the `<style id="standalone-page-reset">` block intact; the player relies on them.
- **A static page:** edit `src/pages/<name>.html`, then run `python3 build.py` and commit both the source and the generated file.
- **Header, footer or nav:** edit `src/partials/`, rebuild. (The course player and the lesson files have their own copies of the nav — search for `standalone-site-header` and `sidebar-footer-links`.)
- **The design:** tokens live at the top of `assets/site.css`, of `index.html`'s `<style>`, and of the `standalone-page-reset` block in every lesson. Keep them in step.

No dependencies beyond Python 3 for the build.
