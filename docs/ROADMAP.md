# ForskarOS – färdplan

## 0.1 – Prototyp (från samtalet med ChatGPT)

- [x] Vault, principer, arbetsmetod och tillitskontrakt
- [x] ForskarOS Core med sju arbetsprov
- [x] Test av tillägget mot simulerat Obsidian-API
- [x] ~~NixOS-ISO~~ ersatt av Bluefin-baserad avbildning i 0.2

## 0.2 – Eget OS på färdig grund (pågår)

- [x] Containerfile ovanpå Bluefin LTS (amd64 + arm64)
- [x] `forskaros-init`: skapar vault och uppdaterar tillägget säkert, med tester
- [x] `forskaros-setup`: Obsidian, Zotero, Pandoc, ripgrep, Ollama efter aktivt val
- [x] CI: bygg, publicera till ghcr.io, signera; manuellt bygge av ISO och qcow2
- [ ] Första lyckade bygget i GitHub Actions
- [ ] Starta arm64-disken i UTM på MacBook Neo
- [ ] Installera amd64-ISO:n i en virtuell maskin
- [ ] Verifiera att GNOME:s välkomstguide skapar konto i qcow2-disken

## 0.3 – Profil och identitet

- [ ] GNOME-standardinställningar (fokusläge, favoriter, bakgrund)
- [ ] Egen os-release, logotyp och namn i uppstartsmenyn
- [ ] Verifiering av signaturer på klienten (bootc/containers-policy)
- [ ] Automatisk, krypterad säkerhetskopiering av vaulten

## 0.4 – Kunskapsytan, en egen öppen editor

- [ ] Öppna vault, redigera Markdown (CodeMirror 6), wikilänkar, bakåtlänkar, frontmatter
- [ ] Tilläggsladdare med det urval av API:t som ForskarOS Core använder
- [ ] Paketeras som Flatpak och ingår i avbildningen

## 0.5 – Lokal AI och forskningsmotorer

- [ ] Motståndaren och Revisorn som roller mot lokal Ollama
- [ ] Zotero/BibTeX-koppling, källspårning
- [ ] Månatlig förmågegranskning: det du kan förklara utan AI

## Senare

- [ ] Asahi-baserad avbildning när Apple Silicon (inkl. Neo) kan starta Linux direkt
- [ ] Experimentmiljöer med Nix eller Guix per studie

## Acceptanskriterium

Efter fyra veckor ska forskaren kunna visa ett självständigt arbetsprov med fråga,
hypotes, motprov, kontrollerbara belägg, redovisad osäkerhet och slutsats.
