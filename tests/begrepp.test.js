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

const BEGREPP = {
  'Envishet': () => regel([1, 2, 3].map(i => n(`q${i}.md`, { typ: 'forskningsfråga', status: 'vilar', vila_till: '2027-01-01', datum: '2026-10-0' + i })), 'Påbörjat mer än avslutat'),
  'Förändring': () => !krav(fråga('ompröva'), [], 'Minst en omprövning').ok,
  'Friktion': () => !krav(fråga('pröva'), [], 'besvarat motprov').ok,
  'Ifrågasättande': () => regel([n('h.md', { typ: 'hypotes', datum: '2026-10-01' })], 'Oprövad hypotes'),
  'Tillit': () => regel([n('k.md', { typ: 'felrättning', status: 'öppen', datum: '2026-10-01' })], 'Öppen felrättning'),
  'Kompetens': () => regel([n('g.md', { typ: 'förmågegranskning', datum: D, metodkompetens: 2 }, '## Metodkompetens\n- Arbetsprov: [[Ö]]\n')], 'Svagaste förmågan')
    && regel([n('g.md', { typ: 'förmågegranskning', datum: D, metodkompetens: 2 }, '## Metodkompetens\n- Arbetsprov:\n')], 'Skattning utan belägg'),
  'Möten': () => !krav(fråga('pröva'), [n('m.md', { typ: 'forskningsmöte', fråga: L }, e.TYPES.meeting.render({ date: D }))], 'framfört en invändning').ok
    && regel([fråga('pröva'), n('m.md', { typ: 'forskningsmöte', datum: '2026-10-01', deltagare: 'A', kompetens: 'ämne' }, '## Uppföljning\n- [ ] Skicka utkast\n')], 'Uppföljning efter möte'),
  'Kontakter': () => regel([1, 2, 3].map(i => n(`m${i}.md`, { typ: 'forskningsmöte', datum: `2026-1${i % 2}-0${i}`, ny_kontakt: 'nej' })), 'Inga nya kontakter'),
  'Nätverk': () => regel([fråga('pröva'), ...[1, 2].map(i => n(`m${i}.md`, { typ: 'forskningsmöte', datum: D, deltagare: `P${i}`, kompetens: 'ämne' }))], 'Saknad kompetens'),
  'Mångfald': () => !krav(fråga('utforska'), [n('k.md', { typ: 'perspektivkarta', fråga: L }, e.TYPES.diversity.render({ date: D }))], 'minst tre ifyllda perspektiv').ok
    && regel([1, 2, 3].map(i => n(`m${i}.md`, { typ: 'forskningsmöte', datum: D, deltagare: 'Samma' })), 'Samma person'),
  'Kombinera': () => !krav(fråga('kombinera'), [n('h.md', { typ: 'hypotes', fråga: L }, e.TYPES.hypothesis.render({ date: D }))], 'vad som är nytt').ok,
  'Respektlöshet': () => !krav(fråga('kombinera'), [n('h.md', { typ: 'hypotes', fråga: L }, e.TYPES.hypothesis.render({ date: D }))], 'antagande den utmanar').ok,
  'Mod': () => !krav(fråga('välj'), [n('h.md', { typ: 'hypotes', fråga: L, konfidens: 'okänd' })], 'konfidens').ok
    && !krav(fråga('välj'), [n('h.md', { typ: 'hypotes', fråga: L })], 'falsifieringskriterium').ok,
  'Arbete': () => regel([fråga('utveckla')], 'Inget arbete loggat'),
  'Engagemang': () => !krav(fråga('utforska', {}, '## Varför är frågan viktig?\nDen är intressant.\n'), [], 'minst 30 ord').ok,
  'Kommunikation': () => !krav(fråga('dela', {}, `## Sammanfattning för någon utanför fältet\n${ord(10)}\n`), [], 'sammanfattning').ok,
  'Lekfullhet': () => regel([fråga('utveckla', { datum: '2026-08-01' })], 'Inga nya idéer')
    && !krav(fråga('utforska'), [n('k.md', { typ: 'perspektivkarta', fråga: L }, e.TYPES.diversity.render({ date: D }))], 'oväntat fält').ok,
  'Vision': () => !krav(fråga('välj'), [], 'vad som förändras om den besvaras').ok,
  'Framtiden': () => !krav(fråga('välj', {}, '## Om frågan besvaras\n'), [], 'vad som förändras').ok,
  'Bekvämt att vara obekväm': () => regel([1, 2, 3].map(i => n(`p${i}.md`, { typ: 'forskarpass', datum: D }, e.TYPES.pass.render({ date: D }))), 'Inget oklart'),
  'Intellektuell ödmjukhet': () => e.UTFALL.förkastad && !krav(fråga('ompröva'), [], 'Minst en omprövning').ok,
  'Mindre beroende av AI över tid': () => regel([
    ...[1, 2, 3].map(i => n(`a${i}.md`, { typ: 'ai-konsultation', datum: '2026-10-05', egen_tanke_först: 'ja' }, '## Vad tar jag med mig?\nx')),
    ...[4, 5, 6].map(i => n(`a${i}.md`, { typ: 'ai-konsultation', datum: D, egen_tanke_först: 'nej' }, '## Vad tar jag med mig?\nx'))
  ], 'Ökande AI-beroende')
};

const misslyckade = Object.entries(BEGREPP).filter(([, fn]) => !fn()).map(([k]) => k);
assert.deepEqual(misslyckade, [], `Begrepp utan fungerande krav eller regel: ${misslyckade.join(', ')}`);
process.stdout.write(`OK: alla ${Object.keys(BEGREPP).length} begrepp har ett krav eller en regel som slår till\n`);
