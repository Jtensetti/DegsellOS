#!/usr/bin/env node
/*
 * Skärmdumpar till README: renderar riktiga delar av ForskarOS.
 *
 *  - ForskarOS-panelen: tilläggets riktiga kod (main.js och styles.css) körs i
 *    en webbläsare mot ett exempelvalv, med Obsidians färgvariabler. Inte en
 *    skiss: det är samma renderDashboard() som körs i Obsidian.
 *  - Terminalen: riktig utdata från forskaros-princip och forskaros-setup.
 *  - Skrivbordsbakgrunden: den riktiga SVG-filen.
 *
 * Kräver Playwright:  node scripts/skarmdumpar.js
 */
'use strict';
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '..');
const OUT = path.join(ROOT, 'docs', 'bilder');
const PLUGIN = path.join(ROOT, 'vault/.obsidian/plugins/forskaros-core');
fs.mkdirSync(OUT, { recursive: true });

const OBSIDIAN_DARK = `
  :root { --background-primary:#1e1e1e; --background-secondary:#262626; --background-modifier-border:#363636;
    --text-normal:#dadada; --text-muted:#a3a3a3; --text-faint:#6f6f6f; --interactive-accent:#7f6df2;
    --text-on-accent:#ffffff; --text-success:#44cf6e; --text-warning:#e0ac00; --font-monospace:monospace; }
  body { margin:0; background:var(--background-primary); color:var(--text-normal);
    font:14px/1.5 Inter, "Segoe UI", Cantarell, sans-serif; }
  h2 { font-weight:700; } h4 { margin:1.2rem 0 0.4rem; font-size:0.95rem; }
  button { background:var(--background-secondary); color:var(--text-normal); border:1px solid var(--background-modifier-border);
    border-radius:6px; padding:0.35rem 0.7rem; font:inherit; font-size:0.82rem; }
  button.mod-cta { background:var(--interactive-accent); color:var(--text-on-accent); border:0; }
  .frame { width:420px; border-left:1px solid var(--background-modifier-border); }
`;

// Ett exempelvalv: en forskare mitt i fasen Pröva.
function exampleVault() {
  const q = '01 RIKTNING/När stärker AI människans förmåga att tänka';
  const link = `[[${q}]]`;
  const notes = [
    [`${q}.md`, { typ: 'forskningsfråga', status: 'aktiv', fas: 'pröva', fas_ändrad: '2026-11-08', cykel: 1, datum: '2026-10-02' },
      '## Varför är frågan värd tio år av mitt liv?\nFör att det avgör hur en generation lär sig tänka.\n## Det jag väljer bort\nYngre barn och programmering.\n'],
    ['03 EVIDENS/Perspektivkarta.md', { typ: 'perspektivkarta', fråga: link, datum: '2026-10-05' }, ''],
    ['02 HYPOTESER/Hypotes kognitiv avlastning.md', { typ: 'hypotes', fråga: link, status: 'oprövad', datum: '2026-10-20' },
      '## Hypotes (min formulering)\nAI-stöd före eget försök försvagar skrivförmågan.\n> [!belagt]\n> Studie om avlastning.\n> [!tolkning]\n> Gäller även skrivande.\n> [!spekulation]\n> Handledande AI vänder effekten.\n## Falsifiering\nIngen skillnad efter tre veckor.\n## Prediktioner\n1. Sämre resultat utan AI.\n'],
    ['05 FRIKTION/Motprov.md', { typ: 'motprov', fråga: link, datum: '2026-11-09' }, '## Mitt svar efter att ha övervägt invändningarna\nInvändningen håller delvis.\n'],
    ['08 REFLEKTION/AI/a1.md', { typ: 'ai-konsultation', egen_tanke_först: 'ja', datum: '2026-11-10' }, '## Vad tar jag med mig – med egna ord?\nFler kontrollvariabler.\n'],
    ['08 REFLEKTION/AI/a2.md', { typ: 'ai-konsultation', egen_tanke_först: 'ja', datum: '2026-11-12' }, '## Vad tar jag med mig – med egna ord?\nMät efter två veckor.\n'],
    ['08 REFLEKTION/AI/a3.md', { typ: 'ai-konsultation', egen_tanke_först: 'nej', datum: '2026-11-14' }, '## Vad tar jag med mig – med egna ord?\nOk.\n'],
    ['08 REFLEKTION/Övning 1.md', { typ: 'övning', utan_ai: 'ja', datum: '2026-11-03' }, ''],
    ['08 REFLEKTION/Övning 2.md', { typ: 'övning', utan_ai: 'ja', datum: '2026-11-13' }, ''],
    ['08 REFLEKTION/Förmågegranskning okt.md', { typ: 'förmågegranskning', datum: '2026-10-16', problemformulering: 3, kritisk_prövning: 3, metodkompetens: 2, självständighet: 3, tvärvetenskaplighet: 4, genomförande: 2, akademisk_samverkan: 1 }, ''],
    ['08 REFLEKTION/Förmågegranskning nov.md', { typ: 'förmågegranskning', datum: '2026-11-15', problemformulering: 4, kritisk_prövning: 3, metodkompetens: 3, självständighet: 3, tvärvetenskaplighet: 4, genomförande: 2, akademisk_samverkan: 2 }, ''],
    ['08 REFLEKTION/Felrättning.md', { typ: 'felrättning', status: 'öppen', datum: '2026-10-25' }, ''],
    ['01 RIKTNING/AI som handledare i språkundervisning.md', { typ: 'forskningsfråga', status: 'vilar', vila_till: '2026-11-28', fas: 'utforska' }, '']
  ];
  return notes.map(([p, fm, body]) => ({ path: p, fm, body }));
}

async function panel(browser) {
  const page = await browser.newPage({ viewport: { width: 420, height: 1400 }, deviceScaleFactor: 2 });
  await page.setContent(`<html><head><style>${OBSIDIAN_DARK}${fs.readFileSync(path.join(PLUGIN, 'styles.css'), 'utf8')}</style></head><body><div class="frame" id="frame"></div></body></html>`);
  await page.evaluate(({ src, notes }) => {
    const P = HTMLElement.prototype;
    P.createEl = function (tag, o = {}) {
      const el = document.createElement(tag);
      if (o.cls) el.className = [].concat(o.cls).join(' ');
      if (o.text != null) el.textContent = o.text;
      this.appendChild(el); return el;
    };
    P.createDiv = function (o = {}) { return this.createEl('div', typeof o === 'string' ? { cls: o } : o); };
    P.empty = function () { this.innerHTML = ''; };
    P.addClass = function (c) { this.classList.add(c); };
    P.setAttr = function (k, v) { this.setAttribute(k, v); };
    const files = notes.map(n => ({ path: n.path, basename: n.path.split('/').pop().replace(/\.md$/, ''), stat: {} }));
    const byPath = Object.fromEntries(notes.map(n => [n.path, n]));
    const app = {
      vault: { getMarkdownFiles: () => files, cachedRead: async f => byPath[f.path].body, getAbstractFileByPath: () => null },
      metadataCache: { getFileCache: f => ({ frontmatter: byPath[f.path].fm }), on: () => ({}) },
      workspace: { getActiveFile: () => null, getLeavesOfType: () => [] }
    };
    class Plugin { constructor() { this.app = app; } registerView(t, c) { this.creator = c; } registerEvent() {} addRibbonIcon() {} addCommand() {} }
    class ItemView { constructor() { this.app = app; this.contentEl = document.getElementById('frame'); } }
    const obsidian = { Plugin, ItemView, Notice: class {}, Modal: class {} };
    const module = { exports: {} };
    new Function('module', 'exports', 'require', src)(module, module.exports, () => obsidian);
    const plugin = new module.exports();
    plugin.onload();
    window.__view = plugin.creator({});
  }, { src: fs.readFileSync(path.join(PLUGIN, 'main.js'), 'utf8'), notes: exampleVault() });
  await page.evaluate(() => window.__view.renderDashboard());
  await page.waitForTimeout(200);
  const frame = await page.$('#frame');
  await frame.screenshot({ path: path.join(OUT, 'panel.png') });
  await page.close();
}

function sh(cmd, args, env = {}) {
  return execFileSync(cmd, args, { cwd: ROOT, env: { ...process.env, ...env }, encoding: 'utf8' });
}

async function terminal(browser) {
  const env = {
    FORSKAROS_PRINCIPER: path.join(ROOT, 'system_files/usr/share/forskaros/principer.txt'),
    FORSKAROS_PROFILDIR: path.join(ROOT, 'system_files/usr/share/forskaros/profiler')
  };
  const princip = sh('bash', ['system_files/usr/bin/forskaros-princip'], env).replace(/\x1b\[[0-9;]*m/g, '');
  const lista = sh('bash', ['system_files/usr/bin/forskaros-setup', '--lista'], env).split('\n').slice(0, 30).join('\n');
  const esc = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;');
  const html = `<html><body style="margin:0;background:#0f1b2a;padding:24px;font:13px/1.45 'DejaVu Sans Mono',monospace;color:#d6dde5">
    <div style="background:#16212e;border-radius:10px;padding:18px 20px;width:860px;box-shadow:0 8px 30px #0008">
    <div style="color:#7d8b99">${esc(princip)}</div>
    <div><span style="color:#7bb662">forskare@forskaros</span>:<span style="color:#2e86ab">~</span>$ forskaros-setup --lista</div>
    <pre style="margin:0;font:inherit">${esc(lista)}\n…</pre></div></body></html>`;
  const page = await browser.newPage({ viewport: { width: 908, height: 700 }, deviceScaleFactor: 2 });
  await page.setContent(html);
  const box = await page.$('div');
  await box.screenshot({ path: path.join(OUT, 'terminal.png') });
  await page.close();
}

async function wallpaper(browser) {
  const page = await browser.newPage({ viewport: { width: 1600, height: 900 }, deviceScaleFactor: 1 });
  const svg = fs.readFileSync(path.join(ROOT, 'system_files/usr/share/forskaros/identitet/forskaros-bakgrund-mork.svg'), 'utf8');
  await page.setContent(`<html><body style="margin:0">${svg.replace('width="3840" height="2160"', 'width="1600" height="900"')}</body></html>`);
  await page.screenshot({ path: path.join(OUT, 'skrivbord.png') });
  await page.close();
}

(async () => {
  const browser = await chromium.launch();
  await panel(browser);
  await terminal(browser);
  await wallpaper(browser);
  await browser.close();
  console.log(`Skärmdumpar sparade i ${OUT}`);
})();
