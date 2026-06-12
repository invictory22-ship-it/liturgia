# -*- coding: utf-8 -*-
"""Перевірка цілісності перед комітом:
 - liturgy-data.js і data-dovidnyk.js: валідний JSON (немає зайвих/відсутніх ком),
 - index.html: збалансовані дужки в <script>.
Викликається git-гачком pre-commit. Якщо щось не так — коміт скасовується."""
import re, json, sys, glob

errors = []

def load(fname):
    try:
        return open(fname, encoding='utf-8').read()
    except FileNotFoundError:
        return None

def find_const(txt, name):
    m = re.search(r'const %s = (\[[\s\S]*?\n\]);' % name, txt)
    return m.group(1) if m else None

FRAG_IDS = set()  # заповнюється з const FRAGMENTS

def check_block(fname, name, i, b):
    """Один блок: include мусить мати відомий id, решта — t і text."""
    if b.get('t') == 'include':
        if b.get('id') not in FRAG_IDS:
            errors.append('%s: %s блок #%d — include з невідомим id %r' % (fname, name, i, b.get('id')))
            return False
        return True
    if 't' not in b or 'text' not in b:
        errors.append('%s: %s блок #%d без t/text' % (fname, name, i))
        return False
    return True

def check_blocks_array(fname, txt, name, required=False):
    """Масив блоків служби: кожен елемент має t і text (або include з відомим id)."""
    src = find_const(txt, name)
    if src is None:
        if required:
            errors.append('%s: не знайдено const %s = [...]' % (fname, name))
        return
    for i, b in enumerate(json.loads(src)):
        if not check_block(fname, name, i, b):
            break

def check_records(fname, txt, name, fields):
    """Масив записів довідника: кожен елемент має вказані поля."""
    src = find_const(txt, name)
    if src is None:
        return
    for i, r in enumerate(json.loads(src)):
        if any(k not in r for k in fields):
            errors.append('%s: %s #%d без %s' % (fname, name, i, '/'.join(fields)))
            break

# 1) Дані служб у кількох файлах. ПОРЯДОК ВАЖЛИВИЙ: спершу FRAGMENTS (заповнює FRAG_IDS),
#    бо служби містять include, що мусять посилатися на відомий id.
# 1a) liturgy-fragments.js — бібліотека ектеній (FRAGMENTS) + реєстр служб
ftxt = load('liturgy-fragments.js')
if ftxt is not None:
    try:
        mfr = re.search(r'const FRAGMENTS = (\{[\s\S]*?\n\});', ftxt)
        if mfr:
            fragments = json.loads(mfr.group(1))
            FRAG_IDS.update(fragments.keys())
            for fid, blocks in fragments.items():
                for i, b in enumerate(blocks):
                    if not check_block('liturgy-fragments.js', 'FRAGMENTS[%s]' % fid, i, b):
                        break
        else:
            errors.append('liturgy-fragments.js: не знайдено const FRAGMENTS = {...}')
    except json.JSONDecodeError as e:
        errors.append('liturgy-fragments.js: ПОМИЛКА JSON (мабуть зайва/відсутня кома) - рядок %d' % e.lineno)

# 1b) liturgy-data.js — головна Літургія (BLOCKS обов'язковий)
txt = load('liturgy-data.js')
if txt is not None:
    try:
        check_blocks_array('liturgy-data.js', txt, 'BLOCKS', required=True)
    except json.JSONDecodeError as e:
        errors.append('liturgy-data.js: ПОМИЛКА JSON (мабуть зайва/відсутня кома) - рядок %d' % e.lineno)

# 1c) svc-*.js — окремі служби (пасхальні, у майбутньому вечірня/рання/всенічна…).
#     Кожен const NAME = [...] — масив блоків служби; auto-покриває нові файли.
for sf in sorted(glob.glob('svc-*.js')):
    stxt = load(sf)
    if stxt is None:
        continue
    try:
        for name in re.findall(r'^const (\w+) = \[', stxt, re.M):
            check_blocks_array(sf, stxt, name)
    except json.JSONDecodeError as e:
        errors.append('%s: ПОМИЛКА JSON (мабуть зайва/відсутня кома) - рядок %d' % (sf, e.lineno))

# 2) data-dovidnyk.js — довідник «На весь рік»
dtxt = load('data-dovidnyk.js')
if dtxt is not None:
    try:
        if find_const(dtxt, 'FEASTS') is None:
            errors.append('data-dovidnyk.js: не знайдено const FEASTS = [...]')
        check_records('data-dovidnyk.js', dtxt, 'FEASTS', ('name',))
        check_records('data-dovidnyk.js', dtxt, 'GLASI', ('glas',))
        check_records('data-dovidnyk.js', dtxt, 'DENNI', ('day', 'rows'))
        check_records('data-dovidnyk.js', dtxt, 'ZAHALNI', ('chyn',))
    except json.JSONDecodeError as e:
        errors.append('data-dovidnyk.js: ПОМИЛКА JSON (мабуть зайва/відсутня кома) - рядок %d' % e.lineno)

# 3) data-vkazivky-РІК.js — богослужбові вказівки по днях (необов'язкові, річні файли)
for vf in glob.glob('data-vkazivky-*.js'):
    vtxt = load(vf)
    if vtxt is None:
        continue
    try:
        mv = re.search(r'const VKAZIVKY_\d+ = (\[[\s\S]*\n\]);', vtxt)
        if not mv:
            errors.append('%s: не знайдено const VKAZIVKY_РІК = [...]' % vf)
        else:
            days = json.loads(mv.group(1))
            for i, d in enumerate(days):
                if 'date' not in d or 'sections' not in d:
                    errors.append('%s: день #%d без date/sections' % (vf, i)); break
    except json.JSONDecodeError as e:
        errors.append('%s: ПОМИЛКА JSON - рядок %d' % (vf, e.lineno))

# 4) index.html — баланс дужок у script (повний прохід зі станами рядків)
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

print('Перевірка OK: liturgy-fragments.js, liturgy-data.js, svc-*.js, data-dovidnyk.js валідні, index.html збалансований.')
sys.exit(0)
