'use strict';

const { Plugin, ItemView, Notice } = require('obsidian');
const VIEW_TYPE = 'forskaros-dashboard';
const FOLDERS = [
  '00 START', '01 RIKTNING', '02 HYPOTESER', '03 EVIDENS',
  '04 EXPERIMENT', '05 FRIKTION', '06 FÖRÄNDRING',
  '07 SAMVERKAN', '08 REFLEKTION', '09 ARKIV'
];

const TYPES = {
  pass: { label: 'Forskarpass', folder: '08 REFLEKTION', prefix: 'Pass', render: (date) => `---
typ: forskarpass
datum: ${date}
status: pågår
---
# Forskarpass ${date}

> Börja med att tänka själv. Be sedan en AI eller människa om kritik.

## 1. Frågan jag försöker förstå


## 2. Min egen förklaring – utan AI


## 3. Mångfald: tre alternativa perspektiv
- Perspektiv A:
- Perspektiv B:
- Perspektiv C:

## 4. Friktion: vad skulle visa att jag har fel?


## 5. Källor och evidens
- Källa:
- Vad källan faktiskt stöder:
- Osäkerhet:

## 6. Vad har förändrats i min uppfattning?


## 7. Nästa lilla genomförbara steg
- [ ]

## 8. Självständighet
Vad kan jag förklara utan att konsultera en AI?
` },
  hypothesis: { label: 'Ny hypotes', folder: '02 HYPOTESER', prefix: 'Hypotes', render: (date) => `---
typ: hypotes
datum: ${date}
status: oprövad
konfidens: okänd
---
# Hypotes

## Forskningsfråga


## Hypotes (min formulering)


## Prediktioner
1.
2.

## Möjliga konkurrerande förklaringar
1.
2.

## Falsifiering: vilken observation skulle tala emot hypotesen?


## Försöksdesign


## Stödjande källor


## Motstridiga källor


## Samhällelig betydelse och framtid


## Beslut: pröva / omformulera / förkasta
` },
  friction: { label: 'Kritisk prövning', folder: '05 FRIKTION', prefix: 'Motprov', render: (date, source) => `---
typ: motprov
datum: ${date}
status: öppet
---
# Motprov

## Påstående som ska prövas
${source || ''}

## Starkaste motargumentet (steelman)


## Vad är ett empiriskt, snarare än retoriskt, motbevis?


## Hur kan jag själv vara partisk?


## Vad säger den bäst underbyggda avvikande ståndpunkten?


## Vilka belägg saknas?


## Mitt svar EFTER att ha övervägt invändningarna


## Vad skulle övertyga mig om att ändra mig?
` },
  diversity: { label: 'Perspektivmångfald', folder: '03 EVIDENS', prefix: 'Perspektivkarta', render: (date, source) => `---
typ: perspektivkarta
datum: ${date}
---
# Perspektivkarta

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
` },
  change: { label: 'Omprövning', folder: '06 FÖRÄNDRING', prefix: 'Omprövning', render: (date, source) => `---
typ: omprövning
datum: ${date}
---
# Omprövning

## Vad trodde jag tidigare?
${source || ''}

## Vad tror jag nu?


## Vad fick mig att ändra uppfattning?


## Primärkällor och belägg


## Vad är ännu osäkert?


## Vilka handlingar ändrar jag?


## Vilken framtida observation kan få mig att ändra mig igen?
` },
  meeting: { label: 'Forskningsmöte', folder: '07 SAMVERKAN', prefix: 'Möte', render: (date) => `---
typ: forskningsmöte
datum: ${date}
---
# Forskningsmöte

## Deltagare och expertområden


## Vad vill jag lära mig?


## Frågorna jag inte redan kan besvara
1.
2.

## Viktigaste invändningen jag fick


## Överenskommelser och källor


## Uppföljning
- [ ]
` },
  correction: { label: 'Tillit och felrättning', folder: '08 REFLEKTION', prefix: 'Korrigering', render: (date) => `---
typ: felrättning
datum: ${date}
status: öppen
---
# Korrigering och tillit

## Tidigare påstående (mitt eller AI:ns)


## Varför var det fel / missvisande / för tvärsäkert?


## Kontrollerade belägg


## Korrekt slutsats och osäkerhet


## Vad ändrar vi i arbetssättet?


## Hur kontrollerar vi att förbättringen fungerar?
` }
};

function today() {
  // sv-SE returns YYYY-MM-DD in desktop locales that support Intl.
  return new Intl.DateTimeFormat('sv-SE', { year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date());
}

function uniqueStamp() {
  return new Date().toISOString().replace(/[.:]/g, '-');
}

class ForskarOSView extends ItemView {
  constructor(leaf, plugin) {
    super(leaf);
    this.plugin = plugin;
  }
  getViewType() { return VIEW_TYPE; }
  getDisplayText() { return 'ForskarOS'; }
  getIcon() { return 'brain'; }
  async onOpen() { this.renderDashboard(); }
  renderDashboard() {
    const root = this.contentEl;
    root.empty();
    root.addClass('forskaros-panel');
    root.createEl('div', { cls: 'forskaros-kicker', text: 'FORSKAROS / 0.1' });
    root.createEl('h2', { text: 'Tänk djupare.' });
    root.createEl('p', { text: 'Framtiden är den viktigaste tiden. Börja med en fråga, pröva den på riktigt och dokumentera det som förändras.' });

    const all = this.app.vault.getMarkdownFiles();
    const metricRoot = root.createDiv({ cls: 'forskaros-metrics' });
    for (const [name, path] of [['Hypoteser', '02 HYPOTESER/'], ['Motprov', '05 FRIKTION/'], ['Omprövningar', '06 FÖRÄNDRING/']]) {
      const card = metricRoot.createDiv({ cls: 'forskaros-metric' });
      card.createEl('strong', { text: String(all.filter(f => f.path.startsWith(path)).length) });
      card.createEl('span', { text: name });
    }

    root.createEl('h4', { text: 'Skapa ett arbetsprov' });
    const actions = root.createDiv({ cls: 'forskaros-actions' });
    for (const [type, spec] of Object.entries(TYPES)) {
      const button = actions.createEl('button', { text: spec.label });
      button.addEventListener('click', () => void this.plugin.createNote(type));
    }
    root.createEl('div', { cls: 'forskaros-warning', text: 'Du ska kunna förklara slutsatsen utan AI. Fler anteckningar är inte samma sak som mer kunskap.' });
    root.createEl('h4', { text: 'Principer i handling' });
    const principles = [
      ['Mångfald', 'Finn minst tre verkligt olika förklaringar.'],
      ['Friktion', 'Sök aktivt den starkaste invändningen.'],
      ['Tillit', 'Särskilj källa, tolkning och gissning.'],
      ['Envishet + förändring', 'Håll fast vid frågan, inte vid svaret.'],
      ['Bekväm med det obekväma', 'Skriv ned vad du inte förstår.'],
      ['Framtiden', 'Fråga vad upptäckten skulle förändra.']
    ];
    for (const [name, description] of principles) {
      const item = root.createDiv({ cls: 'forskaros-principle' });
      item.createEl('b', { text: name });
      item.createEl('small', { text: description });
    }
    const open = root.createEl('button', { text: 'Läs systemets principer' });
    open.addEventListener('click', () => void this.plugin.openPath('00 START/Principer.md'));
  }
}

module.exports = class ForskarOSPlugin extends Plugin {
  async onload() {
    this.registerView(VIEW_TYPE, leaf => new ForskarOSView(leaf, this));
    this.addRibbonIcon('brain', 'Öppna ForskarOS', () => void this.activateDashboard());
    this.addCommand({ id: 'open-dashboard', name: 'Öppna ForskarOS-panelen', callback: () => void this.activateDashboard() });
    for (const [type, spec] of Object.entries(TYPES)) {
      this.addCommand({ id: `new-${type}`, name: spec.label, callback: () => void this.createNote(type) });
    }
  }

  async ensureFolder(folder) {
    const segments = folder.split('/');
    let current = '';
    for (const part of segments) {
      current = current ? `${current}/${part}` : part;
      if (!(await this.app.vault.adapter.exists(current))) {
        await this.app.vault.createFolder(current);
      }
    }
  }

  async openPath(path) {
    const file = this.app.vault.getAbstractFileByPath(path);
    if (!file) { new Notice(`Hittar inte ${path}`); return; }
    await this.app.workspace.getLeaf(true).openFile(file);
  }

  async createNote(type) {
    const spec = TYPES[type];
    if (!spec) return;
    try {
      const active = this.app.workspace.getActiveFile();
      const source = active ? `[[${active.path.replace(/\.md$/, '')}]]` : '';
      await this.ensureFolder(spec.folder);
      const stamp = uniqueStamp();
      let path = `${spec.folder}/${spec.prefix} ${stamp}.md`;
      let suffix = 1;
      while (await this.app.vault.adapter.exists(path)) {
        path = `${spec.folder}/${spec.prefix} ${stamp}-${suffix++}.md`;
      }
      const file = await this.app.vault.create(path, spec.render(today(), source));
      await this.app.workspace.getLeaf(true).openFile(file);
      this.refreshDashboard();
      new Notice(`${spec.label} skapad lokalt`);
    } catch (error) {
      console.error('ForskarOS createNote failed', error);
      new Notice('Kunde inte skapa anteckningen. Se utvecklarkonsolen.');
    }
  }

  refreshDashboard() {
    for (const leaf of this.app.workspace.getLeavesOfType(VIEW_TYPE)) {
      if (leaf.view && typeof leaf.view.renderDashboard === 'function') leaf.view.renderDashboard();
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
