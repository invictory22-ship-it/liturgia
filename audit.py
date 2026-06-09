# -*- coding: utf-8 -*-
"""ДАТЧИК повноти свят (не блокує коміт — лише звіт).
Проходить FEASTS у liturgy-data.js і шукає прогалини:
  A) прокимен/алилуарій/прокимен на утрені має text, але БЕЗ стиха — це завжди помилка;
  B) свято без раннього (matins) прокимна / утреннього Євангелія — може бути нормою
     (залежить від рангу свята), показуємо для звірки.
Запуск:  python audit.py
"""
import re, json, sys
sys.stdout.reconfigure(encoding='utf-8')

txt = open('liturgy-data.js', encoding='utf-8').read()
m = re.search(r'const FEASTS = (\[[\s\S]*?\n\]);', txt)
feasts = json.loads(m.group(1))

def has_stih(o):
    return bool(o.get('stih', '').strip())

def prok_items(f, key):
    """prokLiturgy/prokMatins можуть бути списком {glas,text,stih} або одним об'єктом."""
    v = f.get(key)
    if not v: return []
    return v if isinstance(v, list) else [v]

# Ранги, що МАЮТЬ свій ранній прокимен + утреннє Євангеліє (полієлей і вище).
# Нижчі (славослів’я/шестерична/повсякденна) свого раннього прокимна не мають — це норма.
RANK_HAS_MATINS = {'пасхальна', 'дванадесяте', 'бдіння', 'полієлей'}
KNOWN_RANKS = RANK_HAS_MATINS | {'славослів’я', 'шестерична', 'повсякденна',
                                 'заупокійна', 'великопостова'}

no_stih = []     # A: text є, стиха нема
no_matins = []   # B: ранг вимагає раннього прокимна, а його нема
no_rank = []     # C: немає поля rank (або невідоме значення)

for f in feasts:
    name = f.get('name', '?')
    date = f.get('dateLabel', f.get('date', ''))
    rank = f.get('rank')
    # A) перевіряємо всі прокимни/алилуарій на стих
    for key in ('prokMatins', 'prokLiturgy', 'alleluia'):
        for it in prok_items(f, key):
            if it.get('text', '').strip() and not has_stih(it):
                lbl = it.get('label', '')
                no_stih.append('%s (%s) — %s%s: стих ВІДСУТНІЙ' %
                               (name, date, key, (' [%s]' % lbl) if lbl else ''))
    # C) ранг
    if not rank or rank not in KNOWN_RANKS:
        no_rank.append('%s (%s) — rank=%r' % (name, date, rank))
    # B) ранній прокимен — лише якщо ранг його вимагає
    ch = f.get('chytannia', {}) or {}
    has_mp = bool(prok_items(f, 'prokMatins'))
    has_mg = bool(ch.get('matinsGospel'))
    if rank in RANK_HAS_MATINS and not has_mp:
        no_matins.append('%s (%s) [%s]%s' %
                         (name, date, rank, '' if has_mg else ' — і без утр. Єв.'))

print('=' * 70)
print('A) ПРОКИМЕН/АЛИЛУАРІЙ БЕЗ СТИХА (завжди треба виправити): %d' % len(no_stih))
print('=' * 70)
for s in no_stih: print('  X ' + s)
print()
print('=' * 70)
print('B) ПОЛІЄЛЕЙ/БДІННЯ БЕЗ РАННЬОГО ПРОКИМНА (прогалина): %d' % len(no_matins))
print('=' * 70)
for s in no_matins: print('  ? ' + s)
print()
print('=' * 70)
print('C) БЕЗ ПОЛЯ rank або невідомий ранг: %d' % len(no_rank))
print('=' * 70)
for s in no_rank: print('  ! ' + s)
print()
print('РАЗОМ свят у FEASTS: %d' % len(feasts))
