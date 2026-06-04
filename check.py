# -*- coding: utf-8 -*-
"""Перевірка цілісності перед комітом:
 - liturgy-data.js: валідний JSON (немає зайвих/відсутніх ком),
 - index.html: збалансовані дужки в <script>.
Викликається git-гачком pre-commit. Якщо щось не так — коміт скасовується."""
import re, json, sys

errors = []

# 1) liturgy-data.js — два масиви: BLOCKS (текст служби) і FEASTS (словник свят).
# Кожен масив закінчується рядком, що починається з "];" — нежадібно беремо до нього.
try:
    txt = open('liturgy-data.js', encoding='utf-8').read()

    # --- BLOCKS (обов'язковий) ---
    m = re.search(r'const BLOCKS = (\[[\s\S]*?\n\]);', txt)
    if not m:
        errors.append('liturgy-data.js: не знайдено const BLOCKS = [...]')
    else:
        blocks = json.loads(m.group(1))
        for i, b in enumerate(blocks):
            if 't' not in b or 'text' not in b:
                errors.append('liturgy-data.js: блок #%d без t/text' % i)
                break

    # --- FEASTS (необов'язковий словник свят) ---
    mf = re.search(r'const FEASTS = (\[[\s\S]*?\n\]);', txt)
    if mf:
        feasts = json.loads(mf.group(1))
        for i, f in enumerate(feasts):
            if 'name' not in f:
                errors.append('liturgy-data.js: свято #%d без name' % i)
                break

    # --- PASKY та інші служби (масиви блоків, як BLOCKS) ---
    for name in ('PASKY',):
        ms = re.search(r'const %s = (\[[\s\S]*?\n\]);' % name, txt)
        if ms:
            blk = json.loads(ms.group(1))
            for i, b in enumerate(blk):
                if 't' not in b or 'text' not in b:
                    errors.append('liturgy-data.js: %s блок #%d без t/text' % (name, i))
                    break
except json.JSONDecodeError as e:
    errors.append('liturgy-data.js: ПОМИЛКА JSON (мабуть зайва/відсутня кома) - рядок %d' % e.lineno)
except FileNotFoundError:
    pass

# 2) index.html — баланс дужок у script (повний прохід зі станами рядків)
try:
    h = open('index.html', encoding='utf-8').read()
    js = ''.join(re.findall(r'<script>(.*?)</script>', h, re.S))
    depth = {'{': 0, '(': 0, '[': 0}
    pairs = {'}': '{', ')': '(', ']': '['}
    i, n, state, prev = 0, len(js), 'code', ''
    while i < n:
        ch = js[i]; nxt = js[i+1] if i+1 < n else ''
        if state == 'code':
            if ch == '/' and nxt == '/': state = 'lc'; i += 2; continue
            if ch == '/' and nxt == '*': state = 'bc'; i += 2; continue
            if ch == '"': state = 'dq'; i += 1; continue
            if ch == "'": state = 'sq'; i += 1; continue
            if ch == '`': state = 'tq'; i += 1; continue
            if ch == '/' and prev in '=(,:[!&|?{;': state = 're'; i += 1; continue
            if ch in '{([': depth[ch] += 1
            elif ch in '})]':
                o = pairs[ch]; depth[o] -= 1
            if not ch.isspace(): prev = ch
            i += 1
        elif state == 'lc':
            if ch == '\n': state = 'code'
            i += 1
        elif state == 'bc':
            if ch == '*' and nxt == '/': state = 'code'; i += 2; continue
            i += 1
        elif state in ('dq', 'sq', 'tq', 're'):
            q = {'dq': '"', 'sq': "'", 'tq': '`', 're': '/'}[state]
            if ch == '\\': i += 2; continue
            if ch == q: state = 'code'
            i += 1
    if any(v != 0 for v in depth.values()):
        errors.append('index.html: незбалансовані дужки у script %s' % depth)
except FileNotFoundError:
    pass

if errors:
    sys.stderr.write('\n!!! ПЕРЕВІРКА НЕ ПРОЙДЕНА — коміт скасовано:\n')
    for e in errors:
        sys.stderr.write('   - ' + e + '\n')
    sys.stderr.write('Виправ помилку (або поклич Claude) і спробуй ще раз.\n\n')
    sys.exit(1)

print('Перевірка OK: liturgy-data.js валідний, index.html збалансований.')
sys.exit(0)
