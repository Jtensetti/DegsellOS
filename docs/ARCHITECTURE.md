# Arkitektur

```
ForskarOS Core (Obsidian-tillägg)      faser, granskning, mallar, AI-logg
Vault ~/ForskarOS                      Markdown med YAML-frontmatter
Verktyg                                Flatpak, Homebrew och uv, i profiler
ForskarOS-lagret                       forskaros-* kommandon, systemd-tjänster, dconf
Bluefin LTS                            GNOME, bootc, CentOS Stream 10, amd64 + arm64
```

## Beslut

**Bluefin LTS som bas.** Ger hårdvarustöd, säkerhetsuppdateringar och atomära uppdateringar med rollback för både amd64 och arm64. ForskarOS lägger bara till det som är specifikt för projektet. Nix var första förslaget men byggdes aldrig, och NixOS har svagt stöd för Apple Silicon.

**Program bakas inte in i avbildningen.** Grundprofilen installeras som Flatpak vid första start (`forskaros-grund.service`), övriga profiler med `forskaros-setup`. Det håller avbildningen liten och undviker konflikter med basens uppdateringar.

**En källa för verktygen.** `katalog/verktyg.json` genererar profiler, programmenyns mappar och verktygssidorna i vaulten. Ett test kontrollerar att de genererade filerna är i synk.

**Obsidian ingår inte.** Obsidian är proprietärt och får inte distribueras. Vaultformatet är öppet (Markdown, wikilänkar, frontmatter), så en egen editor kan byggas senare utan att röra Obsidians kod.

**Vaulten skrivs inte över.** `forskaros-init` skapar `~/ForskarOS` en gång. Därefter uppdateras bara tilläggets filer och systemets egna mappar (`00 START/Verktyg`, `00 START/Forskarhandboken`).

**Tillägget gör inga nätverksanrop.** AI-konsultationer blir text som användaren kopierar. Ett test kontrollerar att källkoden saknar nätverksanrop.

## Tillägget

`main.js` har två delar: regler och mallar som rena funktioner (testas i `tests/engine.test.js`) och Obsidian-gränssnittet (testas mot ett simulerat API i `tests/plugin.test.js`). All data läses från anteckningarnas frontmatter, främst `typ`, `fas`, `status`, `fråga` och `datum`.
