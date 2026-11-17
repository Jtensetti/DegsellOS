'use strict';

/*
 * ForskarOS Core
 *
 * Ett tillägg som får operativsystemet att hjälpa forskaren arbeta enligt
 * ForskarOS-metoden: den kreativa forskningscykeln, tänk-först-principen,
 * epistemisk märkning, Revisorns granskning och mått på självständighet.
 *
 * Allt sker lokalt. Tillägget gör inga nätverksanrop. AI-konsultationer
 * förbereds som text som forskaren själv väljer att kopiera till en AI.
 *
 * Filen är uppdelad i två delar:
 *   1. METODEN: rena funktioner utan Obsidian-beroenden (testas i tests/).
 *   2. GRÄNSSNITTET: Obsidian-panel, kommandon och dialoger.
 */

const obsidian = require('obsidian');
const { Plugin, ItemView, Notice, Modal } = obsidian;

/* ======================================================================
 * 1. METODEN
 * ====================================================================== */

/** Den kreativa forskningscykeln. Resultaten förändrar nästa cykel. */
const PHASES = [
  { id: 'utforska', namn: 'Utforska', symbios: 'Mångfald · lekfullhet · nyfikenhet',
    fråga: 'Vilka verkligt olika sätt finns det att förstå problemet?' },
  { id: 'kombinera', namn: 'Kombinera', symbios: 'Oväntade samband · etablerad kunskap',
    fråga: 'Vilken ovanlig kombination vilar på gedigen, etablerad kunskap?' },
  { id: 'välj', namn: 'Välj', symbios: 'Vision · koncentration · kompetens',
    fråga: 'Vilken enda hypotes är värd att fördjupa, och hur kan den visa sig fel?' },
  { id: 'pröva', namn: 'Pröva', symbios: 'Tillit · friktion · ifrågasättande',
    fråga: 'Vad är den starkaste invändningen, och vad säger en människa utanför?' },
  { id: 'utveckla', namn: 'Utveckla', symbios: 'Envishet · arbete · nya metoder',
    fråga: 'Vilket arbete, experiment eller ny metod prövar idén på riktigt?' },
  { id: 'ompröva', namn: 'Ompröva', symbios: 'Förändring · återkoppling · återhämtning',
    fråga: 'Vad har förändrats i din uppfattning, och vad gör du annorlunda?' },
  { id: 'dela', namn: 'Dela', symbios: 'Kommunikation · nätverk · verklig påverkan',
    fråga: 'Vem ska kunna granska, använda och utmana resultatet?' }
];

const MAX_AKTIVA_FRÅGOR = 2;
const MIN_EGNA_ORD = 50;

/** AI-rollerna. Systemet växlar uppgift, inte personlighet. */
const ROLES = {
  upptäckaren: {
    namn: 'Upptäckaren',
    uppdrag: 'Tillför alternativa perspektiv och möjliga forskningsluckor. Jämför min idé med minst två andra teoretiska utgångspunkter, gärna från fält jag inte nämnt. Peka ut var perspektiven motsäger varandra.'
  },
  motståndaren: {
    namn: 'Motståndaren',
    uppdrag: 'Försök motbevisa min hypotes, inte vinna en debatt. Redovisa de starkaste invändningarna, alternativa förklaringar och vilken evidens som skulle avgöra frågan.'
  },
  handledaren: {
    namn: 'Handledaren',
    uppdrag: 'Hjälp mig utveckla de metodiska och teoretiska förmågor jag saknar. Börja med att pröva vad jag redan kan. Föreläs inte om sådant jag behärskar.'
  },
  laboratorieassistenten: {
    namn: 'Laboratorieassistenten',
    uppdrag: 'Hjälp mig konstruera experiment, analysera resultat och dokumentera arbetet reproducerbart. Jag äger forskningsbesluten.'
  },
  revisorn: {
    namn: 'Revisorn',
    uppdrag: 'Granska mina tidigare slutsatser. Leta efter fel, för tvärsäkra påståenden, löften som inte följts upp och tecken på att samarbetet med AI gör mig mindre självständig.'
  }
};

/** AI-lägen. Utvecklingsläge är standard. */
const MODES = {
  utveckling: {
    namn: 'Utvecklingsläge',
    beskrivning: 'AI ska utveckla min förmåga, inte leverera svaret.',
    instruktion: 'Ge mig inte ett färdigt svar. Ställ frågor, ge ledtrådar och peka ut luckor så att jag själv kommer fram till slutsatsen. Om jag ber om svaret, ge det stegvis.'
  },
  prövning: {
    namn: 'Prövningsläge',
    beskrivning: 'AI ska hitta fel, i mina och i AI-genererade slutsatser.',
    instruktion: 'Leta efter fel, svaga antaganden och alternativa förklaringar. Var saklig och konkret. Säg tydligt om du inte hittar något allvarligt fel, och hitta inte på problem.'
  },
  prestation: {
    namn: 'Prestationsläge',
    beskrivning: 'AI får hjälpa till att producera ett resultat. Används sparsamt.',
    instruktion: 'Hjälp mig producera ett bra resultat. Markera tydligt vilka delar som är ditt bidrag så att jag kan granska dem.'
  }
};

/** Tillitskontraktet, som skickas med varje AI-konsultation. */
const EPISTEMIC_CONTRACT = [
  'Märk varje viktigt påstående som [BELAGT] (med källa), [TOLKNING] eller [SPEKULATION].',
  'Förväxla inte rimlighet med sanning. Säg när du inte vet.',
  'Anpassa inte slutsatsen efter hur säker jag verkar. Kritisera svaga idéer och lyft starka.',
  'Om du upptäcker att du tidigare haft fel, säg det öppet.',
  'Ta inte över tänkandet: jag har skrivit min egen uppfattning först, utgå från den.'
];

/** Principer som visas i panelen, en per dag. */
const PRINCIPLES = [
  'Var envis med frågan, inte med svaret.',
  'Mångfald ger perspektiv. Friktion skapar prövning. Tillit möjliggör öppenhet.',
  'Vi ska vara envisa i vår nyfikenhet, men föränderliga i våra övertygelser.',
  'Vi ska vara trygga med varandra, inte nödvändigtvis trygga i våra övertygelser.',
  'En ovanlig idé blir mer kraftfull när den vilar på mycket gedigen kunskap.',
  'Envishet med problemet. Förändringsvilja i metoden. Återhämtning för att se nya lösningar.',
  'En liten, stabil kärna som arbetar djupt, och ett stort, föränderligt nätverk.',
  'Intellektuell ödmjukhet: att verkligen vilja upptäcka att ens favoritidé är fel.',
  'Ett negativt resultat är ett forskningsresultat när metoden är sund.',
  'Framtiden är den viktigaste tiden.',
  'Målet är inte ett system som tänker åt dig, utan ett som tränar dig i att tänka bättre än i går.'
];

/** De sju förmågorna i den månatliga granskningen. */
const CAPABILITIES = [
  ['problemformulering', 'Problemformulering', 'Kan du formulera en avgränsad, vetenskapligt intressant fråga?'],
  ['kritisk_prövning', 'Kritisk prövning', 'Kan du själv hitta de starkaste invändningarna mot en idé?'],
  ['metodkompetens', 'Metodkompetens', 'Kan du välja och motivera en lämplig undersökningsmetod?'],
  ['självständighet', 'Intellektuell självständighet', 'Kan du återskapa och försvara resonemanget utan AI?'],
  ['tvärvetenskaplighet', 'Tvärvetenskaplighet', 'Kan du använda perspektiv från andra forskningsfält korrekt?'],
  ['genomförande', 'Genomförande', 'Har du avslutat något som kan granskas av andra?'],
  ['akademisk_samverkan', 'Akademisk samverkan', 'Har du fått relevant återkoppling från verkliga forskare?']
];

/* ---------- Hjälpfunktioner ---------- */

function pad(n) { return String(n).padStart(2, '0'); }

function today(now = new Date()) {
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
}

function addDays(date, days) {
  const d = new Date(`${date}T12:00:00`);
  d.setDate(d.getDate() + days);
  return today(d);
}

function daysBetween(from, to) {
  const a = Date.parse(`${from}T12:00:00`);
  const b = Date.parse(`${to}T12:00:00`);
  if (Number.isNaN(a) || Number.isNaN(b)) return 0;
  return Math.round((b - a) / 86400000);
}

function phaseIndex(id) { return PHASES.findIndex(p => p.id === id); }

function phaseOf(id) { return PHASES[phaseIndex(id)] || PHASES[0]; }

function nextPhase(id) {
  const i = phaseIndex(id);
  return i < 0 || i === PHASES.length - 1 ? PHASES[0] : PHASES[i + 1];
}

/** "[[01 RIKTNING/Fråga|alias]]" → "01 RIKTNING/Fråga" */
function linkTarget(value) {
  if (!value) return '';
  const raw = Array.isArray(value) ? value[0] : value;
  return String(raw).trim()
    .replace(/^\[\[/, '').replace(/\]\]$/, '')
    .split('|')[0].split('#')[0].trim()
    .replace(/\.md$/, '');
}

function basename(path) { return path.split('/').pop().replace(/\.md$/, ''); }

function refersTo(note, question) {
  const target = linkTarget(note.fm && note.fm.fråga);
  if (!target) return false;
  const qPath = question.path.replace(/\.md$/, '');
  return target === qPath || target === basename(qPath);
}

function stripFrontmatter(body) {
  return String(body || '').replace(/^---\n[\s\S]*?\n---\n?/, '');
}

/** Rader som bara är mallens stödstruktur räknas inte som eget innehåll. */
function isTemplateLine(line) {
  const t = line.trim();
  if (!t) return true;
  if (/^#/.test(t)) return true;                       // rubriker
  if (/^>/.test(t)) return true;                       // mallens instruktioner
  if (/^\|/.test(t)) return /^\|[\s|:-]*$/.test(t) || /^\|[^|]*\|(\s*\|)+\s*$/.test(t);
  return /^([-*]|\d+\.)?\s*(\[[ xX]\])?\s*([^:]{0,60}:)?\s*$/.test(t);
}

/** Raderna som forskaren själv skrivit: utan mallrader och tabellrubriker. */
function contentLines(lines) {
  const separator = l => /^\s*\|[\s|:-]+\|\s*$/.test(l);
  return lines.filter((l, i) => !isTemplateLine(l) && !separator(lines[i + 1] || ''));
}

/** Texten under en rubrik (## …) som börjar med prefix, utan mallrader. */
function section(body, prefix) {
  const lines = stripFrontmatter(body).split('\n');
  const want = prefix.toLowerCase();
  let inside = false;
  const out = [];
  for (const line of lines) {
    const m = /^##\s+(?:\d+\.\s*)?(.*)$/.exec(line);
    if (m) {
      if (inside) break;
      inside = m[1].trim().toLowerCase().startsWith(want);
      continue;
    }
    if (inside) out.push(line);
  }
  return contentLines(out).map(l => l.trim()).join('\n').trim();
}

function countWords(text) {
  return (String(text).match(/[\p{L}\p{N}]+/gu) || []).length;
}

/** Antal ord forskaren själv skrivit i en anteckning. */
function ownWords(body) {
  return countWords(contentLines(stripFrontmatter(body).split('\n')).join('\n'));
}

/** Datum för en anteckning: frontmatter först, annars filens skapandedatum. */
function noteDate(note) {
  if (note.fm && note.fm.datum) return String(note.fm.datum).slice(0, 10);
  return note.created || '';
}

/* ---------- Faskrav (grindar) ---------- */

function req(ok, text) { return { ok: Boolean(ok), text }; }

/**
 * Vad som behöver vara gjort innan en forskningsfråga lämnar sin nuvarande fas.
 * Kraven är mjuka: forskaren kan gå vidare ändå, men måste motivera varför.
 * Motiveringen loggas öppet i frågan (tillit).
 */
function phaseRequirements(question, notes) {
  const linked = notes.filter(n => refersTo(n, question));
  const of = typ => linked.filter(n => n.fm.typ === typ);
  const hyps = of('hypotes');
  switch (question.fm.fas || 'utforska') {
    case 'utforska':
      return [
        req(section(question.body, 'Varför'), 'Du har skrivit varför frågan är värd din tid (engagemang)'),
        req(of('perspektivkarta').length > 0, 'Minst en perspektivkarta med verkligt olika förklaringar (mångfald)')
      ];
    case 'kombinera':
      return [
        req(hyps.length > 0, 'Minst en hypotes formulerad med egna ord'),
        req(hyps.some(h => section(h.body, 'Etablerad kunskap')), 'Hypotesen redovisar den etablerade kunskap den vilar på'),
        req(hyps.some(h => section(h.body, 'Den ovanliga kombinationen')), 'Hypotesen beskriver sin ovanliga kombination (originalitet)')
      ];
    case 'välj':
      return [
        req(hyps.some(h => section(h.body, 'Falsifiering')), 'En hypotes har ett falsifieringskriterium: vad skulle visa att du har fel?'),
        req(hyps.some(h => section(h.body, 'Prediktioner')), 'En hypotes har konkreta prediktioner'),
        req(section(question.body, 'Det jag väljer bort'), 'Du har skrivit vad du väljer bort (koncentration)')
      ];
    case 'pröva':
      return [
        req(of('motprov').some(m => section(m.body, 'Mitt svar')), 'Minst ett motprov där du besvarat den starkaste invändningen (friktion)'),
        req(of('forskningsmöte').length > 0, 'Minst ett forskningsmöte: en människa utanför har prövat idén')
      ];
    case 'utveckla':
      return [
        req(of('experiment').some(e => section(e.body, 'Resultat')), 'Minst ett genomfört experiment eller arbetsprov med redovisat resultat')
      ];
    case 'ompröva':
      return [
        req(of('omprövning').length > 0, 'En omprövning: vad tror du nu, och varför?'),
        req(section(question.body, 'Lärdomar'), 'Du har skrivit vad cykeln lärde dig om ditt arbetssätt')
      ];
    case 'dela':
      return [
        req(section(question.body, 'Delat med'), 'Resultatet har delats med någon som kan granska eller använda det')
      ];
    default:
      return [];
  }
}

/* ---------- Revisorn ---------- */

function finding(nivå, princip, text, path) { return { nivå, princip, text, path: path || null }; }

/**
 * Revisorn granskar hela vaulten mot metoden och säger till när arbetet
 * glider ifrån den. Inget här kräver AI.
 */
function audit(notes, date) {
  const out = [];
  const of = typ => notes.filter(n => n.fm.typ === typ);
  const questions = of('forskningsfråga');
  const active = questions.filter(q => (q.fm.status || 'aktiv') === 'aktiv');

  // Envishet: för många öppna frågor samtidigt.
  if (active.length > MAX_AKTIVA_FRÅGOR) {
    out.push(finding('varning', 'Envishet',
      `Du har ${active.length} aktiva forskningsfrågor. Metoden tillåter högst ${MAX_AKTIVA_FRÅGOR}. Parkera eller lägg några att vila, så att lovande idéer faktiskt fördjupas.`));
  }

  for (const q of active) {
    const fas = q.fm.fas || 'utforska';
    const sedan = q.fm.fas_ändrad || noteDate(q);
    const dagar = sedan ? daysBetween(sedan, date) : 0;
    const titel = basename(q.path);
    if ((fas === 'utforska' || fas === 'kombinera') && dagar > 30) {
      out.push(finding('varning', 'Utforskning + koncentration',
        `"${titel}" har varit i fasen ${phaseOf(fas).namn} i ${dagar} dagar. Du utforskar utan att välja. Vilken hypotes är värd att fördjupa?`, q.path));
    }
    if (fas === 'utveckla' || fas === 'välj') {
      const linked = notes.filter(n => refersTo(n, q));
      if (!linked.some(n => n.fm.typ === 'motprov')) {
        out.push(finding('varning', 'Friktion',
          `"${titel}" fördjupas utan att någon invändning prövats. Skriv ett motprov innan du investerar mer.`, q.path));
      }
    }
  }

  // Inkubation: vilande frågor som är redo att återvända till.
  for (const q of questions.filter(q => q.fm.status === 'vilar' && q.fm.vila_till)) {
    if (daysBetween(String(q.fm.vila_till), date) >= 0) {
      out.push(finding('påminnelse', 'Återhämtning',
        `"${basename(q.path)}" har vilat klart. Återvänd med nya ögon: vad ser du nu som du inte såg innan?`, q.path));
    }
  }

  // Hypoteser utan motprov.
  for (const h of of('hypotes')) {
    const ålder = daysBetween(noteDate(h) || date, date);
    const harMotprov = of('motprov').some(m => linkTarget(m.fm.gäller) &&
      (linkTarget(m.fm.gäller) === h.path.replace(/\.md$/, '') || linkTarget(m.fm.gäller) === basename(h.path)));
    if (!harMotprov && ålder > 14 && (h.fm.status || 'oprövad') === 'oprövad') {
      out.push(finding('påminnelse', 'Ifrågasättande',
        `Hypotesen "${basename(h.path)}" har inte mött någon invändning på ${ålder} dagar.`, h.path));
    }
  }

  // Människor: AI kan inte ersätta verklig mänsklig mångfald.
  const möten = of('forskningsmöte').map(noteDate).filter(Boolean).sort();
  const senasteMöte = möten[möten.length - 1];
  if (active.length > 0 && (!senasteMöte || daysBetween(senasteMöte, date) > 30)) {
    out.push(finding('varning', 'Mångfald',
      senasteMöte
        ? `Inget forskningsmöte med en människa på ${daysBetween(senasteMöte, date)} dagar. AI-perspektiv ersätter inte oberoende människor.`
        : 'Inget forskningsmöte dokumenterat än. Vem utanför ditt huvud och utanför AI kan pröva idén?'));
  }

  // Tillit: öppna felrättningar.
  for (const k of of('felrättning').filter(k => (k.fm.status || 'öppen') === 'öppen')) {
    const ålder = daysBetween(noteDate(k) || date, date);
    if (ålder > 14) {
      out.push(finding('påminnelse', 'Tillit',
        `Felrättningen "${basename(k.path)}" har varit öppen i ${ålder} dagar. Vad ändrar vi i arbetssättet?`, k.path));
    }
  }

  // Tänk först: AI-konsultationer utan egna ord efteråt.
  for (const a of of('ai-konsultation')) {
    const ålder = daysBetween(noteDate(a) || date, date);
    if (ålder >= 2 && !section(a.body, 'Vad tar jag med mig')) {
      out.push(finding('påminnelse', 'Självständighet',
        `AI-konsultationen "${basename(a.path)}" saknar din sammanfattning med egna ord.`, a.path));
    }
  }

  const ai30 = of('ai-konsultation').filter(a => daysBetween(noteDate(a) || date, date) <= 30);
  const utanTanke = ai30.filter(a => a.fm.egen_tanke_först !== 'ja').length;
  if (ai30.length >= 3 && utanTanke / ai30.length > 0.5) {
    out.push(finding('varning', 'Självständighet',
      `${utanTanke} av ${ai30.length} AI-konsultationer senaste månaden gjordes innan du skrivit din egen uppfattning.`));
  }

  // Återkoppling: månatlig förmågegranskning.
  const granskningar = of('förmågegranskning').map(noteDate).filter(Boolean).sort();
  const senaste = granskningar[granskningar.length - 1];
  if (!senaste || daysBetween(senaste, date) > 35) {
    out.push(finding('påminnelse', 'Återkoppling',
      senaste ? 'Det är dags för månadens förmågegranskning.' : 'Gör din första förmågegranskning, så att vi kan se om du faktiskt blir bättre.'));
  }

  // Förslag: första uppdraget.
  if (active.length === 0 && questions.some(q => q.fm.status === 'förslag')) {
    out.push(finding('påminnelse', 'Riktning',
      'Du har ingen aktiv forskningsfråga. Det finns ett förslag i 01 RIKTNING. Gör det till ditt eller formulera en egen fråga.'));
  }

  return out.sort((a, b) => (a.nivå === b.nivå ? 0 : a.nivå === 'varning' ? -1 : 1));
}

/* ---------- Mått ---------- */

/** Mått på förmåga och självständighet, inte på produktion. */
function metrics(notes, date) {
  const of = typ => notes.filter(n => n.fm.typ === typ);
  const inom = (n, d) => daysBetween(noteDate(n) || date, date) <= d;
  const ai = of('ai-konsultation').filter(n => inom(n, 30));
  const övningar = of('övning').filter(n => inom(n, 30) && n.fm.utan_ai === 'ja');
  const granskningar = of('förmågegranskning').sort((a, b) => noteDate(a).localeCompare(noteDate(b)));
  const score = g => {
    const v = CAPABILITIES.map(([k]) => Number(g.fm[k])).filter(x => x >= 1 && x <= 5);
    return v.length ? v.reduce((s, x) => s + x, 0) / v.length : null;
  };
  const sista = granskningar[granskningar.length - 1];
  const förra = granskningar[granskningar.length - 2];
  let belagt = 0, tolkning = 0, spekulation = 0;
  for (const n of notes) {
    const b = String(n.body || '');
    belagt += (b.match(/\[!belagt\]/gi) || []).length;
    tolkning += (b.match(/\[!tolkning\]/gi) || []).length;
    spekulation += (b.match(/\[!spekulation\]/gi) || []).length;
  }
  return {
    aiKonsultationer: ai.length,
    tänktFörst: ai.filter(a => a.fm.egen_tanke_först === 'ja').length,
    övningarUtanAI: övningar.length,
    motprov: of('motprov').length,
    omprövningar: of('omprövning').length,
    felrättningar: of('felrättning').length,
    avslutadeCykler: of('forskningsfråga').reduce((s, q) => s + Math.max(0, Number(q.fm.cykel || 1) - 1), 0),
    förmåga: sista ? score(sista) : null,
    förmågaFörra: förra ? score(förra) : null,
    epistemik: { belagt, tolkning, spekulation }
  };
}

/* ---------- AI-konsultation ---------- */

/** Bygger den text som forskaren själv väljer att skicka till en AI. */
function buildPrompt({ roll, läge, titel, text }) {
  const r = ROLES[roll] || ROLES.motståndaren;
  const m = MODES[läge] || MODES.utveckling;
  return [
    `Du arbetar som "${r.namn}" i ForskarOS, ett system som ska göra forskaren mer självständig, inte mer beroende av AI.`,
    '',
    `Ditt uppdrag: ${r.uppdrag}`,
    '',
    `Läge: ${m.namn}. ${m.instruktion}`,
    '',
    'Regler (tillitskontraktet):',
    ...EPISTEMIC_CONTRACT.map((c, i) => `${i + 1}. ${c}`),
    '',
    `Här är mitt arbete, "${titel}":`,
    '',
    '"""',
    stripFrontmatter(text).trim(),
    '"""'
  ].join('\n');
}

/* ---------- Mallar ---------- */

function fm(fields) {
  const lines = Object.entries(fields)
    .filter(([, v]) => v !== undefined && v !== null)
    .map(([k, v]) => `${k}: ${typeof v === 'string' && /[:#[\]{}]/.test(v) ? JSON.stringify(v) : v}`);
  return `---\n${lines.join('\n')}\n---\n`;
}

const TYPES = {
  pass: {
    label: 'Forskarpass', folder: '08 REFLEKTION', prefix: 'Pass',
    render: ({ date, source, fråga }) => fm({ typ: 'forskarpass', datum: date, status: 'pågår', fråga }) + `# Forskarpass ${date}

> Tänk själv först. Be sedan en AI eller en människa om kritik.

## 1. Frågan jag försöker förstå
${source || ''}

## 2. Min egen förklaring – utan AI


## 3. Mångfald: tre verkligt olika perspektiv
- Perspektiv A:
- Perspektiv B:
- Perspektiv C:

## 4. Friktion: vad skulle visa att jag har fel?


## 5. Källor och evidens
- Källa:
- Vad källan faktiskt stöder:
- Osäkerhet:

## 6. Det jag inte förstår (bekvämt att vara obekväm)


## 7. Vad har förändrats i min uppfattning?


## 8. Nästa lilla genomförbara steg
- [ ]

## 9. Självständighet
> Vad kan jag nu förklara utan att konsultera en AI?

`
  },
  hypothesis: {
    label: 'Ny hypotes', folder: '02 HYPOTESER', prefix: 'Hypotes',
    render: ({ date, fråga }) => fm({ typ: 'hypotes', datum: date, status: 'oprövad', konfidens: 'okänd', fråga }) + `# Hypotes

## Hypotes (min formulering)


## Etablerad kunskap jag bygger på
> Ovanliga idéer blir starkare när de vilar på gedigen kunskap.


## Den ovanliga kombinationen
> Vilka fält, idéer eller metoder kombineras som sällan möts?


## Prediktioner
1.
2.

## Konkurrerande förklaringar
1.
2.

## Falsifiering: vilken observation skulle tala emot hypotesen?


## Försöksdesign


## Stödjande källor


## Motstridiga källor


## Vad skulle upptäckten göra möjligt? (framtiden)


## Beslut: pröva / omformulera / förkasta
`
  },
  friction: {
    label: 'Motprov', folder: '05 FRIKTION', prefix: 'Motprov',
    render: ({ date, source, fråga, gäller }) => fm({ typ: 'motprov', datum: date, status: 'öppet', fråga, gäller }) + `# Motprov

## Påstående som ska prövas
${source || ''}

## Starkaste motargumentet (steelman)


## Vad vore ett empiriskt, snarare än retoriskt, motbevis?


## Hur kan jag själv vara partisk?


## Vad säger den bäst underbyggda avvikande ståndpunkten?


## Vilka belägg saknas?


## Mitt svar efter att ha övervägt invändningarna


## Vad skulle övertyga mig om att ändra mig?
`
  },
  diversity: {
    label: 'Perspektivkarta', folder: '03 EVIDENS', prefix: 'Perspektivkarta',
    render: ({ date, source, fråga }) => fm({ typ: 'perspektivkarta', datum: date, fråga }) + `# Perspektivkarta

## Utgångsfråga
${source || ''}

| Perspektiv / fält | Vad det förklarar | Vad det missar | Källa att kontrollera |
|---|---|---|---|
| Kognitionsvetenskap | | | |
| Teknik / datavetenskap | | | |
| Filosofi / epistemologi | | | |
| Institutionellt / samhälleligt | | | |
| Oväntat fält | | | |

## Där perspektiven motsäger varandra


## En ny kombination att pröva


## Vilka verkliga människor behöver utmana analysen?
`
  },
  experiment: {
    label: 'Experiment / arbetsprov', folder: '04 EXPERIMENT', prefix: 'Experiment',
    render: ({ date, fråga }) => fm({ typ: 'experiment', datum: date, status: 'planerat', fråga }) + `# Experiment

> Skriv allt fram till "Resultat" innan du samlar in data. Då kan resultatet
> inte i efterhand forma vad du sa att du skulle pröva.

## Vilken hypotes prövas?


## Prediktion: vad förväntar jag mig?


## Vad räknas som att jag har fel?


## Metod och material


## Ny metod eller nytt verktyg?
> Många genombrott har gjorts möjliga av nya sätt att undersöka verkligheten.


## Resultat


## Avvikelser från planen


## Vad betyder resultatet, och vad betyder det inte?
`
  },
  change: {
    label: 'Omprövning', folder: '06 FÖRÄNDRING', prefix: 'Omprövning',
    render: ({ date, source, fråga }) => fm({ typ: 'omprövning', datum: date, fråga }) + `# Omprövning

## Vad trodde jag tidigare?
${source || ''}

## Vad tror jag nu?


## Vad fick mig att ändra uppfattning?


## Primärkällor och belägg


## Vad är ännu osäkert?


## Vilka handlingar ändrar jag?


## Vilken framtida observation kan få mig att ändra mig igen?
`
  },
  meeting: {
    label: 'Forskningsmöte', folder: '07 SAMVERKAN', prefix: 'Möte',
    render: ({ date, fråga }) => fm({ typ: 'forskningsmöte', datum: date, krets: 'nätverk', ny_kontakt: 'ja', fråga }) + `# Forskningsmöte

> krets: kärna (handledare, nära forskningspartner) eller nätverk.
> Nya kontakter tillför oftare nya perspektiv än upprepade samarbeten.

## Deltagare och expertområden


## Vad vill jag lära mig?


## Frågorna jag inte redan kan besvara
1.
2.

## Viktigaste invändningen jag fick


## Överenskommelser och källor


## Uppföljning
- [ ]
`
  },
  correction: {
    label: 'Felrättning', folder: '08 REFLEKTION', prefix: 'Felrättning',
    render: ({ date }) => fm({ typ: 'felrättning', datum: date, status: 'öppen' }) + `# Felrättning och tillit

## Tidigare påstående (mitt eller AI:ns)


## Varför var det fel, missvisande eller för tvärsäkert?


## Kontrollerade belägg


## Korrekt slutsats och osäkerhet


## Vad ändrar vi i arbetssättet?


## Hur kontrollerar vi att förbättringen fungerar?
`
  },
  exercise: {
    label: 'Övning utan AI', folder: '08 REFLEKTION', prefix: 'Övning',
    render: ({ date, fråga }) => fm({ typ: 'övning', datum: date, utan_ai: 'ja', förmåga: 'metodkompetens', fråga }) + `# Övning utan AI

> Fördjupning: lös en uppgift helt på egen hand. Bara så kan vi avgöra vad
> du faktiskt har lärt dig. Sätt utan_ai till "nej" om du tog hjälp.

## Uppgiften


## Min lösning


## Var det tog stopp


## Vad jag behöver träna mer på
`
  },
  review: {
    label: 'Förmågegranskning', folder: '08 REFLEKTION', prefix: 'Förmågegranskning',
    render: ({ date }) => fm(Object.assign({ typ: 'förmågegranskning', datum: date },
      Object.fromEntries(CAPABILITIES.map(([k]) => [k, ''])))) + `# Förmågegranskning ${date}

> Skatta varje förmåga 1–5 i egenskaperna ovan. Varje skattning ska bygga på
> ett konkret arbetsprov, länka till det. Det är en självskattning tills vi har
> oberoende bedömning. Det intressanta är inte totalsiffran, utan om du klarar
> mer krävande uppgifter med mindre hjälp.

${CAPABILITIES.map(([, namn, fråga]) => `## ${namn}\n> ${fråga}\n- Arbetsprov:\n- Motivering:\n`).join('\n')}
## Vad ska jag träna nästa månad?
`
  }
};

function questionNote({ date, titel, varför, status = 'aktiv' }) {
  return fm({ typ: 'forskningsfråga', datum: date, status, fas: 'utforska', fas_ändrad: date, cykel: 1 }) + `# ${titel}

## Varför är frågan värd tio år av mitt liv?
${varför || ''}

## Avgränsning


## Det jag väljer bort


## Lärdomar


## Delat med


## Fasbeslut
- ${date}: Frågan formulerades. Fas: Utforska.
`;
}

function ideaNote({ date, idé }) {
  return fm({ typ: 'idé', datum: date, status: 'parkerad' }) + `# Idé

${idé || ''}

> Parkerad, inte bortglömd. När en aktiv fråga är avslutad kan idén bli nästa.
> Varför lockar den, och vad har den gemensamt med det du redan undersöker?
`;
}

/** Lägger till en rad under "## Fasbeslut" (eller sist) i en frågas text. */
function appendPhaseLog(body, line) {
  const marker = '\n## Fasbeslut\n';
  const i = body.indexOf(marker);
  if (i < 0) return `${body.replace(/\s*$/, '')}\n\n## Fasbeslut\n- ${line}\n`;
  const start = i + marker.length;
  const nextHeading = body.indexOf('\n## ', start);
  const end = nextHeading < 0 ? body.length : nextHeading;
  const block = body.slice(start, end).replace(/\s*$/, '');
  return `${body.slice(0, start)}${block ? `${block}\n` : ''}- ${line}\n${body.slice(end).replace(/^\n*/, nextHeading < 0 ? '' : '\n')}`;
}

const engine = {
  PHASES, ROLES, MODES, CAPABILITIES, PRINCIPLES, EPISTEMIC_CONTRACT, MAX_AKTIVA_FRÅGOR, MIN_EGNA_ORD,
  today, addDays, daysBetween, phaseOf, nextPhase, linkTarget, refersTo, section, ownWords,
  phaseRequirements, audit, metrics, buildPrompt, appendPhaseLog, questionNote, ideaNote, TYPES
};

/* ======================================================================
 * 2. GRÄNSSNITTET
 * ====================================================================== */

const VIEW_TYPE = 'forskaros-dashboard';

function uniqueStamp() {
  return new Date().toISOString().replace(/[.:]/g, '-').slice(0, 19);
}

function safeName(text) {
  return String(text).replace(/[\\/:*?"<>|#^[\]]/g, '').replace(/\s+/g, ' ').trim().slice(0, 80) || 'Utan titel';
}

/** En enkel dialog med textfält. */
class FormModal extends Modal {
  constructor(app, { title, intro, fields, submit, onSubmit }) {
    super(app);
    Object.assign(this, { titleText: title, intro, fields, submit, onSubmit });
  }
  onOpen() {
    const el = this.contentEl;
    el.empty();
    el.addClass('forskaros-modal');
    el.createEl('h3', { text: this.titleText });
    if (this.intro) for (const p of [].concat(this.intro)) el.createEl('p', { text: p });
    const inputs = {};
    for (const f of this.fields) {
      el.createEl('label', { text: f.label, cls: 'forskaros-label' });
      inputs[f.key] = el.createEl(f.multiline ? 'textarea' : 'input', { cls: 'forskaros-input' });
      if (f.placeholder) inputs[f.key].setAttr('placeholder', f.placeholder);
    }
    const row = el.createDiv({ cls: 'forskaros-row' });
    for (const s of [].concat(this.submit)) {
      const b = row.createEl('button', { text: s.text, cls: s.cta ? 'mod-cta' : '' });
      b.addEventListener('click', () => {
        const values = Object.fromEntries(Object.entries(inputs).map(([k, i]) => [k, i.value.trim()]));
        const missing = this.fields.filter(f => f.required && !values[f.key] && !s.skipRequired);
        if (missing.length) { new Notice(`Fyll i: ${missing.map(f => f.label).join(', ')}`); return; }
        this.close();
        this.onSubmit(s.id || 'ok', values);
      });
    }
  }
  onClose() { this.contentEl.empty(); }
}

/** Dialog för att lämna en fas: visar kraven och kräver motivering om de inte är uppfyllda. */
class PhaseModal extends Modal {
  constructor(app, plugin, question, requirements) {
    super(app);
    Object.assign(this, { plugin, question, requirements });
  }
  onOpen() {
    const el = this.contentEl;
    el.empty();
    el.addClass('forskaros-modal');
    const cur = phaseOf(this.question.fm.fas);
    const nxt = nextPhase(this.question.fm.fas);
    el.createEl('h3', { text: `${cur.namn} → ${nxt.namn}` });
    el.createEl('p', { text: nxt.fråga });
    const list = el.createEl('ul', { cls: 'forskaros-checklist' });
    for (const r of this.requirements) {
      list.createEl('li', { text: `${r.ok ? '✓' : '○'} ${r.text}`, cls: r.ok ? 'is-ok' : 'is-missing' });
    }
    const allOk = this.requirements.every(r => r.ok);
    let reason = null;
    if (!allOk) {
      el.createEl('p', { text: 'Allt är inte gjort. Du kan gå vidare ändå, men motiveringen sparas öppet i frågan.' });
      reason = el.createEl('textarea', { cls: 'forskaros-input' });
      reason.setAttr('placeholder', 'Varför går du vidare ändå?');
    }
    const row = el.createDiv({ cls: 'forskaros-row' });
    const go = row.createEl('button', { text: allOk ? `Gå vidare till ${nxt.namn}` : 'Gå vidare ändå', cls: 'mod-cta' });
    go.addEventListener('click', async () => {
      const why = reason ? reason.value.trim() : '';
      if (!allOk && !why) { new Notice('Skriv en motivering.'); return; }
      this.close();
      const missing = this.requirements.filter(r => !r.ok).map(r => r.text);
      await this.plugin.advancePhase(this.question, why, missing);
    });
    const cancel = row.createEl('button', { text: 'Stanna kvar' });
    cancel.addEventListener('click', () => this.close());
  }
  onClose() { this.contentEl.empty(); }
}

/** AI-konsultation: välj roll och läge, se exakt vad som delas, kopiera själv. */
class AIModal extends Modal {
  constructor(app, plugin, file, text, words) {
    super(app);
    Object.assign(this, { plugin, file, text, words });
  }
  onOpen() {
    const el = this.contentEl;
    el.empty();
    el.addClass('forskaros-modal');
    el.createEl('h3', { text: 'Be en AI om hjälp' });
    const tänktFörst = this.words >= MIN_EGNA_ORD;
    el.createEl('p', {
      cls: tänktFörst ? 'forskaros-ok' : 'forskaros-warning',
      text: tänktFörst
        ? `Du har skrivit ${this.words} egna ord i anteckningen. Bra, AI:n får utgå från din uppfattning.`
        : `Du har bara skrivit ${this.words} egna ord. Tänk-först-principen: skriv din egen uppfattning (minst ${MIN_EGNA_ORD} ord) innan du ber om hjälp. Bara prestationsläget är öppet.`
    });

    el.createEl('label', { text: 'Roll', cls: 'forskaros-label' });
    const roll = el.createEl('select', { cls: 'forskaros-input' });
    for (const [id, r] of Object.entries(ROLES)) roll.createEl('option', { text: r.namn, value: id });
    roll.value = 'motståndaren';

    el.createEl('label', { text: 'Läge', cls: 'forskaros-label' });
    const läge = el.createEl('select', { cls: 'forskaros-input' });
    for (const [id, m] of Object.entries(MODES)) {
      const o = läge.createEl('option', { text: `${m.namn} – ${m.beskrivning}`, value: id });
      if (!tänktFörst && id !== 'prestation') o.disabled = true;
    }
    läge.value = tänktFörst ? 'utveckling' : 'prestation';

    el.createEl('label', { text: 'Exakt detta delas. Inget skickas automatiskt.', cls: 'forskaros-label' });
    const preview = el.createEl('textarea', { cls: 'forskaros-input forskaros-preview' });
    preview.readOnly = true;
    const update = () => {
      preview.value = buildPrompt({ roll: roll.value, läge: läge.value, titel: this.file.basename, text: this.text });
    };
    roll.addEventListener('change', update);
    läge.addEventListener('change', update);
    update();

    const row = el.createDiv({ cls: 'forskaros-row' });
    const copy = row.createEl('button', { text: 'Kopiera och logga konsultationen', cls: 'mod-cta' });
    copy.addEventListener('click', async () => {
      try { await navigator.clipboard.writeText(preview.value); } catch (e) { /* kopiera manuellt */ }
      this.close();
      await this.plugin.logConsultation(this.file, roll.value, läge.value, tänktFörst, preview.value);
    });
  }
  onClose() { this.contentEl.empty(); }
}

class ForskarOSView extends ItemView {
  constructor(leaf, plugin) {
    super(leaf);
    this.plugin = plugin;
  }
  getViewType() { return VIEW_TYPE; }
  getDisplayText() { return 'ForskarOS'; }
  getIcon() { return 'brain'; }
  async onOpen() { await this.renderDashboard(); }

  async renderDashboard() {
    const root = this.contentEl;
    const notes = await this.plugin.collectNotes();
    const date = today();
    root.empty();
    root.addClass('forskaros-panel');
    root.createEl('div', { cls: 'forskaros-kicker', text: 'FORSKAROS' });
    const dayIndex = daysBetween('2026-01-01', date);
    root.createEl('h2', { text: PRINCIPLES[((dayIndex % PRINCIPLES.length) + PRINCIPLES.length) % PRINCIPLES.length] });

    // Forskningsfrågor och deras fas i cykeln.
    const questions = notes.filter(n => n.fm.typ === 'forskningsfråga');
    const active = questions.filter(q => (q.fm.status || 'aktiv') === 'aktiv');
    root.createEl('h4', { text: 'Dina forskningsfrågor' });
    if (!active.length) {
      const förslag = questions.find(q => q.fm.status === 'förslag');
      root.createEl('p', { text: 'Ingen aktiv fråga. Forskning börjar med ett problem du är beredd att ägna tio år åt att förstå.' });
      const row = root.createDiv({ cls: 'forskaros-row' });
      row.createEl('button', { text: 'Formulera en forskningsfråga', cls: 'mod-cta' })
        .addEventListener('click', () => this.plugin.newQuestion());
      if (förslag) {
        row.createEl('button', { text: `Anta förslaget: ${basename(förslag.path)}` })
          .addEventListener('click', () => this.plugin.adoptQuestion(förslag));
      }
    }
    for (const q of active) this.renderQuestion(root, q, notes);
    const vilande = questions.filter(q => q.fm.status === 'vilar');
    if (vilande.length) {
      root.createEl('p', { cls: 'forskaros-muted', text: `Vilar: ${vilande.map(q => `${basename(q.path)} (till ${q.fm.vila_till || '?'})`).join(', ')}` });
    }

    // Revisorn.
    const findings = audit(notes, date);
    root.createEl('h4', { text: 'Revisorn' });
    if (!findings.length) root.createEl('p', { cls: 'forskaros-muted', text: 'Inget att anmärka just nu.' });
    for (const f of findings.slice(0, 8)) {
      const item = root.createDiv({ cls: `forskaros-finding is-${f.nivå}` });
      item.createEl('b', { text: f.princip });
      item.createEl('span', { text: f.text });
      if (f.path) item.addEventListener('click', () => void this.plugin.openPath(f.path));
    }

    // Självständighet.
    const m = metrics(notes, date);
    root.createEl('h4', { text: 'Självständighet, senaste 30 dagarna' });
    const grid = root.createDiv({ cls: 'forskaros-metrics' });
    const card = (value, label) => {
      const c = grid.createDiv({ cls: 'forskaros-metric' });
      c.createEl('strong', { text: value });
      c.createEl('span', { text: label });
    };
    card(m.aiKonsultationer ? `${m.tänktFörst}/${m.aiKonsultationer}` : '–', 'AI-frågor där du tänkte först');
    card(String(m.övningarUtanAI), 'Övningar utan AI');
    card(m.förmåga ? m.förmåga.toFixed(1) : '–', m.förmågaFörra ? `Förmåga (förra: ${m.förmågaFörra.toFixed(1)})` : 'Förmåga (1–5)');
    card(String(m.motprov), 'Motprov');
    card(String(m.omprövningar), 'Omprövningar');
    card(String(m.felrättningar), 'Felrättningar');
    const e = m.epistemik;
    root.createEl('p', { cls: 'forskaros-muted', text: `Märkta påståenden: ${e.belagt} belagda · ${e.tolkning} tolkningar · ${e.spekulation} spekulationer` });

    // Skapa.
    root.createEl('h4', { text: 'Arbeta' });
    const actions = root.createDiv({ cls: 'forskaros-actions' });
    const btn = (text, fn) => actions.createEl('button', { text }).addEventListener('click', fn);
    btn('Parkera en idé', () => this.plugin.parkIdea());
    btn('Be AI om hjälp', () => void this.plugin.consultAI());
    for (const [type, spec] of Object.entries(TYPES)) btn(spec.label, () => void this.plugin.createNote(type));
    root.createEl('div', { cls: 'forskaros-warning', text: 'Du ska kunna förklara slutsatsen utan AI. Fler anteckningar är inte samma sak som mer kunskap.' });
    root.createEl('button', { text: 'Läs arbetsmetoden' })
      .addEventListener('click', () => void this.plugin.openPath('00 START/Arbetsmetod.md'));
  }

  renderQuestion(root, q, notes) {
    const box = root.createDiv({ cls: 'forskaros-question' });
    const title = box.createEl('div', { cls: 'forskaros-question-title', text: basename(q.path) });
    title.addEventListener('click', () => void this.plugin.openPath(q.path));
    const fas = q.fm.fas || 'utforska';
    const steps = box.createDiv({ cls: 'forskaros-steps' });
    PHASES.forEach((p, i) => {
      const cls = i < phaseIndex(fas) ? 'is-done' : i === phaseIndex(fas) ? 'is-current' : '';
      steps.createDiv({ cls: `forskaros-step ${cls}`, text: p.namn });
    });
    const p = phaseOf(fas);
    box.createEl('div', { cls: 'forskaros-muted', text: `Cykel ${q.fm.cykel || 1} · ${p.symbios}` });
    box.createEl('div', { cls: 'forskaros-phase-question', text: p.fråga });
    const reqs = phaseRequirements(q, notes);
    const list = box.createEl('ul', { cls: 'forskaros-checklist' });
    for (const r of reqs) list.createEl('li', { text: `${r.ok ? '✓' : '○'} ${r.text}`, cls: r.ok ? 'is-ok' : 'is-missing' });
    const row = box.createDiv({ cls: 'forskaros-row' });
    row.createEl('button', { text: `Gå vidare till ${nextPhase(fas).namn}` })
      .addEventListener('click', () => new PhaseModal(this.app, this.plugin, q, reqs).open());
    row.createEl('button', { text: 'Lägg att vila' })
      .addEventListener('click', () => void this.plugin.restQuestion(q));
  }
}

module.exports = class ForskarOSPlugin extends Plugin {
  async onload() {
    this.registerView(VIEW_TYPE, leaf => new ForskarOSView(leaf, this));
    this.addRibbonIcon('brain', 'Öppna ForskarOS', () => void this.activateDashboard());
    this.addCommand({ id: 'open-dashboard', name: 'Öppna ForskarOS-panelen', callback: () => void this.activateDashboard() });
    this.addCommand({ id: 'new-question', name: 'Ny forskningsfråga', callback: () => this.newQuestion() });
    this.addCommand({ id: 'park-idea', name: 'Parkera en idé', callback: () => this.parkIdea() });
    this.addCommand({ id: 'consult-ai', name: 'Be AI om hjälp (tänk först)', callback: () => void this.consultAI() });
    this.addCommand({ id: 'advance-phase', name: 'Gå vidare till nästa fas', callback: () => void this.advanceFromActive() });
    for (const [type, spec] of Object.entries(TYPES)) {
      this.addCommand({ id: `new-${type}`, name: spec.label, callback: () => void this.createNote(type) });
    }
    for (const [kind, label] of [['belagt', 'belagt'], ['tolkning', 'tolkning'], ['spekulation', 'spekulation']]) {
      this.addCommand({
        id: `mark-${kind}`,
        name: `Märk markerad text som ${label}`,
        editorCallback: editor => {
          const text = editor.getSelection() || '';
          const body = text.split('\n').map(l => `> ${l}`).join('\n');
          editor.replaceSelection(`> [!${kind}]\n${body}\n`);
        }
      });
    }
    let timer = null;
    const refresh = () => { clearTimeout(timer); timer = setTimeout(() => this.refreshDashboard(), 400); };
    if (this.app.metadataCache && this.app.metadataCache.on) this.registerEvent(this.app.metadataCache.on('changed', refresh));
  }

  /** Läser alla anteckningar som har en ForskarOS-typ. */
  async collectNotes() {
    const notes = [];
    for (const file of this.app.vault.getMarkdownFiles()) {
      const cache = this.app.metadataCache && this.app.metadataCache.getFileCache(file);
      const front = cache && cache.frontmatter;
      if (!front || !front.typ) continue;
      const body = await this.app.vault.cachedRead(file);
      const created = file.stat && file.stat.ctime ? today(new Date(file.stat.ctime)) : '';
      notes.push({ path: file.path, fm: front, body, created });
    }
    return notes;
  }

  /** Frågan som nya anteckningar ska kopplas till. */
  async focusQuestion() {
    const active = this.app.workspace.getActiveFile();
    const notes = await this.collectNotes();
    if (active) {
      const n = notes.find(x => x.path === active.path);
      if (n && n.fm.typ === 'forskningsfråga') return n;
      if (n && n.fm.fråga) {
        const q = notes.find(x => x.fm.typ === 'forskningsfråga' && refersTo(n, x));
        if (q) return q;
      }
    }
    const aktiva = notes.filter(x => x.fm.typ === 'forskningsfråga' && (x.fm.status || 'aktiv') === 'aktiv');
    return aktiva.length === 1 ? aktiva[0] : null;
  }

  async ensureFolder(folder) {
    let current = '';
    for (const part of folder.split('/')) {
      current = current ? `${current}/${part}` : part;
      if (!(await this.app.vault.adapter.exists(current))) await this.app.vault.createFolder(current);
    }
  }

  async uniquePath(folder, name) {
    await this.ensureFolder(folder);
    let path = `${folder}/${name}.md`;
    let i = 1;
    while (await this.app.vault.adapter.exists(path)) path = `${folder}/${name}-${i++}.md`;
    return path;
  }

  async openPath(path) {
    const file = this.app.vault.getAbstractFileByPath(path);
    if (!file) { new Notice(`Hittar inte ${path}`); return; }
    await this.app.workspace.getLeaf(true).openFile(file);
  }

  async createNote(type) {
    const spec = TYPES[type];
    if (!spec) return null;
    try {
      const active = this.app.workspace.getActiveFile();
      const source = active ? `[[${active.path.replace(/\.md$/, '')}]]` : '';
      const q = await this.focusQuestion();
      const fråga = q ? `[[${q.path.replace(/\.md$/, '')}]]` : undefined;
      const gäller = type === 'friction' && active && /^02 HYPOTESER\//.test(active.path) ? source : undefined;
      const path = await this.uniquePath(spec.folder, `${spec.prefix} ${uniqueStamp()}`);
      const file = await this.app.vault.create(path, spec.render({ date: today(), source, fråga, gäller }));
      await this.app.workspace.getLeaf(true).openFile(file);
      this.refreshDashboard();
      new Notice(`${spec.label} skapad${q ? ` för "${basename(q.path)}"` : ''}`);
      return file;
    } catch (error) {
      console.error('ForskarOS createNote failed', error);
      new Notice('Kunde inte skapa anteckningen. Se utvecklarkonsolen.');
      return null;
    }
  }

  newQuestion() {
    void (async () => {
      const notes = await this.collectNotes();
      const aktiva = notes.filter(n => n.fm.typ === 'forskningsfråga' && (n.fm.status || 'aktiv') === 'aktiv');
      const full = aktiva.length >= MAX_AKTIVA_FRÅGOR;
      new FormModal(this.app, {
        title: 'Ny forskningsfråga',
        intro: full
          ? [`Du har redan ${aktiva.length} aktiva frågor: ${aktiva.map(q => basename(q.path)).join(', ')}.`,
            'Envis med frågan, inte med svaret. Ska den nya idén parkeras tills en fråga är avslutad?']
          : ['Formulera frågan själv. Den ska vara värd att ägna tio år åt att förstå.'],
        fields: [
          { key: 'titel', label: 'Frågan, i en mening', required: true },
          { key: 'varför', label: 'Varför är den värd din tid? (engagemanget måste komma från dig)', multiline: true, required: !full }
        ],
        submit: full
          ? [{ id: 'park', text: 'Parkera som idé', cta: true, skipRequired: false },
            { id: 'create', text: 'Skapa ändå' }]
          : [{ id: 'create', text: 'Skapa frågan', cta: true }],
        onSubmit: async (id, v) => {
          if (id === 'park') return this.saveIdea(`${v.titel}\n\n${v.varför || ''}`.trim());
          if (!v.varför) { new Notice('Skriv varför frågan är värd din tid.'); return; }
          const path = await this.uniquePath('01 RIKTNING', safeName(v.titel));
          const file = await this.app.vault.create(path, questionNote({ date: today(), titel: v.titel, varför: v.varför }));
          await this.app.workspace.getLeaf(true).openFile(file);
          this.refreshDashboard();
        }
      }).open();
    })();
  }

  async adoptQuestion(q) {
    const file = this.app.vault.getAbstractFileByPath(q.path);
    if (!file) return;
    await this.app.fileManager.processFrontMatter(file, f => {
      f.status = 'aktiv'; f.fas = 'utforska'; f.fas_ändrad = today(); f.datum = today();
    });
    await this.openPath(q.path);
    new Notice('Frågan är din nu. Börja med att skriva varför den är värd din tid.');
    this.refreshDashboard();
  }

  parkIdea() {
    new FormModal(this.app, {
      title: 'Parkera en idé',
      intro: ['Nya idéer är värdefulla. Parkera dem i stället för att byta fråga, så att den du arbetar med hinner fördjupas.'],
      fields: [{ key: 'idé', label: 'Idén', multiline: true, required: true }],
      submit: [{ text: 'Parkera', cta: true }],
      onSubmit: (_, v) => this.saveIdea(v.idé)
    }).open();
  }

  async saveIdea(text) {
    const first = String(text).split('\n')[0];
    const path = await this.uniquePath('01 RIKTNING/Idébank', safeName(first));
    await this.app.vault.create(path, ideaNote({ date: today(), idé: text }));
    new Notice('Idén är parkerad i 01 RIKTNING/Idébank.');
    this.refreshDashboard();
  }

  async advanceFromActive() {
    const q = await this.focusQuestion();
    if (!q) { new Notice('Öppna den forskningsfråga du vill gå vidare med.'); return; }
    const notes = await this.collectNotes();
    new PhaseModal(this.app, this, q, phaseRequirements(q, notes)).open();
  }

  async advancePhase(q, motivering, saknas) {
    const file = this.app.vault.getAbstractFileByPath(q.path);
    if (!file) return;
    const cur = phaseOf(q.fm.fas);
    const nxt = nextPhase(q.fm.fas);
    const nyCykel = cur.id === 'dela';
    await this.app.fileManager.processFrontMatter(file, f => {
      f.fas = nxt.id;
      f.fas_ändrad = today();
      if (nyCykel) f.cykel = Number(f.cykel || 1) + 1;
    });
    let line = `${today()}: ${cur.namn} → ${nxt.namn}${nyCykel ? ' (ny cykel: resultaten förändrar nästa varv)' : ''}.`;
    if (saknas.length) line += ` Gick vidare trots att detta saknades: ${saknas.join('; ')}. Motivering: ${motivering}`;
    const body = await this.app.vault.read(file);
    await this.app.vault.modify(file, appendPhaseLog(body, line));
    new Notice(`Fas: ${nxt.namn}. ${nxt.fråga}`);
    this.refreshDashboard();
  }

  async restQuestion(q) {
    const file = this.app.vault.getAbstractFileByPath(q.path);
    if (!file) return;
    const till = addDays(today(), 14);
    await this.app.fileManager.processFrontMatter(file, f => { f.status = 'vilar'; f.vila_till = till; });
    const body = await this.app.vault.read(file);
    await this.app.vault.modify(file, appendPhaseLog(body, `${today()}: Lagd att vila till ${till} (inkubation).`));
    new Notice(`"${basename(q.path)}" vilar till ${till}. Revisorn påminner dig.`);
    this.refreshDashboard();
  }

  async consultAI() {
    const file = this.app.workspace.getActiveFile();
    if (!file) { new Notice('Öppna anteckningen du vill ha hjälp med.'); return; }
    const text = await this.app.vault.read(file);
    new AIModal(this.app, this, file, text, ownWords(text)).open();
  }

  async logConsultation(file, roll, läge, tänktFörst, prompt) {
    const q = await this.focusQuestion();
    const path = await this.uniquePath('08 REFLEKTION/AI', `AI ${ROLES[roll].namn} ${uniqueStamp()}`);
    const content = fm({
      typ: 'ai-konsultation', datum: today(), roll, läge,
      egen_tanke_först: tänktFörst ? 'ja' : 'nej',
      källa: `[[${file.path.replace(/\.md$/, '')}]]`,
      fråga: q ? `[[${q.path.replace(/\.md$/, '')}]]` : undefined
    }) + `# AI-konsultation: ${ROLES[roll].namn}

> Texten nedan är kopierad. Klistra in den i den AI du väljer, och klistra
> sedan in svaret här. Granska det innan du tar med dig något.

## Svaret (klistra in)


## Granskning: vad är belagt, vad är tolkning, vad är spekulation?


## Vad håller jag inte med om?


## Vad tar jag med mig – med egna ord?


## Det som skickades
\`\`\`\`text
${prompt}
\`\`\`\`
`;
    const created = await this.app.vault.create(path, content);
    await this.app.workspace.getLeaf(true).openFile(created);
    new Notice('Texten är kopierad. Klistra in svaret i loggen och skriv vad du tar med dig, med egna ord.');
    this.refreshDashboard();
  }

  refreshDashboard() {
    for (const leaf of this.app.workspace.getLeavesOfType(VIEW_TYPE)) {
      if (leaf.view && typeof leaf.view.renderDashboard === 'function') void leaf.view.renderDashboard();
    }
  }

  async activateDashboard() {
    let leaf = this.app.workspace.getLeavesOfType(VIEW_TYPE)[0];
    if (!leaf) {
      leaf = this.app.workspace.getRightLeaf(false) || this.app.workspace.getLeaf(true);
      await leaf.setViewState({ type: VIEW_TYPE, active: true });
    }
    await this.app.workspace.revealLeaf(leaf);
  }
};

module.exports.engine = engine;
