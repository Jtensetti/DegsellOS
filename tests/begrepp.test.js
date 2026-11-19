'use strict';
// Varje begrepp i arbetsmetoden ska bäras av något systemet kräver eller följer
// upp: ett faskrav som inte uppfylls, eller en regel i "Att åtgärda" som slår till.
// Testet kör ett scenario per begrepp där begreppet brister och kontrollerar
// att systemet reagerar.
const assert = require('node:assert/strict');
const Module = require('node:module');
const orig = Module._load;
Module._load = function (r, ...a) { return r === 'obsidian' ? { Plugin: class {}, ItemView: class {}, Notice: class {}, Modal: class {} } : orig.call(this, r, ...a); };
const { engine: e } = require('../vault/.obsidian/plugins/forskaros-core/main.js');
Module._load = orig;

const D = '2026-11-17';
const n = (path, fm, body = '') => ({ path, fm, body, created: fm.datum || D });
const L = '[[Q]]';
const fråga = (fas, extra = {}, body = '') => n('Q.md', Object.assign({ typ: 'forskningsfråga', status: 'aktiv', fas, fas_ändrad: D, datum: D }, extra), body);
const krav = (q, notes, text) => e.phaseRequirements(q, notes).find(r => r.text.includes(text));
const regel = (notes, princip) => e.audit(notes, D).some(f => f.princip === princip);
const ord = k => Array.from({ length: k }, (_, i) => `ord${i}`).join(' ');

const hyp = (extra = {}, body = e.TYPES.hypothesis.render({ date: D })) => n('h.md', Object.assign({ typ: 'hypotes', fråga: L }, extra), body);
const karta = () => n('k.md', { typ: 'perspektivkarta', fråga: L }, e.TYPES.diversity.render({ date: D }));
const möte = (extra = {}, body = '') => n(`m${Math.random()}.md`, Object.assign({ typ: 'forskningsmöte', fråga: L, datum: D }, extra), body);
const projekt = extra => n('04 EXPERIMENT/Projekt.md', Object.assign({ typ: 'experiment', fråga: L, projekt: '/p' }, extra), '## Resultat\nRapporten är byggd.\n');

const BEGREPP = {
  'Kreativitet': () => !krav(fråga('kombinera'), [hyp()], 'vad som är nytt').ok
    && regel([fråga('utveckla', { datum: '2026-08-01' })], 'Inga nya idéer'),
  'Kommunikation': () => !krav(fråga('dela', {}, `## Sammanfattning för någon utanför fältet\n${ord(10)}\n`), [], 'sammanfattning').ok,
  'Ifrågasättande': () => regel([n('h.md', { typ: 'hypotes', datum: '2026-10-01' })], 'Oprövad hypotes')
    && !krav(fråga('pröva'), [], 'besvarat motprov').ok,
  'Möten': () => !krav(fråga('pröva'), [möte({}, e.TYPES.meeting.render({ date: D }))], 'framfört en invändning').ok
    && regel([fråga('pröva'), möte({ datum: '2026-10-01', deltagare: 'A', kompetens: 'ämne' }, '## Uppföljning\n- [ ] Skicka utkast\n')], 'Uppföljning efter möte'),
  'Vision': () => !krav(fråga('välj'), [], 'vad som förändras om den besvaras').ok,
  'Respektlöshet': () => !krav(fråga('kombinera'), [hyp()], 'antagande den utmanar').ok
    && !krav(fråga('kombinera'), [hyp()], 'vem som företräder antagandet').ok,
  'Mod': () => !krav(fråga('välj'), [hyp({ konfidens: 'okänd' })], 'konfidens').ok
    && !krav(fråga('välj'), [hyp({}, '')], 'falsifieringskriterium').ok
    && !krav(fråga('pröva'), [möte({}, '## Viktigaste invändningen jag fick\nUrvalet.\n')], 'företräder det antagande').ok,
  'Arbete': () => regel([fråga('utveckla')], 'Inget arbete loggat'),
  'Kontakter': () => regel([1, 2, 3].map(i => n(`m${i}.md`, { typ: 'forskningsmöte', datum: `2026-1${i % 2}-0${i}`, ny_kontakt: 'nej' })), 'Inga nya kontakter'),
  'Lekfullhet': () => regel([fråga('utveckla', { datum: '2026-08-01' })], 'Inga nya idéer')
    && regel([1, 2, 3].map(i => n(`p${i}.md`, { typ: 'forskarpass', datum: D }, e.TYPES.pass.render({ date: D }))), 'Inget oklart'),
  'Kompetens': () => regel([n('g.md', { typ: 'förmågegranskning', datum: D, metodkompetens: 2 }, '## Metodkompetens\n- Arbetsprov: [[Ö]]\n')], 'Svagaste förmågan')
    && regel([n('g.md', { typ: 'förmågegranskning', datum: D, metodkompetens: 2 }, '## Metodkompetens\n- Arbetsprov:\n')], 'Skattning utan belägg'),
  'Nätverk': () => regel([1, 2, 3].map(i => möte({ krets: 'kärna', deltagare: `P${i}` })), 'Bara kärnan'),
  'Kombinera': () => !krav(fråga('kombinera'), [], 'Minst en hypotes').ok
    && !krav(fråga('kombinera'), [hyp()], 'etablerad kunskap').ok,
  'Envishet': () => regel([1, 2, 3].map(i => n(`q${i}.md`, { typ: 'forskningsfråga', status: 'vilar', vila_till: '2027-01-01', datum: '2026-10-0' + i })), 'Påbörjat mer än avslutat'),
  'Samarbete': () => !krav(fråga('utveckla'), [projekt({ nivå: 'Dokumenterad' })], 'Någon mer arbetar med frågan').ok,
  'Mångfald': () => !krav(fråga('utforska'), [karta()], 'minst tre ifyllda perspektiv').ok
    && regel([1, 2, 3].map(i => möte({ deltagare: 'Samma' })), 'Samma person'),
  'Tillit': () => regel([n('k.md', { typ: 'felrättning', status: 'öppen', datum: '2026-10-01' })], 'Öppen felrättning')
    && !krav(fråga('dela'), [projekt({ nivå: 'Dokumenterad' })], 'upprepad med samma resultat').ok,
  'Förändring och förbättring': () => !krav(fråga('ompröva'), [], 'Minst en omprövning').ok
    && !krav(fråga('ompröva'), [], 'Lärdomar').ok,
  'Nyfikenhet': () => !krav(fråga('utforska', {}, e.questionNote({ date: D, titel: 'Q' })), [], 'tre saker du undrar').ok,
  'Engagemang': () => !krav(fråga('utforska', {}, '## Varför är frågan viktig?\nDen är intressant.\n'), [], 'minst 30 ord').ok
    && !krav(fråga('utforska'), [], 'vem som bryr sig om svaret').ok,
  'Genomförande – från tanke till handling': () => !krav(fråga('utveckla'), [], 'experiment eller arbetsprov med resultat').ok
    && krav(fråga('utveckla'), [projekt({ nivå: 'Dokumenterad' })], 'experiment eller arbetsprov med resultat').ok,
  'Att se både detaljerna och helheten': () => regel([projekt({ att_ompröva: 1 })], 'Påstående att ompröva'),
  'Att bygga broar mellan människor och kunskaper': () => !krav(fråga('utforska'), [karta()], 'oväntat fält').ok
    && regel([fråga('pröva'), ...[1, 2].map(i => möte({ deltagare: `P${i}`, kompetens: 'ämne' }))], 'Saknad kompetens'),
  'Att vara bekväm med att vara obekväm': () => regel([1, 2, 3].map(i => n(`p${i}.md`, { typ: 'forskarpass', datum: D }, e.TYPES.pass.render({ date: D }))), 'Inget oklart')
    && !krav(fråga('utforska'), [karta()], 'motsäger varandra').ok,
  'Framtiden är den viktigaste tiden': () => !krav(fråga('dela'), [], 'vilken ny fråga svaret öppnar').ok
    && regel([
      ...[1, 2, 3].map(i => n(`a${i}.md`, { typ: 'ai-konsultation', datum: '2026-10-05', egen_tanke_först: 'ja' }, '## Vad tar jag med mig?\nx')),
      ...[4, 5, 6].map(i => n(`a${i}.md`, { typ: 'ai-konsultation', datum: D, egen_tanke_först: 'nej' }, '## Vad tar jag med mig?\nx'))
    ], 'Ökande AI-beroende'),
  // Metodens egna begrepp utöver listan.
  'Friktion': () => !krav(fråga('pröva'), [], 'besvarat motprov').ok,
  'Intellektuell ödmjukhet': () => e.UTFALL.förkastad && !krav(fråga('ompröva'), [], 'Minst en omprövning').ok
};

const misslyckade = Object.entries(BEGREPP).filter(([, fn]) => !fn()).map(([k]) => k);
assert.deepEqual(misslyckade, [], `Begrepp utan fungerande krav eller regel: ${misslyckade.join(', ')}`);
process.stdout.write(`OK: alla ${Object.keys(BEGREPP).length} begrepp bärs av ett krav eller en regel som slår till\n`);
