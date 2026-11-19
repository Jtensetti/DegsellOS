'use strict';
// Testar arbetsmetoden: faskrav, granskning, mått och AI-konsultationer.
// Rena funktioner, ingen Obsidian behövs.
const assert = require('node:assert/strict');
const Module = require('node:module');

const orig = Module._load;
Module._load = function (request, ...rest) {
  if (request === 'obsidian') return { Plugin: class {}, ItemView: class {}, Notice: class {}, Modal: class {} };
  return orig.call(this, request, ...rest);
};
const { engine: e } = require('../vault/.obsidian/plugins/forskaros-core/main.js');
Module._load = orig;

const DAY = '2026-11-17';
const note = (path, fm, body = '') => ({ path, fm, body, created: fm.datum || DAY });
const Q = 'Q.md';
const link = '[[Q]]';
let n = 0;
const test = (name, fn) => { fn(); n++; };

test('cykeln har sju faser och börjar om efter Dela', () => {
  assert.deepEqual(e.PHASES.map(p => p.id), ['utforska', 'kombinera', 'välj', 'pröva', 'utveckla', 'ompröva', 'dela']);
  assert.equal(e.nextPhase('dela').id, 'utforska');
  assert.equal(e.nextPhase('pröva').id, 'utveckla');
});

test('länkar tolkas med och utan sökväg, alias och .md', () => {
  assert.equal(e.linkTarget('[[01 RIKTNING/Fråga|kort]]'), '01 RIKTNING/Fråga');
  assert.equal(e.linkTarget('Fråga.md'), 'Fråga');
  assert(e.refersTo(note('x.md', { fråga: '[[01 RIKTNING/Min fråga]]' }), note('01 RIKTNING/Min fråga.md', {})));
  assert(e.refersTo(note('x.md', { fråga: '[[Min fråga]]' }), note('01 RIKTNING/Min fråga.md', {})));
  assert(!e.refersTo(note('x.md', {}), note('Q.md', {})));
});

test('mallens stödstruktur räknas inte som egna ord', () => {
  const tom = e.TYPES.pass.render({ date: DAY });
  assert.equal(e.ownWords(tom), 0, 'en tom mall ska ha noll egna ord');
  const ifylld = tom.replace('## 2. Min egen förklaring – utan AI\n', '## 2. Min egen förklaring – utan AI\nJag tror att AI försvagar tänkandet när den används innan man själv har försökt.\n');
  assert.equal(e.ownWords(ifylld), 14);
  for (const [type, spec] of Object.entries(e.TYPES)) {
    assert.equal(e.ownWords(spec.render({ date: DAY })), 0, `mallen ${type} ska vara tom`);
  }
});

test('section hittar text under rubrik och ignorerar mallrader', () => {
  const body = '# T\n## Falsifiering: vad?\n\n## Prediktioner\n1.\n2. Fler fel med AI\n## Nästa\nx';
  assert.equal(e.section(body, 'Falsifiering'), '');
  assert.equal(e.section(body, 'Prediktioner'), '2. Fler fel med AI');
});

const MOTIVERING = 'Frågan avgör om skolor ska använda AI som stöd för skrivande eller inte, och hur. Det berör hundratusentals elever och lärare varje år, och dagens beslut fattas nästan helt utan forskning om långsiktiga effekter.';
const fyllKarta = (rader) => e.TYPES.diversity.render({ date: DAY })
  .replace('| Kognitionsvetenskap | | | |', rader >= 1 ? '| Kognitionsvetenskap | Avlastning | Motivation | Risko |' : '| Kognitionsvetenskap | | | |')
  .replace('| Teknik / datavetenskap | | | |', rader >= 2 ? '| Teknik / datavetenskap | Verktyg | Lärande | ACM |' : '| Teknik / datavetenskap | | | |')
  .replace('| Oväntat fält | | | |', rader >= 3 ? '| Oväntat fält | Idrottens träningslära | Kontext | Ericsson |' : '| Oväntat fält | | | |')
  .replace('## Där perspektiven motsäger varandra\n', '## Där perspektiven motsäger varandra\nAvlastning hjälper i stunden men inte på sikt.\n');

test('faskrav: Utforska kräver motivering och en riktig perspektivkarta', () => {
  const q = note(Q, { typ: 'forskningsfråga', fas: 'utforska' }, e.questionNote({ date: DAY, titel: 'Q', varför: 'Kort.' }));
  assert.deepEqual(e.phaseRequirements(q, [q]).map(r => r.ok), [false, false, false, false, false, false]);
  const q2 = note(Q, q.fm, e.questionNote({ date: DAY, titel: 'Q', varför: MOTIVERING })
    .replace('-\n-\n-\n', '- Varför glömmer elever?\n- Gäller det vuxna?\n- Spelar uppgiften roll?\n')
    .replace('## Vem bryr sig om svaret?\n> Vilka människor eller verksamheter har nytta av svaret, utanför ditt eget fält?\n',
      '## Vem bryr sig om svaret?\n> Vilka människor eller verksamheter har nytta av svaret, utanför ditt eget fält?\nLärare och skolhuvudmän.\n'));
  const tvåFrågor = note(Q, q.fm, q2.body.replace('- Spelar uppgiften roll?\n', '-\n'));
  assert.equal(e.phaseRequirements(tvåFrågor, [])[1].ok, false, 'två saker att undra över räcker inte');
  const tom = note('k.md', { typ: 'perspektivkarta', fråga: link }, e.TYPES.diversity.render({ date: DAY }));
  assert.deepEqual(e.phaseRequirements(q2, [q2, tom]).map(r => r.ok), [true, true, true, false, false, false], 'en tom karta räknas inte');
  const två = note('k.md', { typ: 'perspektivkarta', fråga: link }, fyllKarta(2));
  assert.deepEqual(e.phaseRequirements(q2, [q2, två]).map(r => r.ok), [true, true, true, false, false, true]);
  const full = note('k.md', { typ: 'perspektivkarta', fråga: link }, fyllKarta(3));
  assert.deepEqual(e.phaseRequirements(q2, [q2, full]).map(r => r.ok), [true, true, true, true, true, true]);
});

test('faskrav: Kombinera kräver grund, det nya, ett utmanat antagande och vem som företräder det', () => {
  const q = note(Q, { typ: 'forskningsfråga', fas: 'kombinera' });
  const tom = note('h.md', { typ: 'hypotes', fråga: link }, e.TYPES.hypothesis.render({ date: DAY }));
  assert.deepEqual(e.phaseRequirements(q, [tom]).map(r => r.ok), [true, false, false, false, false]);
  const full = note('h.md', { typ: 'hypotes', fråga: link }, tom.body
    .replace('## Etablerad kunskap jag bygger på\n', '## Etablerad kunskap jag bygger på\nForskning om kognitiv avlastning.\n')
    .replace('## Den ovanliga kombinationen\n> Vilka fält, idéer eller metoder kombineras som sällan möts?\n',
      '## Den ovanliga kombinationen\n> Vilka fält, idéer eller metoder kombineras som sällan möts?\nSpråkdidaktik möter förvaltningsforskning.\n')
    .replace('## Vilket etablerat antagande utmanar hypotesen?\n', '## Vilket etablerat antagande utmanar hypotesen?\nAtt mer stöd alltid ger mer lärande.\n'));
  assert.deepEqual(e.phaseRequirements(q, [full]).map(r => r.ok), [true, true, true, true, false]);
  const företrädd = note('h.md', full.fm, full.body.replace(/(## Vem företräder antagandet i dag\?\n> .*\n)/, '$1Forskare i lärandeteknik.\n'));
  assert.deepEqual(e.phaseRequirements(q, [företrädd]).map(r => r.ok), [true, true, true, true, true]);
});

test('faskrav: Välj kräver konfidens och vad som förändras', () => {
  const body = e.questionNote({ date: DAY, titel: 'Q', varför: MOTIVERING })
    .replace('## Om frågan besvaras\n> Vad vet vi då som vi inte vet i dag, och vem har nytta av det?\n', '## Om frågan besvaras\n> Vad vet vi då som vi inte vet i dag, och vem har nytta av det?\nSkolor kan välja AI-stöd som bygger förmåga.\n')
    .replace('## Det jag väljer bort\n', '## Det jag väljer bort\nYngre barn.\n');
  const q = note(Q, { typ: 'forskningsfråga', fas: 'välj' }, body);
  const h = konfidens => note('h.md', { typ: 'hypotes', fråga: link, konfidens }, '## Falsifiering\nIngen skillnad.\n## Prediktioner\n1. Sämre utan AI.\n');
  assert.deepEqual(e.phaseRequirements(q, [h('okänd')]).map(r => r.ok), [true, true, false, true, true]);
  assert.deepEqual(e.phaseRequirements(q, [h('medel')]).map(r => r.ok), [true, true, true, true, true]);
});

test('faskrav: Pröva kräver besvarat motprov, en invändning från en människa och ett möte med den som företräder antagandet', () => {
  const q = note(Q, { typ: 'forskningsfråga', fas: 'pröva' });
  const motprov = note('m.md', { typ: 'motprov', fråga: link }, '## Mitt svar efter att ha övervägt invändningarna\nInvändningen håller delvis.');
  assert.deepEqual(e.phaseRequirements(q, [motprov]).map(r => r.ok), [true, false, false], 'AI-kritik räcker inte');
  const tomtMöte = note('mö.md', { typ: 'forskningsmöte', fråga: link }, e.TYPES.meeting.render({ date: DAY }));
  assert.deepEqual(e.phaseRequirements(q, [motprov, tomtMöte]).map(r => r.ok), [true, false, false], 'ett möte utan invändning räknas inte');
  const möte = note('mö.md', { typ: 'forskningsmöte', fråga: link }, '## Viktigaste invändningen jag fick\nUrvalet är för litet.\n');
  assert.deepEqual(e.phaseRequirements(q, [motprov, möte]).map(r => r.ok), [true, true, false]);
  const motpart = note('mö.md', { typ: 'forskningsmöte', fråga: link, företräder_antagandet: 'ja' }, möte.body);
  assert.deepEqual(e.phaseRequirements(q, [motprov, motpart]).map(r => r.ok), [true, true, true]);
});

test('faskrav: Dela kräver en sammanfattning på 50–200 ord och nästa fråga', () => {
  const ord = n => Array.from({ length: n }, (_, i) => `ord${i}`).join(' ');
  const q = n => note(Q, { typ: 'forskningsfråga', fas: 'dela' }, `## Sammanfattning för någon utanför fältet\n${ord(n)}\n## Delat med\nSeminariet.\n## Vilken fråga öppnar svaret?\nGäller det vuxna?\n`);
  assert.deepEqual(e.phaseRequirements(q(20), []).map(r => r.ok), [false, true, true]);
  assert.deepEqual(e.phaseRequirements(q(120), []).map(r => r.ok), [true, true, true]);
  assert.deepEqual(e.phaseRequirements(q(400), []).map(r => r.ok), [false, true, true]);
});

test('faskrav: Utveckla och Dela läser projekt från appen ForskarOS', () => {
  const projekt = (nivå, extra = '') => note('04 EXPERIMENT/Projekt.md',
    { typ: 'experiment', fråga: link, projekt: '/home/forskare/Forskningsprojekt/Studie', nivå }, `## Resultat\nRapporten är byggd.\n${extra}`);
  const utv = note(Q, { typ: 'forskningsfråga', fas: 'utveckla' }, '## Medarbetare\nAnna kodar intervjuerna.\n');
  assert.deepEqual(e.phaseRequirements(utv, [projekt('Dokumenterad')]).map(r => r.ok), [true, true], 'en körning i appen är ett experiment med resultat');
  const ensam = note(Q, { typ: 'forskningsfråga', fas: 'utveckla' });
  assert.equal(e.phaseRequirements(ensam, [projekt('Dokumenterad')])[1].ok, false, 'ingen medarbetare och inget samarbete');
  const samarbete = note('mö.md', { typ: 'forskningsmöte', fråga: link, form: 'samarbete' });
  assert.equal(e.phaseRequirements(ensam, [projekt('Dokumenterad'), samarbete])[1].ok, true);
  const dela = note(Q, { typ: 'forskningsfråga', fas: 'dela' });
  const sista = rs => rs[rs.length - 1];
  assert.equal(sista(e.phaseRequirements(dela, [projekt('Dokumenterad')])).ok, false, 'resultatet ska vara upprepat innan det delas');
  assert.equal(sista(e.phaseRequirements(dela, [projekt('Återkörd')])).ok, true);
  assert.equal(e.phaseRequirements(dela, []).length, 3, 'utan projekt i appen gäller inte kravet');
});

test('AI-stödet är frivilligt: av från början, handledning utan färdiga svar', () => {
  assert.equal(e.AI_STANDARD, 'av');
  assert.deepEqual(e.aiModes('av'), []);
  assert.deepEqual(e.aiModes('handledning'), ['utveckling', 'prövning']);
  assert.deepEqual(e.aiModes('fullt'), ['utveckling', 'prövning', 'prestation']);
  assert.deepEqual(e.aiModes('okänd'), [], 'okänd nivå betyder av');
  const ai = [1, 2, 3].map(i => note(`a${i}.md`, { typ: 'ai-konsultation', datum: DAY, egen_tanke_först: 'nej' }));
  assert(e.audit(ai, DAY, { ai: 'handledning' }).some(f => f.princip === 'AI-användning'));
  assert(!e.audit(ai, DAY, { ai: 'av' }).some(f => /AI/.test(f.princip)), 'avstängt AI nämns inte i granskningen');
});

test('appen och panelen pekar på varandra', () => {
  assert.equal(e.appUri('nytt-projekt', { fråga: '01 RIKTNING/Min fråga', hypotes: null }),
    'forskaros://nytt-projekt?fr%C3%A5ga=01+RIKTNING%2FMin+fr%C3%A5ga');
  const q = note(Q, { typ: 'forskningsfråga' });
  const egen = note('04 EXPERIMENT/Projekt A.md', { typ: 'experiment', fråga: link, projekt: '/p/A' });
  const annan = note('04 EXPERIMENT/Projekt B.md', { typ: 'experiment', fråga: '[[Annan]]', projekt: '/p/B' });
  const handskriven = note('04 EXPERIMENT/Försök.md', { typ: 'experiment', fråga: link });
  assert.deepEqual(e.projectsFor(q, [egen, annan, handskriven]).map(n => n.path), ['04 EXPERIMENT/Projekt A.md']);
});

test('granskning: påståenden att ompröva i appens projekt och möten bara med kärnan', () => {
  const projekt = note('04 EXPERIMENT/Projekt Studie.md', { typ: 'experiment', projekt: '/p', att_ompröva: 2 });
  assert(e.audit([projekt], DAY).some(f => f.princip === 'Påstående att ompröva' && f.text.startsWith('2 påståenden')));
  assert(!e.audit([note('x.md', { typ: 'experiment', projekt: '/p', att_ompröva: 0 })], DAY).some(f => f.princip === 'Påstående att ompröva'));
  const möten = krets => [1, 2, 3].map(i => note(`m${i}.md`, { typ: 'forskningsmöte', datum: DAY, krets, deltagare: `P${i}` }));
  assert(e.audit(möten('kärna'), DAY).some(f => f.princip === 'Bara kärnan'));
  assert(!e.audit(möten('nätverk'), DAY).some(f => f.princip === 'Bara kärnan'));
});

test('faskrav: anteckningar till en annan fråga räknas inte', () => {
  const q = note(Q, { typ: 'forskningsfråga', fas: 'pröva' });
  const annan = note('m.md', { typ: 'forskningsmöte', fråga: '[[Annan]]' });
  assert.equal(e.phaseRequirements(q, [annan])[1].ok, false);
});

test('fasloggen läggs till öppet under Fasbeslut', () => {
  const body = e.questionNote({ date: DAY, titel: 'Q', varför: 'x' });
  const out = e.appendPhaseLog(body, '2026-11-18: Utforska → Kombinera.');
  assert.match(out, /## Fasbeslut\n- 2026-11-17: Frågan formulerades\. Fas: Utforska\.\n- 2026-11-18: Utforska → Kombinera\.\n$/);
  const mitt = e.appendPhaseLog('# T\n## Fasbeslut\n- a\n## Annat\ntext\n', 'b');
  assert.equal(mitt, '# T\n## Fasbeslut\n- a\n- b\n\n## Annat\ntext\n');
  assert.equal(e.appendPhaseLog('# T\n', 'c'), '# T\n\n## Fasbeslut\n- c\n');
});

const princip = (findings, p) => findings.filter(f => f.princip === p);

test('granskning: högst två aktiva frågor', () => {
  const qs = [1, 2, 3].map(i => note(`q${i}.md`, { typ: 'forskningsfråga', status: 'aktiv', fas: 'utforska', datum: DAY }));
  assert.equal(princip(e.audit(qs, DAY), 'För många frågor').length, 1);
  assert.equal(princip(e.audit(qs.slice(0, 2), DAY), 'För många frågor').length, 0);
});

test('granskning: utforskar utan att välja efter 30 dagar', () => {
  const q = note(Q, { typ: 'forskningsfråga', status: 'aktiv', fas: 'utforska', fas_ändrad: '2026-10-01' });
  assert.equal(princip(e.audit([q], DAY), 'Står still').length, 1);
  const ny = note(Q, { typ: 'forskningsfråga', status: 'aktiv', fas: 'utforska', fas_ändrad: '2026-11-10' });
  assert.equal(princip(e.audit([ny], DAY), 'Står still').length, 0);
});

test('granskning: fördjupning utan motprov', () => {
  const q = note(Q, { typ: 'forskningsfråga', status: 'aktiv', fas: 'utveckla', fas_ändrad: DAY });
  assert.equal(princip(e.audit([q], DAY), 'Ingen kritik').length, 1);
  const m = note('m.md', { typ: 'motprov', fråga: link, datum: DAY });
  assert.equal(princip(e.audit([q, m], DAY), 'Ingen kritik').length, 0);
});

test('granskning: inget forskningsmöte', () => {
  const q = note(Q, { typ: 'forskningsfråga', status: 'aktiv', fas: 'pröva', fas_ändrad: DAY });
  assert.equal(princip(e.audit([q], DAY), 'Ingen extern återkoppling').length, 1);
  const gammalt = note('mö.md', { typ: 'forskningsmöte', datum: '2026-09-01' });
  assert.match(princip(e.audit([q, gammalt], DAY), 'Ingen extern återkoppling')[0].text, /77 dagar/);
  const nytt = note('mö.md', { typ: 'forskningsmöte', datum: '2026-11-10' });
  assert.equal(princip(e.audit([q, nytt], DAY), 'Ingen extern återkoppling').length, 0);
});

test('granskning: vilande fråga påminner när vilan är slut', () => {
  const q = note(Q, { typ: 'forskningsfråga', status: 'vilar', vila_till: '2026-11-17' });
  assert.equal(princip(e.audit([q], DAY), 'Vila slut').length, 1);
  const vilar = note(Q, { typ: 'forskningsfråga', status: 'vilar', vila_till: '2026-11-30' });
  assert.equal(princip(e.audit([vilar], DAY), 'Vila slut').length, 0);
});

test('granskning: AI-konsultationer utan egen tanke först', () => {
  const ai = i => note(`a${i}.md`, { typ: 'ai-konsultation', datum: DAY, egen_tanke_först: i < 3 ? 'nej' : 'ja' },
    '## Vad tar jag med mig?\nJag behöver fler källor.');
  const all = [0, 1, 2, 3].map(ai);
  assert.equal(princip(e.audit(all, DAY), 'AI-användning').length, 1);
  const bra = [0, 1, 2, 3].map(i => note(`a${i}.md`, { typ: 'ai-konsultation', datum: DAY, egen_tanke_först: 'ja' },
    '## Vad tar jag med mig?\nOk.'));
  assert.equal(princip(e.audit(bra, DAY), 'AI-användning').length, 0);
});

test('granskning: AI-svar utan egen sammanfattning', () => {
  const a = note('a.md', { typ: 'ai-konsultation', datum: '2026-11-14', egen_tanke_först: 'ja' },
    '## Svaret (klistra in)\nAI sa något.\n## Vad tar jag med mig?\n\n');
  assert.equal(princip(e.audit([a], DAY), 'AI-användning').length, 1);
});

test('granskning: öppna felrättningar och månadsgranskning', () => {
  const k = note('k.md', { typ: 'felrättning', status: 'öppen', datum: '2026-10-01' });
  assert.equal(princip(e.audit([k], DAY), 'Öppen felrättning').length, 1);
  assert.equal(princip(e.audit([], DAY), 'Förmågegranskning').length, 1);
  const g = note('g.md', { typ: 'förmågegranskning', datum: '2026-11-01' });
  assert.equal(princip(e.audit([g], DAY), 'Förmågegranskning').length, 0);
});

test('granskning: föreslår det första uppdraget när ingen fråga är aktiv', () => {
  const f = note('f.md', { typ: 'forskningsfråga', status: 'förslag' });
  assert.equal(princip(e.audit([f], DAY), 'Ingen aktiv fråga').length, 1);
});

test('granskning: varningar före påminnelser', () => {
  const qs = [1, 2, 3].map(i => note(`q${i}.md`, { typ: 'forskningsfråga', status: 'aktiv', fas: 'pröva', fas_ändrad: DAY }));
  const f = e.audit(qs, DAY);
  const first = f.findIndex(x => x.nivå === 'påminnelse');
  assert(first === -1 || f.slice(first).every(x => x.nivå === 'påminnelse'));
});

test('mått: självständighet och förmåga, inte produktion', () => {
  const notes = [
    note('a.md', { typ: 'ai-konsultation', datum: DAY, egen_tanke_först: 'ja' }),
    note('b.md', { typ: 'ai-konsultation', datum: DAY, egen_tanke_först: 'nej' }),
    note('ö.md', { typ: 'övning', datum: DAY, utan_ai: 'ja' }),
    note('g1.md', { typ: 'förmågegranskning', datum: '2026-10-15', problemformulering: 2, metodkompetens: 2 }),
    note('g2.md', { typ: 'förmågegranskning', datum: '2026-11-15', problemformulering: 3, metodkompetens: 4 }),
    note('h.md', { typ: 'hypotes' }, '> [!belagt]\n> x\n> [!spekulation]\n> y')
  ];
  const m = e.metrics(notes, DAY);
  assert.equal(m.aiKonsultationer, 2);
  assert.equal(m.tänktFörst, 1);
  assert.equal(m.övningarUtanAI, 1);
  assert.equal(m.förmåga, 3.5);
  assert.equal(m.förmågaFörra, 2);
  assert.deepEqual(m.epistemik, { belagt: 1, tolkning: 0, spekulation: 1 });
});

test('AI-konsultation: roll, läge och tillitskontraktet följer med', () => {
  const p = e.buildPrompt({ roll: 'kritik', läge: 'utveckling', titel: 'Hypotes', text: '---\ntyp: hypotes\n---\nMin idé.' });
  assert.match(p, /Kritisk granskning/);
  assert.match(p, /Ge mig inte ett färdigt svar/);
  assert.match(p, /\[BELAGT\]/);
  assert.match(p, /Utgå från det jag har skrivit/);
  assert.match(p, /Min idé\./);
  assert(!p.includes('typ: hypotes'), 'frontmatter ska inte skickas');
});

test('frågemallen innehåller engagemang, avgränsning och fasloggen', () => {
  const t = e.questionNote({ date: DAY, titel: 'När stärker AI tänkandet?', varför: 'x' });
  for (const h of ['Varför är frågan viktig', 'Det jag väljer bort', 'Lärdomar', 'Delat med', 'Fasbeslut']) assert(t.includes(h), h);
  assert.match(t, /fas: utforska/);
});

test('varje fas har verktyg', () => {
  for (const ph of e.PHASES) assert(e.PHASE_TOOLS[ph.id], `verktyg saknas för ${ph.id}`);
});

test('granskning: vila räknas som öppen fråga', () => {
  const qs = [1, 2, 3, 4, 5].map(i => note(`q${i}.md`, { typ: 'forskningsfråga', status: i < 4 ? 'vilar' : 'aktiv', vila_till: '2026-12-30', fas: 'utforska', fas_ändrad: DAY, datum: DAY }));
  assert.equal(princip(e.audit(qs, DAY), 'Många öppna frågor').length, 1);
  assert.equal(princip(e.audit(qs.slice(0, 4), DAY), 'Många öppna frågor').length, 0);
});

test('granskning: fler påbörjade än avslutade frågor', () => {
  const qs = [1, 2, 3].map(i => note(`q${i}.md`, { typ: 'forskningsfråga', status: 'vilar', vila_till: '2026-12-30', datum: '2026-10-0' + i }));
  assert.equal(princip(e.audit(qs, DAY), 'Påbörjat mer än avslutat').length, 1);
  const klar = note('q4.md', { typ: 'forskningsfråga', status: 'avslutad', utfall: 'förkastad', avslutad: '2026-11-01', datum: '2026-09-01' });
  assert.equal(princip(e.audit([...qs, klar], DAY), 'Påbörjat mer än avslutat').length, 0, 'en förkastad hypotes räknas som avslutad');
  const förslag = [1, 2, 3].map(i => note(`f${i}.md`, { typ: 'forskningsfråga', status: 'förslag', datum: DAY }));
  assert.equal(princip(e.audit(förslag, DAY), 'Påbörjat mer än avslutat').length, 0, 'förslag räknas inte');
});

test('granskning: en fråga som vilat tre gånger', () => {
  const q = note(Q, { typ: 'forskningsfråga', status: 'vilar', vila_till: '2026-12-30', vilat: 3 });
  assert.equal(princip(e.audit([q], DAY), 'Vilar ofta').length, 1);
});

test('granskning: motprov på frågan täcker dess hypoteser, inte andras', () => {
  const h = note('h.md', { typ: 'hypotes', fråga: link, datum: '2026-10-01' });
  const m = note('m.md', { typ: 'motprov', fråga: link, datum: DAY });
  assert.equal(princip(e.audit([h, m], DAY), 'Oprövad hypotes').length, 0);
  const annan = note('m2.md', { typ: 'motprov', fråga: '[[Annan]]', datum: DAY });
  assert.equal(princip(e.audit([h, annan], DAY), 'Oprövad hypotes').length, 1);
  const riktad = note('m3.md', { typ: 'motprov', fråga: link, gäller: '[[annan-hypotes]]', datum: DAY });
  assert.equal(princip(e.audit([h, riktad], DAY), 'Oprövad hypotes').length, 1, 'riktat motprov gäller bara sin hypotes');
});

test('granskning: inga nya kontakter på ett halvår', () => {
  const m = i => note(`mö${i}.md`, { typ: 'forskningsmöte', ny_kontakt: 'nej', datum: '2026-1' + i + '-01' });
  assert.equal(princip(e.audit([0, 1].map(m).concat(note('mö9.md', { typ: 'forskningsmöte', ny_kontakt: 'nej', datum: '2026-09-01' })), DAY), 'Inga nya kontakter').length, 1);
  const ny = note('mö5.md', { typ: 'forskningsmöte', ny_kontakt: 'ja', datum: '2026-11-05' });
  assert.equal(princip(e.audit([0, 1].map(m).concat(ny), DAY), 'Inga nya kontakter').length, 0);
});

test('mått: forskningsmöten, fokuspass och utfall', () => {
  const m = e.metrics([
    note('mö.md', { typ: 'forskningsmöte', ny_kontakt: 'ja', datum: '2026-11-01' }),
    note('mö2.md', { typ: 'forskningsmöte', ny_kontakt: 'nej', datum: '2026-06-01' }),
    note('f.md', { typ: 'fokuslogg' }, '- 2026-11-10 09:00–09:50 (50 av 50 min): \n- 2026-11-12 09:00–10:30 (90 av 90 min): klar\n- 2026-08-01 09:00–09:25 (25 av 25 min): '),
    note('q1.md', { typ: 'forskningsfråga', status: 'avslutad', utfall: 'besvarad' }),
    note('q2.md', { typ: 'forskningsfråga', status: 'avslutad', utfall: 'övergiven' })
  ], DAY);
  assert.equal(m.möten, 1);
  assert.equal(m.nyaKontakter, 1);
  assert.equal(m.fokuspass, 2);
  assert.equal(m.fokusminuter, 140);
  assert.deepEqual(m.utfall, { besvarad: 1, förkastad: 0, övergiven: 1 });
});

test('hypotesmallen frågar efter utmanat antagande', () => {
  assert.match(e.TYPES.hypothesis.render({ date: DAY }), /## Vilket etablerat antagande utmanar hypotesen\?/);
});

test('granskning: möten följs upp, varieras och täcker ämne, metod och annat fält', () => {
  const aq = note(Q, { typ: 'forskningsfråga', status: 'aktiv', fas: 'pröva', fas_ändrad: DAY, datum: DAY });
  const möte = (i, fm, body = '') => note(`mö${i}.md`, Object.assign({ typ: 'forskningsmöte', ny_kontakt: 'ja' }, fm), body);
  const ouppföljt = möte(1, { datum: '2026-10-20', deltagare: 'Anna', kompetens: 'ämne' }, '## Uppföljning\n- [ ] Skicka utkast\n');
  assert.equal(princip(e.audit([aq, ouppföljt], DAY), 'Uppföljning efter möte').length, 1);
  const klart = möte(1, { datum: '2026-10-20', deltagare: 'Anna', kompetens: 'ämne' }, '## Uppföljning\n- [x] Skicka utkast\n');
  assert.equal(princip(e.audit([aq, klart], DAY), 'Uppföljning efter möte').length, 0);
  const samma = [1, 2, 3].map(i => möte(i, { datum: `2026-1${i % 2}-0${i}`, deltagare: 'Anna', kompetens: 'ämne' }));
  assert.equal(princip(e.audit([aq, ...samma], DAY), 'Samma person').length, 1);
  assert.match(princip(e.audit([aq, ...samma], DAY), 'Saknad kompetens')[0].text, /metod, annat fält/);
  const bredd = [möte(1, { datum: '2026-11-01', deltagare: 'Anna', kompetens: 'ämne' }), möte(2, { datum: '2026-11-02', deltagare: 'Bo', kompetens: 'metod' }), möte(3, { datum: '2026-11-03', deltagare: 'Cy', kompetens: 'annat fält' })];
  const f = e.audit([aq, ...bredd], DAY);
  assert.equal(princip(f, 'Samma person').length + princip(f, 'Saknad kompetens').length, 0);
});

test('granskning: aktiv fråga men inget arbete på 14 dagar', () => {
  const aq = note(Q, { typ: 'forskningsfråga', status: 'aktiv', fas: 'utveckla', fas_ändrad: DAY, datum: DAY });
  assert.equal(princip(e.audit([aq], DAY), 'Inget arbete loggat').length, 1);
  const gammalt = note('p.md', { typ: 'forskarpass', datum: '2026-10-01' });
  assert.match(princip(e.audit([aq, gammalt], DAY), 'Inget arbete loggat')[0].text, /47 dagar/);
  const fokus = note('f.md', { typ: 'fokuslogg' }, '- 2026-11-15 09:00–09:50 (50 av 50 min): ');
  assert.equal(princip(e.audit([aq, gammalt, fokus], DAY), 'Inget arbete loggat').length, 0, 'fokuspass räknas som arbete');
});

test('granskning: inga nya idéer på 60 dagar', () => {
  const aq = note(Q, { typ: 'forskningsfråga', status: 'aktiv', fas: 'utveckla', fas_ändrad: DAY, datum: '2026-08-01' });
  assert.equal(princip(e.audit([aq], DAY), 'Inga nya idéer').length, 1);
  const idé = note('i.md', { typ: 'idé', datum: '2026-11-01' });
  assert.equal(princip(e.audit([aq, idé], DAY), 'Inga nya idéer').length, 0);
  const ny = note(Q, Object.assign({}, aq.fm, { datum: '2026-11-01' }));
  assert.equal(princip(e.audit([ny], DAY), 'Inga nya idéer').length, 0, 'inte för nya frågor');
});

test('granskning: forskarpass utan något oklart', () => {
  const pass = (i, body) => note(`p${i}.md`, { typ: 'forskarpass', datum: DAY }, body);
  const tomma = [1, 2, 3].map(i => pass(i, e.TYPES.pass.render({ date: DAY })));
  assert.equal(princip(e.audit(tomma, DAY), 'Inget oklart').length, 1);
  const ärlig = pass(4, '## 6. Det jag inte förstår\nHur effekten ska mätas.\n');
  assert.equal(princip(e.audit([...tomma, ärlig], DAY), 'Inget oklart').length, 0);
});

test('granskning: förmågegranskning kräver belägg och övning för den svagaste förmågan', () => {
  const g = (body) => note('g.md', { typ: 'förmågegranskning', datum: DAY, problemformulering: 4, metodkompetens: 2 }, body);
  const utan = g(e.TYPES.review.render({ date: DAY }));
  assert.equal(princip(e.audit([utan], DAY), 'Skattning utan belägg').length, 1);
  const med = g('## Problemformulering\n- Arbetsprov: [[Pass 1]]\n## Metodkompetens\n- Arbetsprov: [[Övning 1]]\n');
  assert.equal(princip(e.audit([med], DAY), 'Skattning utan belägg').length, 0);
  assert.match(princip(e.audit([med], DAY), 'Svagaste förmågan')[0].text, /Metodkompetens/);
  const övning = note('ö.md', { typ: 'övning', förmåga: 'metodkompetens', utan_ai: 'ja', datum: DAY });
  assert.equal(princip(e.audit([med, övning], DAY), 'Svagaste förmågan').length, 0);
});

test('granskning: ökande AI-beroende jämfört med förra månaden', () => {
  const ai = (i, datum, ja) => note(`a${i}.md`, { typ: 'ai-konsultation', datum, egen_tanke_först: ja ? 'ja' : 'nej' }, '## Vad tar jag med mig?\nx');
  const förra = [1, 2, 3, 4].map(i => ai(i, '2026-10-05', true));
  const nu = [5, 6, 7, 8].map(i => ai(i, DAY, i === 5));
  assert.match(princip(e.audit([...förra, ...nu], DAY), 'Ökande AI-beroende')[0].text, /från 100 % till 25 %/);
  const stabilt = [5, 6, 7, 8].map(i => ai(i, DAY, true));
  assert.equal(princip(e.audit([...förra, ...stabilt], DAY), 'Ökande AI-beroende').length, 0);
  const m = e.metrics([...förra, ...nu], DAY);
  assert.deepEqual([m.tänktFörst, m.aiKonsultationer, m.tänktFörstFörra, m.aiFörra], [1, 4, 4, 4]);
});

test('datumhjälp', () => {
  assert.equal(e.addDays('2026-12-25', 14), '2027-01-08');
  assert.equal(e.daysBetween('2026-11-01', '2026-11-17'), 16);
});

process.stdout.write(`OK: metoden (${n} tester): faser, faskrav, granskning, mått, AI-konsultation\n`);
