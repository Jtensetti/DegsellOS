# ForskarOS – färdplan

## 0.1 – Prototyp

- [x] Vault, principer, arbetsmetod och tillitskontrakt
- [x] ForskarOS Core med sju arbetsprov
- [x] Test av tillägget mot simulerat Obsidian-API
- [x] ~~NixOS-ISO~~ ersatt av Bluefin-baserad avbildning i 0.2

## 0.2 – Avbildning på Bluefin LTS

- [x] Containerfile ovanpå Bluefin LTS (amd64 + arm64)
- [x] `forskaros-init`: skapar vault och uppdaterar tillägget säkert, med tester
- [x] `forskaros-setup`: Obsidian, Zotero, Pandoc, ripgrep, Ollama efter aktivt val
- [x] CI: bygg, publicera till ghcr.io, signera; manuellt bygge av ISO och qcow2
- [x] Första lyckade bygget i GitHub Actions (amd64 + arm64, publicerat till ghcr.io)
- [ ] Starta arm64-disken i UTM på MacBook Neo
- [ ] Installera amd64-ISO:n i en virtuell maskin
- [ ] Verifiera att GNOME:s välkomstguide skapar konto i qcow2-disken

## 0.3 – Arbetsmetoden i tillägget

- [x] Den kreativa forskningscykeln i sju faser med faskrav och öppen fasbeslutslogg
- [x] Regelbaserad granskning (*Att åtgärda*)
- [x] AI-konsultationer med uppgifter, lägen och logg
- [x] Självständighetsmått och månatlig förmågegranskning
- [x] Epistemisk märkning, idéparkering, vila
- [x] Bakgrund och exempelfråga i vaulten
- [ ] Prova metoden på riktigt i fyra veckor och justera reglerna efter erfarenheten
- [ ] Undersöka om måtten mäter det de ska

## 0.3.1 – Verktyg och VM

- [x] Verktygsprofiler: grund, skriva, statistik, programmering, kvalitativ, idéer, lokal AI, proprietärt/moln
- [x] Grundverktygen installeras automatiskt vid första start (systemtjänst, försöker igen utan nätverk)
- [x] Verktygslådan öppnas vid första inloggningen
- [x] Forskningsportal per fas i vaulten, med svenska resurser
- [x] Panelen visar verktyg för fasen
- [x] UTM/QEMU: spice-vdagent och qemu-guest-agent
- [x] Docka med forskningsverktygen
- [x] CI kontrollerar att alla verktyg finns för amd64 och arm64
- [ ] Delad mapp mellan Mac och VM (virtiofs/9p)
- [ ] Öppen självhostad AI-sök som alternativ till Perplexity (t.ex. Perplexica)
- [ ] Färdig `.utm`-paketering med inställningar för RAM, CPU och skärm

## 2027.1

- [x] Appmappar per fas, verktygskatalog, verktygssidor, rekommenderat urval
- [x] VM: forskare/forskare med lösenordsbyte, delad mapp, UTM-paketering från mall
- [x] Logotyp och bakgrund
- [x] Fokusläge med fokuslogg
- [x] ForskarOS-labbet (R, tidyverse, RStudio, Python) för amd64 och arm64
- [x] Forskarhandboken, tolv kapitel med övningar utan AI
- [x] Kvartalsversioner, CHANGELOG och släppprocess
- [ ] UTM-mall från en riktig UTM (`vm/utm/config.plist`)
- [ ] Testa på MacBook Neo: start, inloggning, verktygslåda, delad mapp, labbet
- [ ] Släpp 2027.1



- [x] GNOME-standardinställningar (fokusläge, favoriter, bakgrund)
- [ ] Egen os-release och namn i uppstartsmenyn (logotypen finns)
- [ ] Verifiering av signaturer på klienten (bootc/containers-policy)
- [ ] Automatisk, krypterad säkerhetskopiering av vaulten

## 0.5 – Kunskapsytan, en egen öppen editor

- [ ] Öppna vault, redigera Markdown (CodeMirror 6), wikilänkar, bakåtlänkar, frontmatter
- [ ] Tilläggsladdare med det urval av API:t som ForskarOS Core använder
- [ ] Paketeras som Flatpak och ingår i avbildningen

## 0.6 – Lokal AI och forskningsmotorer

- [ ] AI-konsultationer direkt mot lokal Ollama, med samma logg och krav
- [ ] Zotero/BibTeX-koppling, källspårning
- [ ] Månatlig förmågegranskning: det du kan förklara utan AI

## Senare

- [ ] Asahi-baserad avbildning när Apple Silicon (inkl. Neo) kan starta Linux direkt
- [ ] Experimentmiljöer med Nix eller Guix per studie

## Acceptanskriterium

Efter fyra veckor ska forskaren kunna visa ett självständigt arbetsprov med fråga,
hypotes, motprov, kontrollerbara belägg, redovisad osäkerhet och slutsats.
