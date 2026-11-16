#!/usr/bin/env python3
"""Build the site from src/manual.html (the single source; edit that, then run this).

Writes four pages:
  index.html      the landing page: title, pledge, objectives, and the three parts
  agreement.html  The Agreement Manual
  operating.html  Studio operating manual
  meeting.html    Founding (partner meeting, the building, timing, next steps)
Every page carries the sidebar (parts at the root, sections inside the current part) and the glossary.
Links to anchors on another page are rewritten to page.html#id.
"""
import re
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
src = (ROOT / 'src' / 'manual.html').read_text()

# ---- split the source -------------------------------------------------------
i_nav = src.index('<nav id="siteNav"'); i_nav_end = src.index('</nav>', i_nav) + len('</nav>')
i_main = src.index('<main>', i_nav_end); i_main_end = src.index('</main>', i_main) + len('</main>')
pre, nav, main, rest = src[:i_nav], src[i_nav:i_nav_end], src[i_main:i_main_end], src[i_main_end:]

deskbar = re.search(r'<div class="deskbar".*?</div>\n', main, re.S).group(0)
i_hdr = main.index('<header>'); i_hdr_end = main.index('</header>', i_hdr) + len('</header>')
landing_header = main[i_hdr:i_hdr_end]
i_ops = main.index('<header class="part" id="part-ops">')
i_start = main.index('<header class="part" id="start">')
agreement_body = main[i_hdr_end:i_ops].strip('\n')
ops_body = main[i_ops:i_start].strip('\n').replace('<header class="part" id="part-ops">', '<header id="part-ops">', 1)
founding_body = main[i_start:main.rindex('</main>')].strip('\n').replace('<header class="part" id="start">', '<header id="start">', 1)

# landing header: keep title, description, pledge, agreement line, objectives; rebuild the parts index with all three parts
landing_header = re.sub(r'  <div class="parts-index">.*?\n  </div>\n', '', landing_header, count=1, flags=re.S)
PARTS = [
    ('agreement', 'agreement.html', 'The Agreement Manual',
     "What the studio is, who's in it, and how ownership, contributions, taxes, money, decisions, and leaving work. The spec for the operating agreement."),
    ('ops', 'operating.html', 'Studio operating manual',
     "How we run the place day to day: the room, the gear, moving money, and the monthly close. House rules, and the manager's instructions."),
    ('founding', 'meeting.html', 'Founding',
     "How we get from here to there: the partner meeting, the building, the timing, and what each partner supplies."),
]
parts_index = '  <div class="parts-index">\n' + ''.join(
    f'    <div class="part-entry">\n      <p class="part-name"><a href="{f}">{t}</a></p>\n      <p>{d}</p>\n      <a href="{f}">Go to {t}</a>\n    </div>\n'
    for _, f, t, d in PARTS) + '  </div>\n'
landing_header = landing_header.replace('</header>', parts_index + '</header>')

# agreement page header: title + description only
agreement_header = ('<header id="agreement">\n  <h1>The Agreement Manual</h1>\n'
                    '  <p>' + PARTS[0][3] + '</p>\n'
                    '  <p class="pledge">Every word in here needs to be something we all agree to.</p>\n'
                    '  <p>This manual is what we agree to. We use it to create the operating agreement, which a lawyer reviews before we sign. Nothing goes in there that isn\'t in here.</p>\n</header>')

# ---- nav groups --------------------------------------------------------------
close_link = re.search(r'\s*<a class="toc-close"[^>]*>Close</a>\n', nav).group(0)
gloss_link = re.search(r'\s*<a class="sub" href="#glossary"[^>]*>Glossary</a>\n', nav).group(0)
body = nav[nav.index('>') + 1:nav.rindex('</nav>')].replace(close_link, '').replace(gloss_link, '')
groups = [g for g in re.split(r'(?=  <h1)', body) if g.strip()]
assert len(groups) == 3, len(groups)
panes = dict(zip(['agreement', 'ops', 'founding'], [re.sub(r'  <h1[^>]*>.*?</h1>\n', '', g, count=1) for g in groups]))

def nav_for(current):
    root = '  <div class="nav-root">\n    <p class="nav-eyebrow"><a href="index.html">Contents</a></p>\n'
    for key, f, t, d in PARTS:
        if key == current:
            root += f'    <button type="button" class="nav-part-btn" data-go="{key}"><b>{t}</b><span>{d}</span></button>\n'
        else:
            root += f'    <a class="nav-part-btn" href="{f}"><b>{t}</b><span>{d}</span></a>\n'
    root += '  </div>\n'
    pane = ''
    if current:
        title = next(t for k, _, t, _ in PARTS if k == current)
        pane = (f'  <div class="nav-part" data-part="{current}">\n'
                f'    <button type="button" class="nav-back" data-go="root">All parts</button>\n'
                f'    <h1>{title}</h1>\n{panes[current]}  </div>\n')
    level = current or 'root'
    return (f'<nav id="siteNav" tabindex="-1" aria-label="Contents" data-level="{level}" data-home="{level}">\n'
            + close_link.lstrip('\n') + root + pane + gloss_link.lstrip('\n') + '</nav>')

# ---- chrome ------------------------------------------------------------------
EXTRA_CSS = '''  nav .nav-root, nav .nav-part { display: none; }
  nav[data-level="root"] .nav-root { display: block; }
  nav[data-level="agreement"] .nav-part[data-part="agreement"], nav[data-level="ops"] .nav-part[data-part="ops"], nav[data-level="founding"] .nav-part[data-part="founding"] { display: block; }
  nav .nav-eyebrow { font-size: 13px; font-weight: 600; color: var(--ink-3); margin: 0 0 10px; }
  nav .nav-eyebrow a { color: inherit; text-decoration: none; }
  nav .nav-eyebrow a:hover { color: var(--blue); }
  nav .nav-part-btn { display: block; width: 100%; text-align: left; font: inherit; color: inherit; background: var(--paper-2); border: 0; border-radius: 10px; padding: 12px 14px; margin: 0 0 10px; cursor: pointer; text-decoration: none; }
  nav .nav-part-btn b { display: block; font-size: 15px; font-weight: 700; margin: 0 0 3px; }
  nav .nav-part-btn span { display: block; font-size: 13px; line-height: 1.4; color: var(--ink-2); }
  nav .nav-part-btn:hover { background: var(--blue-soft); }
  nav .nav-part-btn:focus-visible { outline: 2px solid var(--blue); outline-offset: 2px; }
  nav .nav-back { display: block; font: inherit; font-size: 13px; font-weight: 600; color: var(--blue); background: none; border: 0; padding: 0 0 14px; cursor: pointer; }
  nav .nav-back::before { content: "\\2039\\00a0"; }
  header .parts-index .part-name a { color: inherit; text-decoration: none; }
  header .parts-index .part-name a:hover { color: var(--blue); }
  @media (max-width: 900px) { nav .nav-part-btn b { font-size: 16px; } nav .nav-part-btn span { font-size: 14px; } }
'''
EXTRA_JS = '''
  // Sidebar: the parts at the root, this part's sections inside. Follows the scroll unless the reader backed out to the root.
  (function(){
    const navEl=document.getElementById('siteNav'); if(!navEl) return;
    const home=navEl.dataset.home||'root'; let manual=false;
    function setLevel(l){ if(navEl.dataset.level!==l) navEl.dataset.level=l; }
    function follow(){ if(manual) return; const cur=navEl.querySelector('summary a.current'); const part=cur?cur.closest('.nav-part'):null; setLevel(part?part.dataset.part:home); }
    navEl.addEventListener('click', e=>{
      const go=e.target.closest('[data-go]');
      if(go){ e.preventDefault(); const to=go.dataset.go;
              if(to==='root'){ manual=true; setLevel('root'); navEl.scrollTo({top:0}); }
              else { manual=false; setLevel(to); window.scrollTo({top:0, behavior:'smooth'}); try{ history.pushState(null,'',location.pathname); }catch(x){} if(document.body.classList.contains('toc-open') && typeof setOpen==='function') setOpen(false); }
              return; }
      if(e.target.closest('a[href^="#"]')) manual=false;
    });
    window.addEventListener('scroll', ()=>requestAnimationFrame(()=>requestAnimationFrame(follow)), {passive:true});
    window.addEventListener('resize', follow);
    follow();
  })();
'''

def page(title_tag, book, current, main_inner):
    p = pre.replace('<title>The Agreement Manual</title>', f'<title>{title_tag}</title>', 1)
    p = p.replace('<span class="mobilebar-book">The Agreement Manual</span>', f'<span class="mobilebar-book">{book}</span>', 1)
    html = p + nav_for(current) + '\n<main>\n' + deskbar + main_inner + '\n</main>' + rest
    html = html.replace('</style>', EXTRA_CSS + '</style>', 1)
    html = html.replace('\n</script>', EXTRA_JS + '</script>', 1)
    return html

pages = {
    'index.html': page('The Agreement Manual', 'The Agreement Manual', None, landing_header),
    'agreement.html': page('The Agreement Manual', 'The Agreement Manual', 'agreement', agreement_header + '\n\n' + agreement_body),
    'operating.html': page('Studio operating manual', 'Studio operating manual', 'ops', ops_body),
    'meeting.html': page('Founding: The Agreement Manual', 'Founding', 'founding', founding_body),
}

# ---- cross-page links --------------------------------------------------------
def ids(html): return set(re.findall(r'id="([^"]+)"', html))
page_ids = {f: ids(h) for f, h in pages.items()}
def relink(f, html):
    own = page_ids[f]
    def fix(m):
        t = m.group(1)
        if t in own: return m.group(0)
        for g, s in page_ids.items():
            if g != f and t in s: return f'href="{g}#{t}"'
        return m.group(0)
    return re.sub(r'href="#([^"]+)"', fix, html)
pages = {f: relink(f, h) for f, h in pages.items()}

for f, h in pages.items():
    (ROOT / f).write_text(h)
    bad = sorted(set(x for x in re.findall(r'href="#([^"]+)"', h) if x not in page_ids[f]))
    cross = len(re.findall(r'href="[a-z]+\.html#', h))
    print(f'{f}: {len(h):,} bytes, broken {bad}, cross-page links {cross}')
