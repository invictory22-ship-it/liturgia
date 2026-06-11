# -*- coding: utf-8 -*-
"""Build-скрипт: «Богослужбові вказівки» (txt з офіційного PDF) → data-vkazivky-РІК.js.
Структурує по днях: шапка (свято/глас/святі/зачала/примітки) + секції служб
(На вечірні / На ранній / На часах / На Літургії …). Текст слово в слово; прибираємо
лише переноси PDF і ріжемо на блоки за заголовками ВЕЛИКИМИ.

ЩОРОКУ: поклади новий txt у pdf/_vkazivky-РІК.txt, постав YEAR нижче, запусти
`python parse_vkazivky.py` → отримаєш data-vkazivky-РІК.js. Тоді в index.html
(ensureVkazivky) онови назву файла й змінну VKAZIVKY_РІК. Запуск з 'sample'/'stats'
для перевірки без запису файла."""
import io, re, json, sys
sys.stdout.reconfigure(encoding='utf-8')

YEAR = 2026
SRC = 'pdf/_vkazivky-%d.txt' % YEAR
MON = {'СІЧНЯ':1,'ЛЮТОГО':2,'БЕРЕЗНЯ':3,'КВІТНЯ':4,'ТРАВНЯ':5,'ЧЕРВНЯ':6,
       'ЛИПНЯ':7,'СЕРПНЯ':8,'ВЕРЕСНЯ':9,'ЖОВТНЯ':10,'ЛИСТОПАДА':11,'ГРУДНЯ':12}

# Заголовки служб (регістр «НА»/«На»; службове слово ВЕЛИКИМИ).
SERVICES = (r"ВЕЛИКІЙ ВЕЧІРНІ|МАЛІЙ ВЕЧІРНІ|ПОВСЯКДЕННІЙ ВЕЧІРНІ|"
            r"ВЕЧІРНІ ІЗ ЛІТУРГІЄЮ|ВЕЧІРНІ|ВЕЛИКОМУ ПОВЕЧІР’Ї|МАЛОМУ ПОВЕЧІР’Ї|"
            r"ПОВЕЧІР’Ї|ПОЛУНОШНИЦІ|РАННІЙ|УТРЕНІ|ЧАСАХ|ЗОБРАЖАЛЬНИХ|ЛІТУРГІЇ")
SEC_RE = re.compile(r'^(?:НА|На)\s+(' + SERVICES + r')\b')

# Колонтитули сторінок PDF (інтерлайн від pdftotext): назва видання, ВЕЛИКІ-місяці,
# голі номери сторінок. Засмічують текст і РОЗРИВАЮТЬ блоки (напр. «Порядок читань»
# на 14/19.06 → зачала з'їжджали в notes). Прибираємо ЦІЛИМИ рядками ДО склейки.
# Колонтитульні токени (місяць, видання, видавець). Інколи pdftotext зліплює їх
# разом + form-feed (\x0c): «\x0cЧЕРВЕНЬ Богослужбові вказівки 2026». Тому рядок —
# колонтитул, якщо ПІСЛЯ вирізання всіх цих токенів від нього лишається порожньо/цифри.
INLINE_JUNK = re.compile(r'\s*(?:Православна Церква України|Богослужбові вказівки \d{4}|'
                         r'СІЧЕНЬ|ЛЮТИЙ|БЕРЕЗЕНЬ|КВІТЕНЬ|ТРАВЕНЬ|ЧЕРВЕНЬ|ЛИПЕНЬ|СЕРПЕНЬ|'
                         r'ВЕРЕСЕНЬ|ЖОВТЕНЬ|ЛИСТОПАД|ГРУДЕНЬ)\s*')

def strip_colontitul(seg):
    out = []
    for ln in seg.split('\n'):
        s = ln.replace('\x0c', '').strip()
        rest = INLINE_JUNK.sub(' ', s).strip()
        if rest == '' or re.fullmatch(r'\d{1,4}', rest):
            continue        # суцільний колонтитул (місяць/видання/номер) — викинути
        out.append(ln)
    return '\n'.join(out)

def dehyph(s):
    s = re.sub(r'­\n?', '', s)       # м'який перенос U+00AD (+ перенос рядка)
    s = re.sub(r'([а-яіїєґ])-\n([а-яіїєґ])', r'\1\2', s)  # перенос слова дефісом
    return s

def join_lines(lines):
    s = INLINE_JUNK.sub(' ', ' '.join(lines))
    return re.sub(r'\s+', ' ', s).strip()

def parse_day(seg):
    seg = strip_colontitul(seg)   # ДО dehyph: колонтитули рвуть слова й блоки
    seg = dehyph(seg)
    lines = [ln.strip() for ln in seg.split('\n') if ln.strip()]
    m0 = re.match(r'(\d{1,2})([А-ЯІЇЄҐ]+),', lines[0])
    day, mon = int(m0.group(1)), MON[m0.group(2)]
    weekday = lines[1]
    rest = lines[2:]

    sec_start = next((i for i, ln in enumerate(rest) if SEC_RE.match(ln)), len(rest))
    head = rest[:sec_start]
    secs_lines = rest[sec_start:]

    title_lines, readings = [], []
    i = 0
    while i < len(head) and not head[i].startswith('Порядок читань'):
        title_lines.append(head[i]); i += 1
    if i < len(head):
        i += 1
        while i < len(head) and ('зач.' in head[i] or re.match(r'(Ран\.|Літ\.|Утр\.|Веч\.|Апп\.:|Лит)', head[i])):
            readings.append(head[i]); i += 1
    notes = head[i:]

    glas = None
    mg = re.search(r'Глас\s+(\d+)', ' '.join(title_lines))
    if mg: glas = int(mg.group(1))

    sections, cur = [], None
    for ln in secs_lines:
        mh = SEC_RE.match(ln)
        if mh:
            if cur: sections.append(cur)
            cur = {'svc': mh.group(1), 'lines': [ln]}
        elif cur:
            cur['lines'].append(ln)
    if cur: sections.append(cur)
    for s in sections:
        s['text'] = join_lines(s['lines']); del s['lines']

    rec = {'date': '%02d-%02d' % (mon, day), 'weekday': weekday,
           'title': join_lines(title_lines)}
    if glas: rec['glas'] = glas
    if readings: rec['readings'] = [join_lines([r]) for r in readings]
    if notes: rec['notes'] = join_lines(notes)
    rec['sections'] = sections
    if not sections:   # особливі дні (Страсний/Пасха/Благовіщення) — інший формат чину
        rec['special'] = True
    return rec

def main():
    t = io.open(SRC, encoding='utf-8').read()
    pat = re.compile(r'\n(\d{1,2})([А-ЯІЇЄҐ]+),\s*\n')
    ms = list(pat.finditer(t))
    days = [parse_day(t[m.start():(ms[i+1].start() if i+1 < len(ms) else m.start()+6000)])
            for i, m in enumerate(ms)]

    arg = sys.argv[1] if len(sys.argv) > 1 else ''
    if arg == 'stats':
        from collections import Counter
        print('днів:', len(days), '| унікальних:', len(set(d['date'] for d in days)))
        print('секцій/день:', sorted(Counter(len(d['sections']) for d in days).items()))
        print('особливі:', [d['date'] for d in days if d.get('special')])
        return
    if arg == 'sample':
        for d in days:
            if d['date'] in ('06-11', '06-16', '06-07'):
                print(json.dumps(d, ensure_ascii=False, indent=1))
        return

    out = 'data-vkazivky-%d.js' % YEAR
    hdr = ('// БОГОСЛУЖБОВІ ВКАЗІВКИ ПЦУ %d — структуровано по днях з офіційного видання.\n'
           '// Генерує parse_vkazivky.py. Текст слово в слово; прибрано лише переноси PDF.\n'
           '// Поля: date(MM-DD), weekday, title, glas?, readings?[], notes?, sections[{svc,text}].\n'
           '// Файл РІЧНИЙ — на новий рік згенеруй новий і онови ensureVkazivky() в index.html.\n' % YEAR)
    body = ',\n'.join(json.dumps(d, ensure_ascii=False, separators=(',', ':')) for d in days)
    io.open(out, 'w', encoding='utf-8', newline='').write(
        hdr + 'const VKAZIVKY_%d = [\n' % YEAR + body + '\n];\n')
    print('Записано %s: %d днів' % (out, len(days)))

main()
