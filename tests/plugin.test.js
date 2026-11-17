'use strict';
const assert = require('node:assert/strict');
const Module = require('node:module');
const path = require('node:path');

const files = new Map();
const folders = new Set();
const commands = [];
let activeFile = null;
const app = {
  vault: {
    adapter: { exists: async p => folders.has(p) || files.has(p) },
    createFolder: async p => { folders.add(p); },
    create: async (p, content) => {
      assert(!files.has(p), 'Should never overwrite an existing note');
      const file = { path: p, basename: path.basename(p, '.md'), content };
      files.set(p, file);
      return file;
    },
    getMarkdownFiles: () => [...files.values()],
    getAbstractFileByPath: p => files.get(p) || null
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
  addRibbonIcon() {}
  addCommand(command) { commands.push(command); }
}
class ItemView {}
class Notice { constructor() {} }
const origLoad = Module._load;
Module._load = function (request, parent, isMain) {
  if (request === 'obsidian') return { Plugin, ItemView, Notice };
  return origLoad(request, parent, isMain);
};
const ForskarOSPlugin = require('../vault/.obsidian/plugins/forskaros-core/main.js');
Module._load = origLoad;

(async () => {
  const p = new ForskarOSPlugin();
  await p.onload();
  assert.equal(commands.length, 8, 'Dashboard plus 7 note commands');
  assert.equal(p.registeredView.type, 'forskaros-dashboard');

  for (const type of ['pass', 'hypothesis', 'friction', 'diversity', 'change', 'meeting', 'correction']) {
    await p.createNote(type);
  }
  assert.equal(files.size, 7);
  assert([...files.values()].some(f => f.content.includes('Min egen förklaring – utan AI')));
  assert([...files.values()].some(f => f.content.includes('Falsifiering')));
  assert([...files.values()].some(f => f.content.includes('Vad trodde jag tidigare?')));
  assert([...files.values()].some(f => f.content.includes('Vad skulle övertyga mig')));
  assert([...files.values()].every(f => !f.path.includes('undefined')));

  // Repeating a command must create a new document, never overwrite.
  await p.createNote('pass');
  assert.equal(files.size, 8);
  assert.equal([...files.keys()].length, new Set(files.keys()).size);

  // The plugin must be self-contained: no fetch(), HTTP or LLM API calls.
  const source = require('node:fs').readFileSync(require.resolve('../vault/.obsidian/plugins/forskaros-core/main.js'), 'utf8');
  assert(!/\bfetch\s*\(/.test(source));
  assert(!/https?:\/\//.test(source));
  process.stdout.write('OK: plugin commands, local notes, no overwrite, no network calls\n');
})().catch(e => { console.error(e); process.exitCode = 1; });
