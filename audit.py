# -*- coding: utf-8 -*-
"""ДАТЧИК повноти свят (не блокує коміт — лише звіт).
Проходить FEASTS у data-dovidnyk.js і шукає прогалини:
  A) прокимен/алилуарій/прокимен на утрені має text, але БЕЗ стиха — це завжди помилка;
  B) свято без раннього (matins) прокимна / утреннього Євангелія — може бути нормою
     (залежить від рангу свята), показуємо для звірки.
Запуск:  python audit.py
"""
import re, json, sys
sys.stdout.reconfigure(encoding='utf-8')

txt = open('data-dovidnyk.js', encoding='utf-8').read()
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
                                 'заупокійна', 'великопостова', 'неділя'}

no_stih = []     # A: text є, стиха нема
no_matins = []   # B: ранг вимагає раннього прокимна, а його нема
no_rank = []     # C: немає поля rank (або невідоме значення)
incomplete = []  # D: неповний літургійний набір (прокимен/алилуарій/причасний)

for f in feasts:
    name = f.get('name', '?')
    date = f.get('dateLabel', f.get('date', ''))
    rank = f.get('rank')
    # A) перевіряємо прокимни/алилуарій на стих. ВАЖЛИВО: у з'єднаній службі
    #    (свято+святий) лише ПЕРШИЙ прокимен/алилуарій має стих, а 2-й (і далі)
    #    співається БЕЗ стиха — тож перевіряємо тільки items[0].
    for key in ('prokMatins', 'prokLiturgy', 'alleluia'):
        items = prok_items(f, key)
        for idx, it in enumerate(items):
            if idx > 0:
                continue  # 2-й+ прокимен/алилуарій — без стиха норма
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
    # D) повнота ЛІТУРГІЙНОГО набору: кожне свято на Літургії має
    #    прокимен + алилуарій + причасний. Якщо хоч одне є, мусять бути всі три.
    triad = {'prokLiturgy': bool(prok_items(f, 'prokLiturgy')),
             'alleluia':    bool(prok_items(f, 'alleluia')),
             'prychasen':   bool(f.get('prychasen'))}
    if any(triad.values()) and not all(triad.values()):
        missing = [k for k, v in triad.items() if not v]
        incomplete.append('%s (%s) — БРАКУЄ: %s' % (name, date, ', '.join(missing)))

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
print('=' * 70)
print('D) НЕПОВНИЙ ЛІТУРГІЙНИЙ НАБІР (прокимен/алилуарій/причасний): %d' % len(incomplete))
print('=' * 70)
for s in incomplete: print('  # ' + s)
print()
print('РАЗОМ свят у FEASTS: %d' % len(feasts))
