'use strict';
// Testar tillägget mot ett simulerat Obsidian-API.
const assert = require('node:assert/strict');
const Module = require('node:module');
const path = require('node:path');
const fs = require('node:fs');

/* ---------- Simulerad vault ---------- */
const files = new Map();
const folders = new Set();
const commands = [];
let activeFile = null;

function parseFrontmatter(content) {
  const m = /^---\n([\s\S]*?)\n---/.exec(content);
  if (!m) return undefined;
  const out = {};
  for (const line of m[1].split('\n')) {
    const i = line.indexOf(':');
    if (i < 0) continue;
    let v = line.slice(i + 1).trim();
    if (v.startsWith('"')) v = JSON.parse(v);
    out[line.slice(0, i).trim()] = v === '' ? null : v;
  }
  return out;
}
function writeFrontmatter(content, front) {
  const yaml = Object.entries(front).map(([k, v]) => `${k}: ${v === null ? '' : typeof v === 'string' && /[:#[\]]/.test(v) ? JSON.stringify(v) : v}`).join('\n');
  return content.replace(/^---\n[\s\S]*?\n---/, `---\n${yaml}\n---`);
}
const mkfile = (p, content) => ({ path: p, basename: path.basename(p, '.md'), content, stat: { ctime: Date.now() } });

const app = {
  vault: {
    adapter: { exists: async p => folders.has(p) || files.has(p) },
    createFolder: async p => { folders.add(p); },
    create: async (p, content) => {
      assert(!files.has(p), 'En befintlig anteckning får aldrig skrivas över');
      const f = mkfile(p, content);
      files.set(p, f);
      return f;
    },
    read: async f => files.get(f.path).content,
    cachedRead: async f => files.get(f.path).content,
    modify: async (f, content) => { files.get(f.path).content = content; },
    getMarkdownFiles: () => [...files.values()],
    getAbstractFileByPath: p => files.get(p) || null
  },
  metadataCache: {
    getFileCache: f => ({ frontmatter: parseFrontmatter(files.get(f.path).content) }),
    on: () => ({})
  },
  fileManager: {
    processFrontMatter: async (f, fn) => {
      const front = parseFrontmatter(f.content) || {};
      fn(front);
      f.content = writeFrontmatter(f.content, front);
    }
  },
  workspace: {
    getActiveFile: () => activeFile,
    getLeaf: () => ({ openFile: async file => { activeFile = file; } }),
    getLeavesOfType: () => [],
    getRightLeaf: () => null,
    revealLeaf: async () => {}
  }
};

class Plugin {
  constructor() { this.app = app; }
  registerView(type, creator) { this.registeredView = { type, creator }; }
  registerEvent() {}
  addRibbonIcon() {}
  addCommand(command) { commands.push(command); }
}
class ItemView {}
class Modal { constructor(a) { this.app = a; } open() { Modal.opened.push(this); } close() {} }
Modal.opened = [];
class Notice { constructor() {} }

const origLoad = Module._load;
Module._load = function (request, ...rest) {
  if (request === 'obsidian') return { Plugin, ItemView, Notice, Modal };
  return origLoad.call(this, request, ...rest);
};
const ForskarOSPlugin = require('../vault/.obsidian/plugins/forskaros-core/main.js');
Module._load = origLoad;
const { engine } = ForskarOSPlugin;

(async () => {
  const p = new ForskarOSPlugin();
  await p.onload();
  const ids = commands.map(c => c.id);
  for (const id of ['open-dashboard', 'close-question', 'new-question', 'park-idea', 'consult-ai', 'advance-phase', 'mark-belagt', 'mark-tolkning', 'mark-spekulation']) {
    assert(ids.includes(id), `kommandot ${id} saknas`);
  }
  assert.equal(new Set(ids).size, ids.length, 'kommando-id ska vara unika');
  assert.equal(p.registeredView.type, 'forskaros-dashboard');

  // En forskningsfråga skapas, nya anteckningar kopplas till den.
  const qFile = await app.vault.create('01 RIKTNING/När stärker AI tänkandet.md',
    engine.questionNote({ date: engine.today(), titel: 'När stärker AI tänkandet?', varför: 'Frågan avgör om skolor ska använda AI som stöd för skrivande eller inte, och hur. Det berör hundratusentals elever och lärare varje år, och dagens beslut fattas nästan helt utan forskning om långsiktiga effekter.' }));
  activeFile = qFile;
  for (const type of Object.keys(engine.TYPES)) {
    activeFile = qFile;
    const f = await p.createNote(type);
    assert(f, `${type} skapades inte`);
  }
  const typed = [...files.values()].filter(f => f !== qFile);
  assert.equal(typed.length, Object.keys(engine.TYPES).length);
  const linked = typed.filter(f => /fråga: "\[\[01 RIKTNING\/När stärker AI tänkandet\]\]"/.test(f.content));
  assert(linked.length >= 7, `anteckningar ska kopplas till frågan (${linked.length})`);
  assert(typed.every(f => !f.path.includes('undefined')));

  // Samma kommando två gånger skapar två dokument, skriver aldrig över.
  activeFile = qFile;
  await p.createNote('pass');
  await p.createNote('pass');
  assert.equal(files.size, typed.length + 3);

  // Forskaren fyller i perspektivkartan.
  const karta = [...files.values()].find(f => f.path.startsWith('03 EVIDENS/'));
  karta.content = karta.content
    .replace('| Kognitionsvetenskap | | | |', '| Kognitionsvetenskap | Avlastning | Motivation | Risko |')
    .replace('| Teknik / datavetenskap | | | |', '| Teknik / datavetenskap | Verktyg | Lärande | ACM |')
    .replace('| Oväntat fält | | | |', '| Oväntat fält | Träningslära | Kontext | Ericsson |')
    .replace('## Där perspektiven motsäger varandra\n', '## Där perspektiven motsäger varandra\nKort- mot långsiktigt.\n');

  qFile.content = qFile.content
    .replace('## Det jag undrar\n> Minst tre saker du inte vet än och vill veta.\n-\n-\n-\n',
      '## Det jag undrar\n> Minst tre saker du inte vet än och vill veta.\n- Vad händer när stödet tas bort?\n- Gäller det vuxna?\n- Spelar uppgiften roll?\n')
    .replace('## Vem bryr sig om svaret?\n> Vilka människor eller verksamheter har nytta av svaret, utanför ditt eget fält?\n',
      '## Vem bryr sig om svaret?\n> Vilka människor eller verksamheter har nytta av svaret, utanför ditt eget fält?\nLärare, elever och skolhuvudmän.\n');

  // Fasbyte: frontmatter uppdateras och beslutet loggas öppet, med motivering.
  const notes = await p.collectNotes();
  const q = notes.find(n => n.fm.typ === 'forskningsfråga');
  const reqs = engine.phaseRequirements(q, notes);
  assert(reqs.every(r => r.ok), 'Utforska-kraven ska vara uppfyllda: ' + JSON.stringify(reqs));
  await p.advancePhase(q, '', []);
  assert.match(qFile.content, /fas: kombinera/);
  assert.match(qFile.content, /Utforska → Kombinera/);
  const q2 = (await p.collectNotes()).find(n => n.fm.typ === 'forskningsfråga');
  await p.advancePhase(q2, 'Handledaren vill se en skiss först.', ['Hypotesen redovisar den etablerade kunskap den vilar på']);
  assert.match(qFile.content, /fas: välj/);
  assert.match(qFile.content, /Motivering: Handledaren vill se en skiss först\./);

  // Vila (inkubation).
  const q3 = (await p.collectNotes()).find(n => n.fm.typ === 'forskningsfråga');
  await p.restQuestion(q3);
  assert.match(qFile.content, /status: vilar/);
  assert.match(qFile.content, /vila_till: \d{4}-\d{2}-\d{2}/);

  // Vila räknas, återupptagning och avslut med utfall loggas.
  assert.match(qFile.content, /vilat: 1/);
  const q4 = (await p.collectNotes()).find(n => n.fm.typ === 'forskningsfråga');
  await p.resumeQuestion(q4, 'Ny data från SCB gör frågan aktuell igen.');
  assert.match(qFile.content, /status: aktiv/);
  assert.doesNotMatch(qFile.content, /vila_till/);
  assert.match(qFile.content, /Återupptagen\. Ny data från SCB gör frågan aktuell igen\./);
  qFile.content = qFile.content.replace('## Vilken fråga öppnar svaret?\n> Det viktigaste med ett svar är nästa fråga. Den hamnar i idébanken när frågan avslutas.\n',
    '## Vilken fråga öppnar svaret?\n> Det viktigaste med ett svar är nästa fråga. Den hamnar i idébanken när frågan avslutas.\nGäller det också vuxna som lär sig ett yrke?\n');
  const q5 = (await p.collectNotes()).find(n => n.fm.typ === 'forskningsfråga');
  await p.closeQuestion(q5, 'förkastad', 'Ingen skillnad mellan grupperna.');
  const nästa = files.get('01 RIKTNING/Idébank/Gäller det också vuxna som lär sig ett yrke.md');
  assert(nästa && /typ: idé/.test(nästa.content) && /Från \[\[01 RIKTNING\/När stärker AI tänkandet\]\]/.test(nästa.content), 'nästa fråga hamnar i idébanken');
  assert.match(qFile.content, /status: avslutad/);
  assert.match(qFile.content, /utfall: förkastad/);
  assert.match(qFile.content, /Utfall: Hypotesen förkastad\. Ingen skillnad mellan grupperna\./);
  assert.equal(engine.metrics(await p.collectNotes(), engine.today()).utfall.förkastad, 1);

  // Idéparkering.
  await p.saveIdea('AI som handledare i språkundervisning\nKanske en senare fråga.');
  assert(files.has('01 RIKTNING/Idébank/AI som handledare i språkundervisning.md'));

  // AI-konsultationen loggas med uppgift, läge och den skickade texten.
  const hyp = [...files.values()].find(f => f.path.startsWith('02 HYPOTESER/'));
  // Från hypotesen till ett nytt projekt i appen.
  activeFile = hyp;
  const url = await p.projectFromActive();
  assert(url.startsWith('forskaros://nytt-projekt?') && url.includes('hypotes=02+HYPOTESER'), url);
  assert(url.includes(encodeURIComponent('01 RIKTNING/När stärker AI tänkandet').replace(/%20/g, '+')), url);
  // AI-stödet är avstängt tills forskaren väljer en nivå.
  assert.equal(p.settings.ai, 'av');
  activeFile = hyp;
  assert.equal(await p.consultAI(), null, 'ingen AI-dialog när stödet är avstängt');
  await p.setAI('handledning');
  assert.equal(p.settings.ai, 'handledning');
  await p.setAI('påhittad');
  assert.equal(p.settings.ai, 'handledning', 'okända nivåer ignoreras');
  await p.logConsultation(hyp, 'kritik', 'prövning', false, 'TEXT SOM SKICKADES');
  const log = [...files.values()].find(f => f.path.startsWith('08 REFLEKTION/AI/'));
  assert(log, 'AI-loggen skapades inte');
  assert.match(log.content, /egen_tanke_först: nej/);
  assert.match(log.content, /TEXT SOM SKICKADES/);
  assert.match(log.content, /Vad tar jag med mig/);

  // Granskningen av hela vaulten körs utan fel.
  const findings = engine.audit(await p.collectNotes(), engine.today());
  assert(Array.isArray(findings));

  // Tillägget ska vara fristående: inga nätverksanrop.
  const source = fs.readFileSync(require.resolve('../vault/.obsidian/plugins/forskaros-core/main.js'), 'utf8');
  assert(!/\bfetch\s*\(/.test(source));
  assert(!/XMLHttpRequest|requestUrl|https?:\/\//.test(source));
  process.stdout.write('OK: tillägget: kommandon, koppling till fråga, fasbyten, vila, idéer, AI-logg, inget nätverk\n');
})().catch(e => { console.error(e); process.exitCode = 1; });
