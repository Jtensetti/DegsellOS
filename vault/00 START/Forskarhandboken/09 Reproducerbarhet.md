---
typ: handbok
---
# 9. Reproducerbarhet

I skrivbordsappen skapar **Bygg rapport** en körningsmapp med en kopia av underlaget, analyskoden, rapporten och resultaten. **Upprepa** kör analysen på nytt och jämför resultaten byte för byte. Tidigare körningar bevaras när arbetsmaterialet ändras.

Välj **Kör i versionslåst labb** i projektets meny för att använda en bestämd containeravbildning med R och Python. Körningen sparar avbildningens digest och använder den vid upprepning. Den första hämtningen kräver nätåtkomst; projektets analys körs därefter utan nätverk.

För en egen analys utanför projektappen kan du använda labbet direkt:

```bash
cd /sökväg/till/min-studie
degsellos-labb Rscript analys.R
degsellos-labb version
```

Spara miljöns digest tillsammans med kod, data och körinstruktioner. En annan dator behöver Podman eller Docker och kompatibel processorarkitektur. En låst miljö minskar skillnader i programversioner; slump, externa data och hårdvaruberoende beräkningar kan ändå påverka resultatet.

**Versionshantering:** Git kan användas för kod och anteckningar, uv och renv för paketberoenden samt DataLad och git-annex för större datafiler.

## Övning utan AI
Kör en liten analys i labbet. Be någon annan köra om den från din experimentanteckning, utan att fråga dig något. Fungerade det?
