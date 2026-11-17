# ForskarOS – arkitektur

```
┌───────────────────────────────────────────────┐
│ ForskarOS Core   (tillägg: metoden i praktiken)│
├───────────────────────────────────────────────┤
│ Editor: Obsidian i dag, egen öppen editor      │
│         ("Kunskapsytan") på sikt               │
├───────────────────────────────────────────────┤
│ Vault: ~/ForskarOS i ren Markdown              │
├───────────────────────────────────────────────┤
│ Verktygslåda i profiler (Flatpak, Homebrew,    │
│ uv): kontor, källor, statistik, skrivande,     │
│ kvalitativ analys, lokal AI. Grund automatiskt │
├───────────────────────────────────────────────┤
│ ForskarOS-lager: forskaros-init/-setup,        │
│ autostart, seed-vault                          │
├───────────────────────────────────────────────┤
│ Bluefin LTS (GNOME, bootc, Flatpak, Homebrew)  │
│ amd64 + arm64                                  │
└───────────────────────────────────────────────┘
```

## Beslut

**Vi bygger på en färdig distribution.** Bluefin LTS ger hårdvarustöd,
säkerhetsuppdateringar, atomära uppdateringar med rollback och stöd för både
amd64 och arm64. Vi underhåller bara det som är unikt för ForskarOS.

**Nix är inte grunden längre.** NixOS-versionen i 0.1 byggdes aldrig och fungerar
dåligt på Apple Silicon. Reproducerbarhet för experiment (Nix eller Guix per
studie) hör till forskningslagret, inte till skrivbordet.

**Liten avbildning.** Program bakas inte in i avbildningen. Grundprofilen
installeras som Flatpak vid första start (`forskaros-grund.service`), resten
väljer forskaren i verktygslådan (`forskaros-setup`). Profilerna är datafiler i
`/usr/share/forskaros/profiler`, så att de går att testa och utöka. Det minskar
konflikter med basens uppdateringar och låter forskaren välja.

**Proprietärt ingår inte.** Obsidian distribueras inte i avbildningen.
Vaultformatet (Markdown, wikilänkar, frontmatter) är öppet. Därför kan en egen
öppen editor byggas utan att kopiera Obsidians kod, och den ska köra
ForskarOS Core via ett kompatibelt urval av plugin-API:t.

**Forskarens data är helig.** `forskaros-init` skapar vaulten en gång och
uppdaterar därefter bara tilläggets egna tre filer. Anteckningar rörs aldrig.

## Hur principerna syns i systemet

- **Mångfald:** perspektivkartan kräver flera teorier med olika antaganden.
- **Tillit:** felrättningar sparas i historiken. Inga nätverksanrop sker utan aktivt val.
- **Friktion och ifrågasättande:** motprovet frågar vad som kan kullkasta hypotesen.
- **Bekväm med det obekväma:** forskarpasset kräver en lista över det du inte förstår.
- **Envishet och förändring:** omprövningar dokumenterar hur och varför en uppfattning ändrats.
- **Framtiden:** hypotesmallen frågar vad upptäckten skulle göra möjligt.
- **Kompetens:** varje pass frågar vad du kan förklara utan AI.
- **Möten och nätverk:** forskningsmötet dokumenterar kritik från verkliga människor.
