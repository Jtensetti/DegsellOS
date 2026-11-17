'use strict';

/*
 * ForskarOS Core
 *
 * Ett tillägg som får operativsystemet att hjälpa forskaren arbeta enligt
 * arbetsmetoden: forskningscykeln, krav på eget utkast före AI-hjälp,
 * epistemisk märkning, granskning av vaulten och mått på självständighet.
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

/** Forskningscykeln. Efter Dela börjar nästa cykel. */
const PHASES = [
  { id: 'utforska', namn: 'Utforska',
    fråga: 'Vilka verkligt olika sätt finns det att förstå problemet?' },
  { id: 'kombinera', namn: 'Kombinera',
    fråga: 'Vilken ovanlig kombination vilar på gedigen, etablerad kunskap?' },
  { id: 'välj', namn: 'Välj',
    fråga: 'Vilken enda hypotes är värd att fördjupa, och hur kan den visa sig fel?' },
  { id: 'pröva', namn: 'Pröva',
    fråga: 'Vad är den starkaste invändningen, och vad säger en människa utanför?' },
  { id: 'utveckla', namn: 'Utveckla',
    fråga: 'Vilket arbete, experiment eller ny metod prövar idén på riktigt?' },
  { id: 'ompröva', namn: 'Ompröva',
    fråga: 'Vad har förändrats i din uppfattning, och vad gör du annorlunda?' },
  { id: 'dela', namn: 'Dela',
    fråga: 'Vem ska kunna granska, använda och utmana resultatet?' }
];

/** Verktyg per fas (se 00 START/Verktygslåda). */
const PHASE_TOOLS = {
  utforska: 'Zotero, OpenAlex, DiVA, perspektivkarta',
  kombinera: 'draw.io, Freeplane, hypotes',
  välj: 'OSF-förregistrering, etikprövning, fokusläge',
  pröva: 'motprov, forskningsmöte, lokal AI',
  utveckla: 'JASP, jamovi, labbet (R, Python), Speech Note, Taguette',
  ompröva: 'omprövning, felrättning, förmågegranskning',
  dela: 'Zettlr, LibreOffice, Pandoc, Zenodo'
};

const MAX_AKTIVA_FRÅGOR = 2;
/** Aktiva plus vilande. Vila ska inte bli ett sätt att runda gränsen ovan. */
const MAX_ÖPPNA_FRÅGOR = 4;
/** Sätt att avsluta en fråga. Förkastad är ett resultat, inte ett misslyckande. */
const UTFALL = { besvarad: 'Besvarad', förkastad: 'Hypotesen förkastad', övergiven: 'Övergiven' };
const MIN_EGNA_ORD = 50;

/** Uppgifter som en AI-konsultation kan ha. */
const ROLES = {
  perspektiv: {
    namn: 'Alternativa perspektiv',
    uppdrag: 'Jämför min idé med minst två andra teoretiska utgångspunkter, gärna från fält jag inte nämnt. Peka ut var perspektiven motsäger varandra och vilka forskningsluckor som finns.'
  },
  kritik: {
    namn: 'Kritisk granskning',
    uppdrag: 'Försök motbevisa hypotesen. Redovisa de starkaste invändningarna, alternativa förklaringar och vilken evidens som skulle avgöra frågan.'
  },
  handledning: {
    namn: 'Handledning',
    uppdrag: 'Hjälp mig utveckla metodiska och teoretiska färdigheter jag saknar. Börja med att ta reda på vad jag redan kan.'
  },
  metod: {
    namn: 'Metod och analys',
    uppdrag: 'Hjälp mig med försöksdesign, analys och reproducerbar dokumentation. Besluten om forskningen fattar jag.'
  },
  uppfoljning: {
    namn: 'Uppföljning',
    uppdrag: 'Granska mina tidigare slutsatser. Leta efter fel, för säkra påståenden och sådant jag sagt att jag skulle göra men inte gjort.'
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

/** Regler som skickas med varje AI-konsultation. */
const EPISTEMIC_CONTRACT = [
  'Märk varje viktigt påstående som [BELAGT] (med källa), [TOLKNING] eller [SPEKULATION].',
  'Förväxla inte rimlighet med sanning. Säg när du inte vet.',
  'Anpassa inte slutsatsen efter hur säker jag verkar. Kritisera svaga idéer och lyft starka.',
  'Om du upptäcker att du tidigare haft fel, säg det öppet.',
  'Utgå från det jag har skrivit, i stället för att börja om från början.'
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

/** Ifyllda rader i en tabell under en rubrik (mallens tomma rader räknas inte). */
function filledRows(body, prefix) {
  return section(body, prefix).split('\n').filter(l => l.startsWith('|')).length;
}

/** Har tabellraden som börjar med etiketten fått innehåll? */
function rowFilled(body, label) {
  const row = stripFrontmatter(body).split('\n').find(l => l.trim().startsWith(`| ${label}`));
  return Boolean(row) && row.split('|').slice(2).some(c => c.trim());
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
  const kartor = of('perspektivkarta');
  const möten = of('forskningsmöte');
  const sammanfattning = countWords(section(question.body, 'Sammanfattning för någon utanför'));
  switch (question.fm.fas || 'utforska') {
    case 'utforska':
      return [
        req(countWords(section(question.body, 'Varför')) >= 30, 'Motiveringen till frågan är minst 30 ord'),
        req(kartor.some(k => filledRows(k.body, 'Utgångsfråga') >= 3), 'En perspektivkarta med minst tre ifyllda perspektiv'),
        req(kartor.some(k => rowFilled(k.body, 'Oväntat fält')), 'Perspektivkartan har ett perspektiv från ett oväntat fält'),
        req(kartor.some(k => section(k.body, 'Där perspektiven motsäger varandra')), 'Perspektivkartan anger var perspektiven motsäger varandra')
      ];
    case 'kombinera':
      return [
        req(hyps.length > 0, 'Minst en hypotes'),
        req(hyps.some(h => section(h.body, 'Etablerad kunskap')), 'Hypotesen anger vilken etablerad kunskap den bygger på'),
        req(hyps.some(h => section(h.body, 'Den ovanliga kombinationen')), 'Hypotesen anger vad som är nytt'),
        req(hyps.some(h => section(h.body, 'Vilket etablerat antagande')), 'Hypotesen anger vilket etablerat antagande den utmanar')
      ];
    case 'välj':
      return [
        req(hyps.some(h => section(h.body, 'Falsifiering')), 'En hypotes har ett falsifieringskriterium'),
        req(hyps.some(h => section(h.body, 'Prediktioner')), 'En hypotes har konkreta prediktioner'),
        req(hyps.some(h => h.fm.konfidens && h.fm.konfidens !== 'okänd'), 'Hypotesens konfidens är angiven (låg, medel eller hög)'),
        req(section(question.body, 'Om frågan besvaras'), 'Frågan anger vad som förändras om den besvaras'),
        req(section(question.body, 'Det jag väljer bort'), 'Avgränsningen anger vad som väljs bort')
      ];
    case 'pröva':
      return [
        req(of('motprov').some(m => section(m.body, 'Mitt svar')), 'Minst ett besvarat motprov'),
        req(möten.some(m => section(m.body, 'Viktigaste invändningen')), 'Ett forskningsmöte där någon utanför projektet framfört en invändning')
      ];
    case 'utveckla':
      return [
        req(of('experiment').some(e => section(e.body, 'Resultat')), 'Minst ett experiment eller arbetsprov med resultat')
      ];
    case 'ompröva':
      return [
        req(of('omprövning').length > 0, 'Minst en omprövning'),
        req(section(question.body, 'Lärdomar'), 'Lärdomar om arbetssättet är nedskrivna')
      ];
    case 'dela':
      return [
        req(sammanfattning >= 50 && sammanfattning <= 200, `En sammanfattning för någon utanför fältet, 50–200 ord (nu ${sammanfattning})`),
        req(section(question.body, 'Delat med'), 'Resultatet har delats med någon som kan granska det')
      ];
    default:
      return [];
  }
}

/* ---------- Granskning av vaulten ---------- */

function finding(nivå, princip, text, path) { return { nivå, princip, text, path: path || null }; }

/**
 * Granskar hela vaulten mot arbetsmetoden och listar det som behöver
 * åtgärdas. Regelbaserat, ingen AI.
 */
function audit(notes, date) {
  const out = [];
  const of = typ => notes.filter(n => n.fm.typ === typ);
  const questions = of('forskningsfråga');
  const active = questions.filter(q => (q.fm.status || 'aktiv') === 'aktiv');

  // Envishet: för många öppna frågor samtidigt.
  if (active.length > MAX_AKTIVA_FRÅGOR) {
    out.push(finding('varning', 'För många frågor',
      `${active.length} aktiva forskningsfrågor. Arbetsmetoden rekommenderar högst ${MAX_AKTIVA_FRÅGOR}. Parkera eller lägg några att vila.`));
  }

  // Öppna frågor (aktiva + vilande).
  const öppna = questions.filter(q => ['aktiv', 'vilar'].includes(q.fm.status || 'aktiv'));
  if (öppna.length > MAX_ÖPPNA_FRÅGOR) {
    out.push(finding('varning', 'Många öppna frågor',
      `${öppna.length} frågor är aktiva eller vilar. Avsluta några med ett utfall (besvarad, förkastad eller övergiven).`));
  }

  // Påbörjade jämfört med avslutade: fler nya frågor än avslutade är det
  // mönster arbetsmetoden ska fånga.
  const påbörjade90 = questions.filter(q => q.fm.status !== 'förslag' && noteDate(q) && daysBetween(noteDate(q), date) <= 90);
  const avslutade90 = questions.filter(q => q.fm.status === 'avslutad' && q.fm.avslutad && daysBetween(String(q.fm.avslutad), date) <= 90);
  if (påbörjade90.length >= 3 && avslutade90.length === 0) {
    out.push(finding('varning', 'Påbörjat mer än avslutat',
      `${påbörjade90.length} frågor påbörjade de senaste 90 dagarna och ingen avslutad.`));
  }

  for (const q of questions.filter(q => q.fm.status === 'vilar' && Number(q.fm.vilat || 0) >= 3)) {
    out.push(finding('påminnelse', 'Vilar ofta',
      `"${basename(q.path)}" har lagts att vila ${q.fm.vilat} gånger. Ta upp den eller avsluta den med ett utfall.`, q.path));
  }

  for (const q of active) {
    const fas = q.fm.fas || 'utforska';
    const sedan = q.fm.fas_ändrad || noteDate(q);
    const dagar = sedan ? daysBetween(sedan, date) : 0;
    const titel = basename(q.path);
    if ((fas === 'utforska' || fas === 'kombinera') && dagar > 30) {
      out.push(finding('varning', 'Står still',
        `"${titel}" har varit i fasen ${phaseOf(fas).namn} i ${dagar} dagar utan att en hypotes valts.`, q.path));
    }
    if (fas === 'utveckla' || fas === 'välj') {
      const linked = notes.filter(n => refersTo(n, q));
      if (!linked.some(n => n.fm.typ === 'motprov')) {
        out.push(finding('varning', 'Ingen kritik',
          `"${titel}" har inget motprov än.`, q.path));
      }
    }
  }

  // Inkubation: vilande frågor som är redo att återvända till.
  for (const q of questions.filter(q => q.fm.status === 'vilar' && q.fm.vila_till)) {
    if (daysBetween(String(q.fm.vila_till), date) >= 0) {
      out.push(finding('påminnelse', 'Vila slut',
        `"${basename(q.path)}" har vilat färdigt.`, q.path));
    }
  }

  // Hypoteser utan motprov.
  for (const h of of('hypotes')) {
    const ålder = daysBetween(noteDate(h) || date, date);
    // Ett motprov gäller hypotesen om det pekar på den, eller om det inte pekar
    // på någon särskild hypotes men hör till samma forskningsfråga.
    const harMotprov = of('motprov').some(m => {
      const g = linkTarget(m.fm.gäller);
      if (g) return g === h.path.replace(/\.md$/, '') || g === basename(h.path);
      const fm = linkTarget(m.fm.fråga), fh = linkTarget(h.fm.fråga);
      return Boolean(fm) && fm === fh;
    });
    if (!harMotprov && ålder > 14 && (h.fm.status || 'oprövad') === 'oprövad') {
      out.push(finding('påminnelse', 'Oprövad hypotes',
        `Hypotesen "${basename(h.path)}" har inget motprov efter ${ålder} dagar.`, h.path));
    }
  }

  // Människor: AI kan inte ersätta verklig mänsklig mångfald.
  const möten = of('forskningsmöte').map(noteDate).filter(Boolean).sort();
  const senasteMöte = möten[möten.length - 1];
  if (active.length > 0 && (!senasteMöte || daysBetween(senasteMöte, date) > 30)) {
    out.push(finding('varning', 'Ingen extern återkoppling',
      senasteMöte
        ? `Senaste forskningsmötet var för ${daysBetween(senasteMöte, date)} dagar sedan.`
        : 'Inget forskningsmöte dokumenterat än.'));
  }

  // Nätverk: nya kontakter tillför fler perspektiv än samma personer.
  const möten180 = of('forskningsmöte').filter(m => noteDate(m) && daysBetween(noteDate(m), date) <= 180);
  if (möten180.length >= 3 && !möten180.some(m => m.fm.ny_kontakt === 'ja')) {
    out.push(finding('påminnelse', 'Inga nya kontakter',
      `${möten180.length} forskningsmöten senaste halvåret, inget med en ny kontakt.`));
  }

  // Möten: uppföljningar som inte gjorts, samma person, saknade kompetenser.
  for (const m of möten180) {
    const öppna = (section(m.body, 'Uppföljning').match(/^- \[ \]\s*\S/gm) || []).length;
    if (öppna > 0 && daysBetween(noteDate(m), date) > 14) {
      out.push(finding('påminnelse', 'Uppföljning efter möte',
        `"${basename(m.path)}" har ${öppna} uppföljning(ar) som inte är gjorda.`, m.path));
    }
  }
  const personer = new Set(möten180.map(m => String(m.fm.deltagare || '').trim().toLowerCase()).filter(Boolean));
  if (möten180.length >= 3 && personer.size === 1) {
    out.push(finding('påminnelse', 'Samma person',
      `${möten180.length} forskningsmöten senaste halvåret, alla med samma person.`));
  }
  if (active.length > 0 && möten180.length >= 2) {
    const kompetenser = new Set(möten180.map(m => m.fm.kompetens));
    const saknas = ['ämne', 'metod', 'annat fält'].filter(k => !kompetenser.has(k));
    if (saknas.length) {
      out.push(finding('påminnelse', 'Saknad kompetens',
        `Inga forskningsmöten senaste halvåret med kompetens: ${saknas.join(', ')}.`));
    }
  }

  // Arbete: aktiva frågor men inget loggat arbete på 14 dagar.
  if (active.length > 0) {
    const arbete = notes.filter(n => ['forskarpass', 'experiment', 'övning', 'motprov', 'hypotes'].includes(n.fm.typ))
      .map(noteDate).filter(Boolean);
    for (const logg of of('fokuslogg')) {
      for (const m of String(logg.body || '').matchAll(/^- (\d{4}-\d{2}-\d{2}) /gm)) arbete.push(m[1]);
    }
    const senast = arbete.sort().pop();
    if (!senast || daysBetween(senast, date) > 14) {
      out.push(finding('varning', 'Inget arbete loggat',
        senast ? `Senaste forskarpass, fokuspass eller experiment var för ${daysBetween(senast, date)} dagar sedan.` : 'Inga forskarpass, fokuspass eller experiment loggade än.'));
    }
  }

  // Lekfullhet: inga nya idéer eller perspektiv på 60 dagar.
  if (active.length > 0) {
    const nytt = notes.filter(n => ['idé', 'perspektivkarta'].includes(n.fm.typ) && noteDate(n) && daysBetween(noteDate(n), date) <= 60);
    const äldsta = active.map(noteDate).filter(Boolean).sort()[0];
    if (!nytt.length && äldsta && daysBetween(äldsta, date) > 60) {
      out.push(finding('påminnelse', 'Inga nya idéer',
        'Ingen ny idé eller perspektivkarta på 60 dagar. Parkera idéer när de dyker upp.'));
    }
  }

  // Att inte förstå: forskarpass där avsnittet om det man inte förstår är tomt.
  const pass30 = of('forskarpass').filter(n => noteDate(n) && daysBetween(noteDate(n), date) <= 30);
  if (pass30.length >= 3 && !pass30.some(n => section(n.body, 'Det jag inte förstår'))) {
    out.push(finding('påminnelse', 'Inget oklart',
      `${pass30.length} forskarpass senaste månaden, inget med något under "Det jag inte förstår".`));
  }

  // Kompetens: skattningar utan arbetsprov, och ingen övning för den svagaste förmågan.
  const sistaGranskning = of('förmågegranskning').sort((a, b) => noteDate(a).localeCompare(noteDate(b))).pop();
  if (sistaGranskning) {
    const utanBelägg = CAPABILITIES.filter(([k, namn]) => Number(sistaGranskning.fm[k]) >= 1 &&
      !/\[\[[^\]]+\]\]/.test((section(sistaGranskning.body, namn).match(/Arbetsprov:.*$/m) || [''])[0]));
    if (utanBelägg.length) {
      out.push(finding('påminnelse', 'Skattning utan belägg',
        `${utanBelägg.length} förmågor i senaste granskningen saknar länk till ett arbetsprov.`, sistaGranskning.path));
    }
    const skattade = CAPABILITIES.filter(([k]) => Number(sistaGranskning.fm[k]) >= 1);
    if (skattade.length) {
      const [svagast, svagastNamn] = skattade.reduce((a, b) => Number(sistaGranskning.fm[b[0]]) < Number(sistaGranskning.fm[a[0]]) ? b : a);
      const övad = of('övning').some(ö => ö.fm.förmåga === svagast && noteDate(ö) && daysBetween(noteDate(ö), date) <= 30);
      if (!övad) {
        out.push(finding('påminnelse', 'Svagaste förmågan',
          `Lägst skattad: ${svagastNamn}. Ingen övning för den senaste 30 dagarna.`));
      }
    }
  }

  // Tillit: öppna felrättningar.
  for (const k of of('felrättning').filter(k => (k.fm.status || 'öppen') === 'öppen')) {
    const ålder = daysBetween(noteDate(k) || date, date);
    if (ålder > 14) {
      out.push(finding('påminnelse', 'Öppen felrättning',
        `Felrättningen "${basename(k.path)}" har varit öppen i ${ålder} dagar.`, k.path));
    }
  }

  // AI-konsultationer utan egen sammanfattning efteråt.
  for (const a of of('ai-konsultation')) {
    const ålder = daysBetween(noteDate(a) || date, date);
    if (ålder >= 2 && !section(a.body, 'Vad tar jag med mig')) {
      out.push(finding('påminnelse', 'AI-användning',
        `AI-konsultationen "${basename(a.path)}" saknar din egen sammanfattning.`, a.path));
    }
  }

  const ai30 = of('ai-konsultation').filter(a => daysBetween(noteDate(a) || date, date) <= 30);
  const utanTanke = ai30.filter(a => a.fm.egen_tanke_först !== 'ja').length;
  if (ai30.length >= 3 && utanTanke / ai30.length > 0.5) {
    out.push(finding('varning', 'AI-användning',
      `${utanTanke} av ${ai30.length} AI-konsultationer senaste månaden gjordes innan du skrivit något eget.`));
  }

  // Beroende över tid: andelen konsultationer med eget utkast ska inte sjunka.
  const förra30 = of('ai-konsultation').filter(a => { const d = daysBetween(noteDate(a) || date, date); return d > 30 && d <= 60; });
  if (ai30.length >= 3 && förra30.length >= 3) {
    const nu = ai30.filter(a => a.fm.egen_tanke_först === 'ja').length / ai30.length;
    const då = förra30.filter(a => a.fm.egen_tanke_först === 'ja').length / förra30.length;
    if (då - nu >= 0.25) {
      out.push(finding('varning', 'Ökande AI-beroende',
        `Andelen AI-konsultationer med eget utkast har sjunkit från ${Math.round(då * 100)} % till ${Math.round(nu * 100)} %.`));
    }
  }

  // Återkoppling: månatlig förmågegranskning.
  const granskningar = of('förmågegranskning').map(noteDate).filter(Boolean).sort();
  const senaste = granskningar[granskningar.length - 1];
  if (!senaste || daysBetween(senaste, date) > 35) {
    out.push(finding('påminnelse', 'Förmågegranskning',
      senaste ? 'Över en månad sedan senaste förmågegranskningen.' : 'Ingen förmågegranskning gjord än.'));
  }

  // Förslag: första uppdraget.
  if (active.length === 0 && questions.some(q => q.fm.status === 'förslag')) {
    out.push(finding('påminnelse', 'Ingen aktiv fråga',
      'Det finns ett frågeförslag i 01 RIKTNING.'));
  }

  return out.sort((a, b) => (a.nivå === b.nivå ? 0 : a.nivå === 'varning' ? -1 : 1));
}

/* ---------- Mått ---------- */

/** Mått på AI-användning, övning och förmåga. */
function metrics(notes, date) {
  const of = typ => notes.filter(n => n.fm.typ === typ);
  const inom = (n, d) => daysBetween(noteDate(n) || date, date) <= d;
  const ai = of('ai-konsultation').filter(n => inom(n, 30));
  const förraAI = of('ai-konsultation').filter(n => { const d = daysBetween(noteDate(n) || date, date); return d > 30 && d <= 60; });
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
  const möten90 = of('forskningsmöte').filter(n => inom(n, 90));
  // Fokuspass loggas av forskaros-fokus: "- 2026-11-10 09:00–09:50 (50 av 50 min): …"
  let fokuspass = 0, fokusminuter = 0;
  for (const logg of of('fokuslogg')) {
    for (const m of String(logg.body || '').matchAll(/^- (\d{4}-\d{2}-\d{2}) [^(]*\((\d+) av \d+ min\)/gm)) {
      if (daysBetween(m[1], date) <= 30) { fokuspass++; fokusminuter += Number(m[2]); }
    }
  }
  const avslutade = of('forskningsfråga').filter(q => q.fm.status === 'avslutad');
  const utfall = Object.fromEntries(Object.keys(UTFALL).map(k => [k, avslutade.filter(q => q.fm.utfall === k).length]));
  return {
    aiKonsultationer: ai.length,
    tänktFörst: ai.filter(a => a.fm.egen_tanke_först === 'ja').length,
    aiFörra: förraAI.length,
    tänktFörstFörra: förraAI.filter(a => a.fm.egen_tanke_först === 'ja').length,
    idéer: of('idé').filter(n => inom(n, 60)).length,
    övningarUtanAI: övningar.length,
    motprov: of('motprov').length,
    omprövningar: of('omprövning').length,
    felrättningar: of('felrättning').length,
    möten: möten90.length,
    nyaKontakter: möten90.filter(n => n.fm.ny_kontakt === 'ja').length,
    fokuspass,
    fokusminuter,
    utfall,
    förmåga: sista ? score(sista) : null,
    förmågaFörra: förra ? score(förra) : null,
    epistemik: { belagt, tolkning, spekulation }
  };
}

/* ---------- AI-konsultation ---------- */

/** Bygger den text som forskaren själv väljer att skicka till en AI. */
function buildPrompt({ roll, läge, titel, text }) {
  const r = ROLES[roll] || ROLES.kritik;
  const m = MODES[läge] || MODES.utveckling;
  return [
    `Uppgift (${r.namn}): ${r.uppdrag}`,
    '',
    `Läge: ${m.namn}. ${m.instruktion}`,
    '',
    'Regler:',
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

## 6. Det jag inte förstår


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


## Den ovanliga kombinationen
> Vilka fält, idéer eller metoder kombineras som sällan möts?


## Vilket etablerat antagande utmanar hypotesen?


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


## Vad skulle resultatet betyda?


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


## Analysmiljö
> Kör \`forskaros-labb version\` och klistra in raden här. Då kan du och andra
> köra om analysen i exakt samma miljö, år senare.


## Ny metod eller nytt verktyg?


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
    render: ({ date, fråga }) => fm({ typ: 'forskningsmöte', datum: date, deltagare: '', kompetens: 'ämne', krets: 'nätverk', ny_kontakt: 'ja', fråga }) + `# Forskningsmöte

> deltagare: namn. kompetens: ämne, metod eller annat fält.
> krets: kärna (handledare, nära forskningspartner) eller nätverk.

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

> Lös uppgiften utan hjälp. Sätt utan_ai till "nej" om du tog hjälp.

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

> Skatta varje förmåga 1–5 i egenskaperna ovan och länka till arbetsprovet
> skattningen bygger på. Det är en självskattning.

${CAPABILITIES.map(([, namn, fråga]) => `## ${namn}\n> ${fråga}\n- Arbetsprov:\n- Motivering:\n`).join('\n')}
## Vad ska jag träna nästa månad?
`
  }
};

function questionNote({ date, titel, varför, status = 'aktiv' }) {
  return fm({ typ: 'forskningsfråga', datum: date, status, fas: 'utforska', fas_ändrad: date, cykel: 1 }) + `# ${titel}

## Varför är frågan viktig?
${varför || ''}

## Avgränsning


## Om frågan besvaras
> Vad vet vi då som vi inte vet i dag, och vem har nytta av det?


## Det jag väljer bort


## Lärdomar


## Sammanfattning för någon utanför fältet
> 50–200 ord, utan facktermer.


## Delat med


## Fasbeslut
- ${date}: Frågan formulerades. Fas: Utforska.
`;
}

function ideaNote({ date, idé }) {
  return fm({ typ: 'idé', datum: date, status: 'parkerad' }) + `# Idé

${idé || ''}

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
  PHASES, PHASE_TOOLS, ROLES, MODES, CAPABILITIES, EPISTEMIC_CONTRACT, UTFALL, MAX_ÖPPNA_FRÅGOR, MAX_AKTIVA_FRÅGOR, MIN_EGNA_ORD,
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
/** Avsluta en forskningsfråga med ett utfall och en motivering. */
class CloseModal extends Modal {
  constructor(app, plugin, question) {
    super(app);
    Object.assign(this, { plugin, question });
  }
  onOpen() {
    const el = this.contentEl;
    el.empty();
    el.addClass('forskaros-modal');
    el.createEl('h3', { text: `Avsluta: ${basename(this.question.path)}` });
    el.createEl('p', { text: 'En förkastad hypotes är också ett resultat. Övergiven betyder att frågan läggs ner utan svar.' });
    el.createEl('label', { text: 'Utfall', cls: 'forskaros-label' });
    const utfall = el.createEl('select', { cls: 'forskaros-input' });
    for (const [id, namn] of Object.entries(UTFALL)) utfall.createEl('option', { text: namn, value: id });
    el.createEl('label', { text: 'Vad blev resultatet, eller varför läggs frågan ner?', cls: 'forskaros-label' });
    const why = el.createEl('textarea', { cls: 'forskaros-input' });
    const row = el.createDiv({ cls: 'forskaros-row' });
    row.createEl('button', { text: 'Avsluta frågan', cls: 'mod-cta' }).addEventListener('click', async () => {
      if (!why.value.trim()) { new Notice('Skriv en motivering.'); return; }
      this.close();
      await this.plugin.closeQuestion(this.question, utfall.value, why.value.trim());
    });
    row.createEl('button', { text: 'Avbryt' }).addEventListener('click', () => this.close());
  }
  onClose() { this.contentEl.empty(); }
}

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
      el.createEl('p', { text: 'Alla krav är inte uppfyllda. Motiveringen sparas i frågan.' });
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
        ? `${this.words} egna ord i anteckningen.`
        : `${this.words} egna ord i anteckningen. Utvecklings- och prövningsläget kräver minst ${MIN_EGNA_ORD}.`
    });

    el.createEl('label', { text: 'Roll', cls: 'forskaros-label' });
    const roll = el.createEl('select', { cls: 'forskaros-input' });
    for (const [id, r] of Object.entries(ROLES)) roll.createEl('option', { text: r.namn, value: id });
    roll.value = 'kritik';

    el.createEl('label', { text: 'Läge', cls: 'forskaros-label' });
    const läge = el.createEl('select', { cls: 'forskaros-input' });
    if (!tänktFörst) läge.createEl('option', { text: 'Välj läge', value: '' });
    for (const [id, m] of Object.entries(MODES)) {
      const o = läge.createEl('option', { text: `${m.namn} – ${m.beskrivning}`, value: id });
      if (!tänktFörst && id !== 'prestation') o.disabled = true;
    }
    läge.value = tänktFörst ? 'utveckling' : '';
    if (!tänktFörst) el.createEl('p', { text: 'Skriv ett eget utkast för att få frågor och motargument. Välj prestationsläge om du vill ha hjälp att producera text eller kod redan nu.' });

    el.createEl('label', { text: 'Text att kopiera (skickas inte automatiskt)', cls: 'forskaros-label' });
    const preview = el.createEl('textarea', { cls: 'forskaros-input forskaros-preview' });
    preview.readOnly = true;
    const row = el.createDiv({ cls: 'forskaros-row' });
    const copy = row.createEl('button', { text: 'Kopiera och logga', cls: 'mod-cta' });
    const update = () => {
      copy.disabled = !läge.value;
      preview.value = !läge.value ? '' : buildPrompt({ roll: roll.value, läge: läge.value, titel: this.file.basename, text: this.text });
    };
    roll.addEventListener('change', update);
    läge.addEventListener('change', update);
    update();

    copy.addEventListener('click', async () => {
      if (!läge.value) return;
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

    // Forskningsfrågor och deras fas i cykeln.
    const questions = notes.filter(n => n.fm.typ === 'forskningsfråga');
    const active = questions.filter(q => (q.fm.status || 'aktiv') === 'aktiv');
    root.createEl('h4', { text: 'Forskningsfrågor' });
    if (!active.length) {
      const förslag = questions.find(q => q.fm.status === 'förslag');
      root.createEl('p', { cls: 'forskaros-muted', text: 'Ingen aktiv forskningsfråga.' });
      const row = root.createDiv({ cls: 'forskaros-row' });
      row.createEl('button', { text: 'Ny forskningsfråga', cls: 'mod-cta' })
        .addEventListener('click', () => this.plugin.newQuestion());
      if (förslag) {
        row.createEl('button', { text: `Använd förslaget: ${basename(förslag.path)}` })
          .addEventListener('click', () => this.plugin.adoptQuestion(förslag));
      }
    }
    for (const q of active) this.renderQuestion(root, q, notes);
    const vilande = questions.filter(q => q.fm.status === 'vilar');
    for (const q of vilande) {
      const rad = root.createDiv({ cls: 'forskaros-resting' });
      rad.createEl('span', { cls: 'forskaros-muted', text: `Vilar: ${basename(q.path)} (till ${q.fm.vila_till || '?'})` });
      rad.createEl('button', { text: 'Återuppta' }).addEventListener('click', () => new FormModal(this.app, {
        title: `Återuppta: ${basename(q.path)}`,
        fields: [{ key: 'varför', label: 'Varför är frågan fortfarande viktig?', multiline: true, required: true }],
        submit: [{ text: 'Återuppta', cta: true }],
        onSubmit: (_, v) => void this.plugin.resumeQuestion(q, v.varför)
      }).open());
    }

    // Granskning.
    const findings = audit(notes, date);
    root.createEl('h4', { text: 'Att åtgärda' });
    if (!findings.length) root.createEl('p', { cls: 'forskaros-muted', text: 'Inget just nu.' });
    for (const f of findings.slice(0, 8)) {
      const item = root.createDiv({ cls: `forskaros-finding is-${f.nivå}` });
      item.createEl('b', { text: f.princip });
      item.createEl('span', { text: f.text });
      if (f.path) item.addEventListener('click', () => void this.plugin.openPath(f.path));
    }

    // Självständighet.
    const m = metrics(notes, date);
    root.createEl('h4', { text: 'Senaste 30 dagarna' });
    const grid = root.createDiv({ cls: 'forskaros-metrics' });
    const card = (value, label) => {
      const c = grid.createDiv({ cls: 'forskaros-metric' });
      c.createEl('strong', { text: value });
      c.createEl('span', { text: label });
    };
    card(m.aiKonsultationer ? `${m.tänktFörst}/${m.aiKonsultationer}` : '–',
      m.aiFörra ? `AI-frågor efter eget utkast (förra 30 d: ${m.tänktFörstFörra}/${m.aiFörra})` : 'AI-frågor efter eget utkast');
    card(String(m.övningarUtanAI), 'Övningar utan AI');
    card(m.förmåga ? m.förmåga.toFixed(1) : '–', m.förmågaFörra ? `Förmåga (förra: ${m.förmågaFörra.toFixed(1)})` : 'Förmåga (1–5)');
    card(String(m.motprov), 'Motprov');
    card(String(m.omprövningar), 'Omprövningar');
    card(String(m.felrättningar), 'Felrättningar');
    card(String(m.möten), `Forskningsmöten 90 d (${m.nyaKontakter} nya kontakter)`);
    card(String(m.fokuspass), `Fokuspass (${Math.round(m.fokusminuter / 60 * 10) / 10} h)`);
    const u = m.utfall;
    card(String(u.besvarad + u.förkastad), `Avslutade frågor (${u.övergiven} övergivna)`);
    const e = m.epistemik;
    root.createEl('p', { cls: 'forskaros-muted', text: `Märkta påståenden: ${e.belagt} belagt, ${e.tolkning} tolkning, ${e.spekulation} spekulation` });

    // Skapa.
    root.createEl('h4', { text: 'Ny anteckning' });
    const actions = root.createDiv({ cls: 'forskaros-actions' });
    const btn = (text, fn) => actions.createEl('button', { text }).addEventListener('click', fn);
    btn('Parkera en idé', () => this.plugin.parkIdea());
    btn('Be AI om hjälp', () => void this.plugin.consultAI());
    for (const [type, spec] of Object.entries(TYPES)) btn(spec.label, () => void this.plugin.createNote(type));
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
    box.createEl('div', { cls: 'forskaros-muted', text: `Cykel ${q.fm.cykel || 1}` });
    box.createEl('div', { cls: 'forskaros-phase-question', text: p.fråga });
    const tools = box.createEl('div', { cls: 'forskaros-muted forskaros-tools', text: `Verktyg: ${PHASE_TOOLS[fas] || ''}` });
    tools.addEventListener('click', () => void this.plugin.openPath('00 START/Verktygslåda.md'));
    const reqs = phaseRequirements(q, notes);
    const list = box.createEl('ul', { cls: 'forskaros-checklist' });
    for (const r of reqs) list.createEl('li', { text: `${r.ok ? '✓' : '○'} ${r.text}`, cls: r.ok ? 'is-ok' : 'is-missing' });
    const row = box.createDiv({ cls: 'forskaros-row' });
    row.createEl('button', { text: `Gå vidare till ${nextPhase(fas).namn}` })
      .addEventListener('click', () => new PhaseModal(this.app, this.plugin, q, reqs).open());
    row.createEl('button', { text: 'Lägg att vila' })
      .addEventListener('click', () => void this.plugin.restQuestion(q));
    row.createEl('button', { text: 'Avsluta' })
      .addEventListener('click', () => new CloseModal(this.app, this.plugin, q).open());
  }
}

module.exports = class ForskarOSPlugin extends Plugin {
  async onload() {
    this.registerView(VIEW_TYPE, leaf => new ForskarOSView(leaf, this));
    this.addRibbonIcon('brain', 'Öppna ForskarOS', () => void this.activateDashboard());
    this.addCommand({ id: 'open-dashboard', name: 'Öppna ForskarOS-panelen', callback: () => void this.activateDashboard() });
    this.addCommand({ id: 'new-question', name: 'Ny forskningsfråga', callback: () => this.newQuestion() });
    this.addCommand({ id: 'park-idea', name: 'Parkera en idé', callback: () => this.parkIdea() });
    this.addCommand({ id: 'consult-ai', name: 'Be AI om hjälp', callback: () => void this.consultAI() });
    this.addCommand({ id: 'close-question', name: 'Avsluta forskningsfrågan', callback: () => void (async () => {
      const q = await this.focusQuestion();
      if (!q) { new Notice('Öppna den forskningsfråga du vill avsluta.'); return; }
      new CloseModal(this.app, this, q).open();
    })() });
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
    // Panelen öppnas när vaulten öppnas.
    if (this.app.workspace.onLayoutReady) {
      this.app.workspace.onLayoutReady(() => {
        if (!this.app.workspace.getLeavesOfType(VIEW_TYPE).length) void this.activateDashboard();
      });
    }
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
          ? [`Du har redan ${aktiva.length} aktiva frågor: ${aktiva.map(q => basename(q.path)).join(', ')}. Parkera den nya som idé i stället?`]
          : null,
        fields: [
          { key: 'titel', label: 'Frågan, i en mening', required: true },
          { key: 'varför', label: 'Varför är frågan viktig?', multiline: true, required: !full }
        ],
        submit: full
          ? [{ id: 'park', text: 'Parkera som idé', cta: true, skipRequired: false },
            { id: 'create', text: 'Skapa ändå' }]
          : [{ id: 'create', text: 'Skapa frågan', cta: true }],
        onSubmit: async (id, v) => {
          if (id === 'park') return this.saveIdea(`${v.titel}\n\n${v.varför || ''}`.trim());
          if (!v.varför) { new Notice('Skriv varför frågan är viktig.'); return; }
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
    new Notice('Frågan är aktiv.');
    this.refreshDashboard();
  }

  parkIdea() {
    new FormModal(this.app, {
      title: 'Parkera en idé',
      intro: ['Sparas i 01 RIKTNING/Idébank.'],
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
    new Notice(`Fas: ${nxt.namn}`);
    this.refreshDashboard();
  }

  async restQuestion(q) {
    const file = this.app.vault.getAbstractFileByPath(q.path);
    if (!file) return;
    const till = addDays(today(), 14);
    await this.app.fileManager.processFrontMatter(file, f => { f.status = 'vilar'; f.vila_till = till; f.vilat = Number(f.vilat || 0) + 1; });
    const body = await this.app.vault.read(file);
    await this.app.vault.modify(file, appendPhaseLog(body, `${today()}: Lagd att vila till ${till} (inkubation).`));
    new Notice(`"${basename(q.path)}" vilar till ${till}.`);
    this.refreshDashboard();
  }

  async resumeQuestion(q, varför = '') {
    const file = this.app.vault.getAbstractFileByPath(q.path);
    if (!file) return;
    await this.app.fileManager.processFrontMatter(file, f => { f.status = 'aktiv'; f.fas_ändrad = today(); delete f.vila_till; });
    const body = await this.app.vault.read(file);
    await this.app.vault.modify(file, appendPhaseLog(body, `${today()}: Återupptagen.${varför ? ` ${varför}` : ''}`));
    const notes = await this.collectNotes();
    const aktiva = notes.filter(n => n.fm.typ === 'forskningsfråga' && (n.fm.status || 'aktiv') === 'aktiv').length;
    new Notice(aktiva > MAX_AKTIVA_FRÅGOR ? `${aktiva} aktiva frågor nu.` : `"${basename(q.path)}" är aktiv igen.`);
    this.refreshDashboard();
  }

  async closeQuestion(q, utfall, motivering) {
    const file = this.app.vault.getAbstractFileByPath(q.path);
    if (!file || !UTFALL[utfall]) return;
    await this.app.fileManager.processFrontMatter(file, f => {
      f.status = 'avslutad'; f.utfall = utfall; f.avslutad = today(); delete f.vila_till;
    });
    const body = await this.app.vault.read(file);
    await this.app.vault.modify(file, appendPhaseLog(body, `${today()}: Avslutad i fasen ${phaseOf(q.fm.fas).namn}. Utfall: ${UTFALL[utfall]}. ${motivering}`));
    new Notice(`"${basename(q.path)}" avslutad: ${UTFALL[utfall]}.`);
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

> Texten under "Det som skickades" ligger i urklippet.

## Svaret (klistra in)


## Vad är belagt, tolkning respektive spekulation?


## Vad håller jag inte med om?


## Vad tar jag med mig?


## Det som skickades
\`\`\`\`text
${prompt}
\`\`\`\`
`;
    const created = await this.app.vault.create(path, content);
    await this.app.workspace.getLeaf(true).openFile(created);
    new Notice('Texten är kopierad. Klistra in svaret i loggen.');
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
