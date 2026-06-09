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

no_stih = []     # A: text є, стиха нема
no_matins = []   # B: нема раннього прокимна/Євангелія

for f in feasts:
    name = f.get('name', '?')
    date = f.get('dateLabel', f.get('date', ''))
    # A) перевіряємо всі прокимни/алилуарій на стих
    for key in ('prokMatins', 'prokLiturgy', 'alleluia'):
        for it in prok_items(f, key):
            if it.get('text', '').strip() and not has_stih(it):
                lbl = it.get('label', '')
                no_stih.append('%s (%s) — %s%s: стих ВІДСУТНІЙ' %
                               (name, date, key, (' [%s]' % lbl) if lbl else ''))
    # B) ранній прокимен / утреннє Євангеліє
    ch = f.get('chytannia', {}) or {}
    has_mp = bool(prok_items(f, 'prokMatins'))
    has_mg = bool(ch.get('matinsGospel'))
    if not has_mp and not has_mg:
        no_matins.append('%s (%s)' % (name, date))

print('=' * 70)
print('A) ПРОКИМЕН/АЛИЛУАРІЙ БЕЗ СТИХА (завжди треба виправити): %d' % len(no_stih))
print('=' * 70)
for s in no_stih: print('  ✗ ' + s)
print()
print('=' * 70)
print('B) БЕЗ РАННЬОГО ПРОКИМНА/УТРЕННЬОГО ЄВАНГЕЛІЯ: %d' % len(no_matins))
print('   (норма для нижчих рангів; для Полієлей/Бдіння — прогалина)')
print('=' * 70)
for s in no_matins: print('  ? ' + s)
print()
print('РАЗОМ свят у FEASTS: %d' % len(feasts))
