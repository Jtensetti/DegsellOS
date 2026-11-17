# Säkerhet och integritet

## Skydd i dag

- ForskarOS Core gör inga nätverksanrop. Det kontrolleras av ett test.
- Vaulten skapas lokalt och skrivs aldrig över. Bara tilläggets egna filer uppdateras.
- Avbildningarna byggs öppet i GitHub Actions och signeras med sigstore/cosign.
- Basen (Bluefin LTS) får säkerhetsuppdateringar. Vi bygger om varje vecka.
- Obsidian, Zotero och verktyg installeras först efter ett aktivt val.

## Kvarstående risker

- Obsidian och tillägg från andra har egen nätverks- och filåtkomst.
- Ingen automatisk säkerhetskopiering av vaulten än.
- Diskkryptering (LUKS) väljs i installeraren och är inte påtvingad.
- Signaturerna verifieras inte automatiskt av klienten än (policy för bootc saknas).
- Hantera inte sekretessbelagda uppgifter eller personuppgifter från arbetet i
  ForskarOS utan en egen riskbedömning.

## Lokal AI (planerad)

Moln-AI ska aldrig få läsa vaulten utan att forskaren aktivt valt det och sett
exakt vad som skickas. Standard är lokal körning via Ollama.
