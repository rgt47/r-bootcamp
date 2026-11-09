#!/usr/bin/env python3
"""Generate analysis/report/contents.qmd, the HTML book's full contents.

Run as a Quarto pre-render step, so the page always follows the chapter
order in the book configuration (_quarto.yml, or _quarto-html.yml when
the chapter list lives in the HTML profile). Chapter numbers are
computed the way Quarto assigns them: numbered chapters 1, 2, ...;
numbered appendices A, B, ...; parts I, II, ....

Each chapter's one-line summary comes from, in order of preference:
the bullet that describes it on its part page ('- @sec-why distinguishes
...'), or a 'description:' field in the chapter's own front matter.
Chapters with neither are listed by title alone.

The page is HTML only: the PDF has its own printed table of contents.
If PyYAML is unavailable the script leaves the existing page in place
rather than failing the build.
"""
import re
import sys
import textwrap
from pathlib import Path

REPORT = Path(__file__).resolve().parent.parent / 'analysis' / 'report'
OUT = REPORT / 'contents.qmd'

try:
    import yaml
except ImportError:
    print('make-contents: PyYAML not available; keeping existing '
          'contents.qmd', file=sys.stderr)
    sys.exit(0)

ROMAN = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X',
         'XI', 'XII', 'XIII', 'XIV', 'XV']


def book_config():
    for name in ('_quarto.yml', '_quarto-html.yml'):
        p = REPORT / name
        if p.exists():
            book = (yaml.safe_load(p.read_text()) or {}).get('book') or {}
            if 'chapters' in book:
                return book
    sys.exit('make-contents: no book chapter list found')


def front_matter(text):
    m = re.match(r'^---\n(.*?)\n---\n', text, re.S)
    if not m:
        return {}
    try:
        return yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return {}


def heading(qmd):
    """Title, anchor id, numbered and listed flags, and description."""
    text = (REPORT / qmd).read_text()
    fm = front_matter(text)
    desc = fm.get('description')
    for line in text.splitlines():
        m = re.match(r'^#\s+(.*?)\s*(\{[^}]*\})?\s*$', line)
        if m:
            attrs = m.group(2) or ''
            sid = re.search(r'#(sec-[\w-]+)', attrs)
            return (m.group(1), sid.group(1) if sid else None,
                    '.unnumbered' not in attrs, '.unlisted' not in attrs,
                    desc)
    title = fm.get('title', qmd)
    return title, None, True, True, desc


def part_summaries(part_qmd):
    """Map sec-id -> summary text from a part page's bullets."""
    out = {}
    text = (REPORT / part_qmd).read_text()
    for m in re.finditer(r'^- @(sec-[\w-]+) (.*?)(?=\n- |\n\n|\Z)',
                         text, re.M | re.S):
        s = ' '.join(m.group(2).split())
        out[m.group(1)] = s[0].upper() + s[1:]
    return out


def entry(qmd, number, title, summary):
    label = f'{number} {title}' if number else title
    line = textwrap.fill(f'- [{label}]({qmd})', width=76,
                         subsequent_indent='  ', break_long_words=False,
                         break_on_hyphens=False)
    if summary:
        line += '\\\n' + textwrap.fill(' '.join(str(summary).split()),
                                        width=72, initial_indent='  ',
                                        subsequent_indent='  ')
    return line


book = book_config()
lines = []
state = {'chap': 0, 'part': 0}


def add_chapter(qmd, summ=None):
    if qmd == 'contents.qmd' or not (REPORT / qmd).exists():
        return
    title, sid, numbered, listed, desc = heading(qmd)
    if not listed:
        return
    num = None
    if numbered:
        state['chap'] += 1
        num = str(state['chap'])
    lines.append(entry(qmd, num, title,
                       (summ or {}).get(sid) or desc))


back_matter_open = False
for item in book['chapters']:
    if isinstance(item, str):
        # Top-level files after the parts (References) are back matter,
        # not part of the last part.
        if state['part'] and not back_matter_open:
            lines += ['', '## References and Appendices {.unnumbered}', '']
            back_matter_open = True
        add_chapter(item)
        continue
    state['part'] += 1
    part = item['part']
    roman = ROMAN[state['part'] - 1]
    if str(part).endswith('.qmd') and (REPORT / part).exists():
        ptitle = heading(part)[0]
        lines += ['', f'## Part {roman}. [{ptitle}]({part}) {{.unnumbered}}',
                  '']
        summ = part_summaries(part)
    else:
        lines += ['', f'## Part {roman}. {part} {{.unnumbered}}', '']
        summ = {}
    for c in item.get('chapters', []):
        add_chapter(c, summ)

appendices = book.get('appendices') or []
if appendices and not back_matter_open:
    lines += ['', '## Appendices {.unnumbered}', '']
app = 0
for qmd in appendices:
    if not (REPORT / qmd).exists():
        continue
    title, sid, numbered, listed, desc = heading(qmd)
    if not listed:
        continue
    num = None
    if numbered:
        num = chr(ord('A') + app)
        app += 1
    lines.append(entry(qmd, num, title, desc))

body = '\n'.join(lines).strip('\n')
intro = 'Every part and chapter of the book on one page, in reading order'
intro += (', each chapter with a one-line summary.' if '\\\n' in body
          else '.')
page = f'''::: {{.content-visible when-format="html"}}

# Contents {{.unnumbered}}

<!-- Generated by tools/make-contents.py from the book configuration
and chapter files on every build. Edit those, not this file. -->

{textwrap.fill(intro, width=72)}

{body}

:::
'''
if not OUT.exists() or OUT.read_text() != page:
    OUT.write_text(page)
    print(f'make-contents: wrote {OUT.name}')
