#!/usr/bin/env python3
"""Convert Hugo markdown blog posts to static HTML pages."""

import os
import re
import markdown

SITE_DIR = os.path.expanduser("~/Codes/go/src/github.com/auxten/site/content/posts")
OUT_DIR = os.path.expanduser("~/Codes/go/src/github.com/auxten/auxten.com/blog")

# Map source folder -> output slug (Hugo posts)
POSTS = {
    "chDB is joining ClickHouse": "chdb-is-joining-clickhouse",
    "ClickHouse on Pandas DataFrame": "clickhouse-on-pandas-dataframe",
    "Context Management Is the Real Bottleneck for AI Agents": "context-management-is-the-real-bottleneck-for-ai-agents",
    "How I make Apache Superset a macOS App": "how-i-made-apache-superset-a-macos-app",
    "My 182 ARM SBC Draws 7 Watts and Runs a Full AI Agent": "my-182-arm-sbc-draws-7-watts-and-runs-a-full-ai-agent",
    "Potential of MCP in Database Applications is still underestimated": "potential-of-mcp-in-database-applications",
    "The birth of chDB": "the-birth-of-chdb",
    "Vector Database-1": "vector-databases-a-traditional-database-developers-perspective",
}

# Direct markdown posts (not from Hugo): (md_path, title, date, slug)
DIRECT_POSTS = [
    (
        os.path.expanduser("~/Library/CloudStorage/Dropbox/Notes/写书/openclaw-meetup-images/how-i-manage-my-one-man-company-with-openclaw.md"),
        "How I Manage My One-Man Company with OpenClaw",
        "2026-03-14",
        "how-i-manage-my-one-man-company-with-openclaw",
    ),
]

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} — auxten</title>
  <meta name="description" content="{title} — A blog post by Auxten Wang">
  <meta name="author" content="Auxten Wang">
  <link rel="canonical" href="https://auxten.com/blog/{slug}.html">
  <!-- Open Graph -->
  <meta property="og:type" content="article">
  <meta property="og:title" content="{title} — auxten">
  <meta property="og:description" content="{title} — A blog post by Auxten Wang">
  <meta property="og:url" content="https://auxten.com/blog/{slug}.html">
  <meta property="og:image" content="https://auxten.com/head.jpg">
  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary">
  <meta name="twitter:site" content="@auxten">
  <meta name="twitter:title" content="{title} — auxten">
  <meta name="twitter:description" content="{title} — A blog post by Auxten Wang">
  <meta name="twitter:image" content="https://auxten.com/head.jpg">
  <link rel="icon" href="/favicon.ico">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/style.css">
  <!-- Google Analytics -->
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-23V4MNKDZJ"></script>
  <script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-23V4MNKDZJ');</script>
</head>
<body>
  <nav class="nav">
    <div class="nav-inner">
      <a href="/" class="nav-logo">auxten<span class="dot">.</span></a>
      <div class="nav-links">
        <a href="/#projects">Projects</a>
        <a href="/#press">Talks</a>
        <a href="/blog.html">Blog</a>
        <a href="/#about">About</a>
        <button class="theme-toggle" id="themeToggle" aria-label="Toggle theme">
          <svg class="icon-sun" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>
          <svg class="icon-moon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
        </button>
      </div>
    </div>
  </nav>

  <div class="post-header">
    <h1>{title}</h1>
    <p class="post-meta">{date}</p>
  </div>

  <div class="post-wrapper">
    <nav class="post-toc" id="postToc"></nav>
    <article class="post-content" id="postContent">
      {content}
    </article>
  </div>

  <footer class="footer">
    <div class="footer-inner">
      <p>&copy; 2009&ndash;2026 Auxten Wang &middot; Licensed under <a href="https://creativecommons.org/licenses/by-nc/4.0/" target="_blank" rel="noopener">CC BY-NC 4.0</a></p>
    </div>
  </footer>

  <script src="/theme.js"></script>
  <script>
  (function(){{
    var toc=document.getElementById('postToc');
    var content=document.getElementById('postContent');
    if(!toc||!content)return;
    var headings=content.querySelectorAll('h2,h3');
    if(headings.length<2){{toc.style.display='none';return;}}
    headings.forEach(function(h){{
      var a=document.createElement('a');
      a.href='#'+h.id;
      a.textContent=h.textContent;
      if(h.tagName==='H3')a.classList.add('post-toc-h3');
      toc.appendChild(a);
    }});
    var links=toc.querySelectorAll('a');
    function updateActive(){{
      var scrollPos=window.scrollY+150;
      var current=null;
      headings.forEach(function(h){{
        if(h.offsetTop<=scrollPos)current=h;
      }});
      links.forEach(function(a){{
        a.classList.toggle('active',current&&a.getAttribute('href')==='#'+current.id);
      }});
    }}
    window.addEventListener('scroll',updateActive);
    updateActive();
  }})();
  </script>
  <div class="lightbox" id="lightbox"><img id="lightboxImg"></div>
  <script>
  (function(){{
    var lb=document.getElementById('lightbox');
    var lbImg=document.getElementById('lightboxImg');
    var content=document.getElementById('postContent');
    if(!content)return;
    content.addEventListener('click',function(e){{
      if(e.target.tagName==='IMG'){{
        lbImg.src=e.target.src;
        lb.classList.add('active');
      }}
    }});
    lb.addEventListener('click',function(){{
      lb.classList.remove('active');
    }});
    document.addEventListener('keydown',function(e){{
      if(e.key==='Escape')lb.classList.remove('active');
    }});
  }})();
  </script>
</body>
</html>
"""


def parse_frontmatter(text):
    """Extract frontmatter and body from markdown."""
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            fm = parts[1].strip()
            body = parts[2].strip()
            meta = {}
            for line in fm.split("\n"):
                if ":" in line:
                    key, val = line.split(":", 1)
                    meta[key.strip()] = val.strip().strip('"').strip("'")
            return meta, body
    # Handle frontmatter with +++ delimiters
    if text.startswith("+++"):
        parts = text.split("+++", 2)
        if len(parts) >= 3:
            fm = parts[1].strip()
            body = parts[2].strip()
            meta = {}
            for line in fm.split("\n"):
                if "=" in line:
                    key, val = line.split("=", 1)
                    meta[key.strip()] = val.strip().strip('"').strip("'")
            return meta, body
    return {}, text


def fix_image_paths(html, slug):
    """Fix image paths to be relative to the post directory."""
    # Hugo-style image references like /post-slug/image.png or just image.png
    # Replace absolute Hugo paths like /chdb-is-joining-clickhouse/image.png
    # with relative paths
    html = re.sub(
        r'src="/' + re.escape(slug) + r'/([^"]+)"',
        r'src="\1"',
        html
    )
    # Also handle Hugo shortcode-style paths
    # Replace src="/post-title/image.png" patterns
    for folder_name, s in POSTS.items():
        # Handle various Hugo path patterns
        html = re.sub(
            r'src="/' + re.escape(folder_name.lower().replace(" ", "-")) + r'/([^"]+)"',
            lambda m, sl=s: f'src="/blog/{sl}/{m.group(1)}"',
            html, flags=re.IGNORECASE
        )
    # Fix relative image refs (just filename) to include blog path
    # Match src="filename.ext" where filename doesn't start with / or http
    html = re.sub(
        r'src="(?!/|http)([^"]+)"',
        lambda m: f'src="/blog/{slug}/{m.group(1)}"',
        html
    )
    return html


def fix_hugo_specific(body):
    """Remove Hugo-specific shortcodes and fix markup."""
    # Remove Hugo shortcodes like {{< ... >}}
    body = re.sub(r'\{\{<[^>]*>\}\}', '', body)
    body = re.sub(r'\{\{%[^%]*%\}\}', '', body)

    # Fix image references - convert Hugo absolute paths to relative
    # /post-slug/image.png -> image.png (since we're in the slug directory)
    for folder_name, slug in POSTS.items():
        # Handle /slug/image.png pattern
        body = body.replace(f"/{slug}/", "")
        # Handle Hugo resource paths
        lower_folder = folder_name.lower().replace(" ", "-")
        body = body.replace(f"/{lower_folder}/", "")

    # Handle raw HTML img tags with style attributes - keep them as-is
    # but fix their src paths

    return body


def convert_post(folder_name, slug):
    """Convert a single post from markdown to HTML."""
    md_path = os.path.join(SITE_DIR, folder_name, "index.md")
    if not os.path.exists(md_path):
        print(f"  SKIP: {md_path} not found")
        return

    with open(md_path, "r", encoding="utf-8") as f:
        raw = f.read()

    meta, body = parse_frontmatter(raw)
    title = meta.get("title", folder_name)
    date_str = meta.get("date", "")
    # Extract just the date part (YYYY-MM-DD)
    date_short = date_str[:10] if len(date_str) >= 10 else date_str

    # Fix Hugo-specific content
    body = fix_hugo_specific(body)

    # Convert markdown to HTML
    md = markdown.Markdown(extensions=[
        'tables',
        'fenced_code',
        'codehilite',
        'toc',
        'attr_list',
    ], extension_configs={
        'codehilite': {'css_class': 'highlight', 'guess_lang': False},
    })
    html_content = md.convert(body)

    # Fix image paths in the generated HTML
    html_content = fix_image_paths(html_content, slug)

    # Write output
    out_path = os.path.join(OUT_DIR, slug + ".html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(TEMPLATE.format(
            title=title,
            date=date_short,
            content=html_content,
            slug=slug,
        ))
    print(f"  OK: {slug}.html ({len(html_content)} chars)")

    # Write markdown version for AI agents (llms.txt convention)
    md_out_path = os.path.join(OUT_DIR, slug + ".md")
    with open(md_out_path, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n")
        f.write(f"*{date_short} — by Auxten Wang*\n\n")
        f.write(body)
    print(f"  OK: {slug}.md")


def convert_direct_post(md_path, title, date_short, slug):
    """Convert a direct markdown file (not from Hugo) to HTML."""
    if not os.path.exists(md_path):
        print(f"  SKIP: {md_path} not found")
        return

    with open(md_path, "r", encoding="utf-8") as f:
        body = f.read()

    # Strip the H1 title and blockquote if present (already in template)
    lines = body.split("\n")
    start = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and not stripped.startswith(">") and stripped != "---":
            start = i
            break
    # Find first --- separator and skip everything before it
    for i, line in enumerate(lines):
        if line.strip() == "---" and i > 0:
            start = i + 1
            break
    body = "\n".join(lines[start:])

    # Add ClickHouse blog links to the Links section at the bottom (before italic strip)
    body = body.replace(
        '- *[Building chDB DataStore with AI](https://github.com/chdb-io/chdb/pull/496) — Multi-agent pipeline for pandas compatibility*',
        '- *[Building chDB DataStore with AI](https://github.com/chdb-io/chdb/pull/496) — Multi-agent pipeline for pandas compatibility*\n'
        '- *[The Journey to Zero-Copy](https://clickhouse.com/blog/chdb-journey-to-zero-copy) — ClickHouse Blog*\n'
        '- *[chDB 4.0 — Pandas Hex](https://clickhouse.com/blog/chdb.4-0-pandas-hex) — ClickHouse Blog*'
    )

    # Add link to ClickHouse acquisition
    body = body.replace(
        'In 2023, ClickHouse acquired chDB.',
        'In 2023, [ClickHouse acquired chDB](https://clickhouse.com/blog/chdb-joins-clickhouse-family).'
    )

    # Remove redundant blockquote (duplicated by screenshot below)
    body = body.replace(
        '> "Building a rendering engine from scratch in 2026 is the kind of ambitious bet the web needs. Monoculture kills innovation."\n',
        ''
    )

    # Fix italic list items: "- *[link](url) — desc*" -> proper list items
    body = re.sub(r'^- \*(.+)\*$', r'- \1', body, flags=re.MULTILINE)
    # Fix "*Links:*" prefix to be a proper heading
    body = body.replace('*Links:*\n', '**Links:**\n\n')

    # Convert zoom styles to percentage max-width for better rendering
    body = re.sub(r'style="zoom:\s*(\d+)%;\s*"',
                  lambda m: f'style="max-width: {min(int(m.group(1)) * 8, 100)}%;"',
                  body)

    # Add max-width to chDB logo
    body = body.replace(
        '![chDB logo](chdb-logo.png)',
        '<img src="chdb-logo.png" alt="chDB logo" style="max-width: 200px;">'
    )

    # Add multi-agent pipeline screenshot and replace benchmark image with webp
    body = body.replace(
        '![chDB DataStore benchmark — pandas vs chDB vs DuckDB across 14 operations](chdb-dataframe-benchmark.png)',
        '![chDB DataStore multi-agent pipeline — test generator, bug fixer, reviewer, all orchestrated by Python](chdb-ai-loop.jpg)\n\n'
        '![chDB DataStore benchmark — pandas vs chDB vs DuckDB across 14 operations](chdb-dataframe-benchmark.webp)\n\n'
        '*Source: [The Journey to Zero-Copy](https://clickhouse.com/blog/chdb-journey-to-zero-copy) — ClickHouse Blog. '
        'See also: [chDB 4.0 — Pandas Hex](https://clickhouse.com/blog/chdb.4-0-pandas-hex)*'
    )

    # Fix image paths: relative images -> /blog/slug/image.png
    body = re.sub(
        r'!\[([^\]]*)\]\((?!/|http)([^)]+)\)',
        lambda m: f'![{m.group(1)}](/blog/{slug}/{m.group(2)})',
        body
    )
    # Fix HTML img tags with relative src
    body = re.sub(
        r'src="(?!/|http)([^"]+)"',
        lambda m: f'src="/blog/{slug}/{m.group(1)}"',
        body
    )

    # Convert markdown to HTML
    md = markdown.Markdown(extensions=[
        'tables',
        'fenced_code',
        'codehilite',
        'toc',
        'attr_list',
    ], extension_configs={
        'codehilite': {'css_class': 'highlight', 'guess_lang': False},
    })
    html_content = md.convert(body)

    # Convert <p><img alt="..."></p> to <figure><img><figcaption></figure>
    # Skip generic alt texts like "image-2026..." or simple logos
    def img_to_figure(m):
        full = m.group(0)
        alt = re.search(r'alt="([^"]*)"', full)
        if not alt:
            return full
        alt_text = alt.group(1)
        # Skip generic or trivial alt texts
        if not alt_text or alt_text.startswith('image-') or alt_text in ('chDB logo',):
            return full
        img_tag = re.search(r'<img[^>]+>', full).group(0)
        return f'<figure>{img_tag}<figcaption>{alt_text}</figcaption></figure>'

    html_content = re.sub(
        r'<p>(<img[^>]+>)\s*</p>',
        img_to_figure,
        html_content
    )

    # Write HTML output
    out_path = os.path.join(OUT_DIR, slug + ".html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(TEMPLATE.format(
            title=title,
            date=date_short,
            content=html_content,
            slug=slug,
        ))
    print(f"  OK: {slug}.html ({len(html_content)} chars)")

    # Write markdown version for AI agents
    md_out_path = os.path.join(OUT_DIR, slug + ".md")
    with open(md_out_path, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n")
        f.write(f"*{date_short} — by Auxten Wang*\n\n")
        f.write(body)
    print(f"  OK: {slug}.md")


def main():
    print("Building blog posts...")
    for folder_name, slug in POSTS.items():
        convert_post(folder_name, slug)
    for md_path, title, date, slug in DIRECT_POSTS:
        convert_direct_post(md_path, title, date, slug)
    print("Done!")


if __name__ == "__main__":
    main()
