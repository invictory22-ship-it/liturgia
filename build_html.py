# -*- coding: utf-8 -*-
import shutil

path = 'index.html'
html = open(path, encoding='utf-8').read()
shutil.copyfile(path, 'index.html.bak')
log = []

# 1) прибрати inline-рядок const BLOCKS = ... ;
lines = html.split('\n')
kept = [ln for ln in lines if not ln.lstrip().startswith('const BLOCKS = [')]
log.append('inline BLOCKS rows removed: %d' % (len(lines) - len(kept)))
html = '\n'.join(kept)

# 2) підключити зовнішній файл
if 'liturgy-data.js' not in html:
    html = html.replace('<script>\n', '<script src="liturgy-data.js"></script>\n<script>\n', 1)
    log.append('external script tag inserted')
else:
    log.append('external script tag already present')

# 3) CSS для fold
fold_css = """  /* FOLD */
  .b-fold { margin: 20px auto 20px 0; max-width: 680px; }
  .b-fold > summary {
    color: #9a8a5f; font-size: 14px; font-style: italic; cursor: pointer;
    list-style: none; padding: 9px 14px; border: 1px dashed #3a3320;
    border-radius: 8px; user-select: none;
  }
  .b-fold > summary::-webkit-details-marker { display: none; }
  .b-fold > summary::before { content: "\\25b8 "; color: #6a5f3a; }
  .b-fold[open] > summary::before { content: "\\25be "; }
  .b-fold > summary:hover { background: #141414; }
  .b-fold[open] > summary { margin-bottom: 8px; color: #b09560; }
  .b-fold .b-stage { margin: 10px 0; border-left-color: #3a3320; }
"""
if '.b-fold {' not in html:
    html = html.replace('</style>', fold_css + '</style>', 1)
    log.append('fold CSS inserted')
else:
    log.append('fold CSS already present')

# 4) рендер fold
fold_render = """    } else if (block.t === 'fold'){
      const det = document.createElement('details');
      det.className = 'b-fold';
      if (block.open) det.open = true;
      const sum = document.createElement('summary');
      sum.textContent = block.text;
      det.appendChild(sum);
      for (const cb of (block.blocks||[])){
        const c = document.createElement('div');
        c.className = 'b-stage'; c.textContent = cb.text;
        det.appendChild(c);
      }
      scroll.appendChild(det);
    } else if (block.t === 'say'){"""
anchor = "    } else if (block.t === 'say'){"
if "block.t === 'fold'" not in html:
    n = html.count(anchor)
    if n != 1:
        log.append('!!! render anchor count=%d (skipped)' % n)
    else:
        html = html.replace(anchor, fold_render, 1)
        log.append('fold render inserted')
else:
    log.append('fold render already present')

open(path, 'w', encoding='utf-8').write(html)
open('_html_log.txt', 'w', encoding='utf-8').write('\n'.join(log) + '\n')
