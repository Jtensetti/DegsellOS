---
typ: handbok
---
# 9. Reproducerbarhet

En analys som bara kan köras på din dator i dag är inte färdig.

**ForskarOS-labbet** är en låst analysmiljö (R, tidyverse, RStudio, Python, Pandoc) som körs likadant överallt:

```bash
cd ~/ForskarOS/"04 EXPERIMENT"/min-studie
forskaros-labb Rscript analys.R      # kör analysen
forskaros-labb version               # miljöns exakta version
```

Klistra in raden från `forskaros-labb version` under *Analysmiljö* i experimentet. Den innehåller avbildningens digest, ett fingeravtryck som pekar på exakt samma miljö om tio år. Vem som helst med Podman eller Docker kan köra om analysen.

**Mer:**
- **Git** för kod och vault: se hur dina uppfattningar ändrats över tid.
- **uv** och **renv** låser Python- och R-paket per projekt.
- **DataLad** och **git-annex** versionshanterar stora datafiler.

## Övning utan AI
Kör en liten analys i labbet. Be någon annan köra om den från din experimentanteckning, utan att fråga dig något. Fungerade det?
