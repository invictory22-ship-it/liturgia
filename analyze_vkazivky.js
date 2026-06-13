// Аналізатор «Богослужбових вказівок»: шукає СТРУКТУРНІ збої, які важко вловити очима
// на 365 днях. Запуск: node analyze_vkazivky.js [рік]  (за замовч. 2026).
// НЕ змінює дані — лише друкує звіт. Гнати щороку після генерації нового data-vkazivky-РІК.js.
//
// Що ловить:
//  1) ЗЛИПЛІ СЛУЖБИ — у тілі однієї секції сидить заголовок ІНШОЇ служби (парсер не розділив):
//     напр. «…Євангеліє – дня. Б. НА ВЕЧІРНІ…» або «…ЧАСАХ… ЛІТУРГІЯ свт. …». Це треба різати
//     на окремі акордеони (еталон — 03-07: ЧАСАХ + ЛІТУРГІЇ окремо).
//  2) ОДНА СЕКЦІЯ, ДУЖЕ ДОВГА — підозра на цілий нерозділений день (Страсні/пісні: 04-06, 04-08).
//  3) ВИНОСКИ [N] — скільки на день (де їх багато, варто причесати показ приміток у блоках).
const fs = require('fs');
const YEAR = process.argv[2] || '2026';
const FILE = 'data-vkazivky-' + YEAR + '.js';
const VAR = 'VKAZIVKY_' + YEAR;
const A = new Function(fs.readFileSync(FILE, 'utf8') + '\nreturn ' + VAR + ';')();

const SVCWORD = 'ВЕЧІРНІ|МАЛІЙ ВЕЧІРНІ|ВЕЛИКІЙ ВЕЧІРНІ|ПОВСЯКДЕННІЙ ВЕЧІРНІ|РАННІЙ|УТРЕНІ|ЧАСАХ|ЗОБРАЖАЛЬНИХ|ПОВЕЧІР|ПОЛУНОШНИЦІ|ЛІТУРГІЇ';
const INNER = new RegExp('[.»)\\]]\\s+(?:НА\\s+(?:' + SVCWORD + ')|ВЕЧІРНЯ\\s+з\\s+Літург|ЛІТУРГІЯ\\s+(?:за\\s+чином|свт\\.|Раніш|Передосв)|ЗОБРАЖАЛЬНІ\\b|УТРЕНЯ\\b|ВЕЛИКЕ\\s+ПОВЕЧІР)', 'g');

const merged = [], inNotes = [], longOne = [], foot = [];
for (const d of A){
  for (const s of (d.sections || [])){
    const body = s.text.replace(new RegExp('^(?:НА|На)\\s+' + s.svc + '\\s*'), '');
    const hits = body.match(INNER);
    if (hits) merged.push({date: d.date, svc: s.svc, len: s.text.length, inner: [...new Set(hits.map(x => x.trim()))]});
  }
  // СЛУЖБИ, ЗАХОВАНІ В notes (простирадло замість примітки) — напр. 03-07: повечір'я/рання в notes
  if (d.notes){
    const nh = d.notes.match(INNER);
    if (nh || d.notes.length > 1500) inNotes.push({date: d.date, len: d.notes.length, inner: nh ? [...new Set(nh.map(x => x.trim()))] : []});
  }
  if ((d.sections || []).length === 1 && d.sections[0].text.length > 3000)
    longOne.push({date: d.date, len: d.sections[0].text.length});
  const allText = (d.notes || '') + ' ' + (d.sections || []).map(s => s.text).join(' ');
  const fns = allText.match(/\[[0-9]{1,2}\]/g);
  if (fns) foot.push({date: d.date, n: fns.length});
}
console.log('Аналіз ' + FILE + ' — ' + A.length + ' днів\n');
console.log('═══ 1. ЗЛИПЛІ СЛУЖБИ (різати на акордеони) : ' + merged.length + ' ═══');
for (const m of merged) console.log('  ' + m.date + ' [' + m.svc + '] len=' + m.len + ' → ' + m.inner.join(' | '));
console.log('\n═══ 1б. СЛУЖБИ/ПРОСТИРАДЛО В notes (примітка >1500 або із заголовком служби) : ' + inNotes.length + ' ═══');
for (const m of inNotes) console.log('  ' + m.date + ' notes=' + m.len + (m.inner.length ? ' → ' + m.inner.join(' | ') : ' (довга примітка)'));
console.log('\n═══ 2. ОДНА СЕКЦІЯ, текст >3000 (нерозділений день) : ' + longOne.length + ' ═══');
for (const m of longOne) console.log('  ' + m.date + ' len=' + m.len);
console.log('\n═══ 3. Дні з виносками [N] : ' + foot.length + ' (маркерів ' + foot.reduce((a, b) => a + b.n, 0) + ') ═══');
console.log('  ' + foot.map(x => x.date + '(' + x.n + ')').join(', '));
