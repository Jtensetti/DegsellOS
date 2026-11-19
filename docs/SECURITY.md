# Säkerhet och integritet

## Skyddat forskningsprojekt

Skyddsnivån i `projekt.json` styr de processer som DegsellOS startar för analys och rapportbygge. Ett skyddat projekt körs i bubblewrap, eller i det versionsbundna labbet med Podman och avstängt nätverk. Om den begärda isoleringen inte kan upprättas avbryts körningen.

I bubblewrap-sandlådan gäller följande:

- Nätverket är avstängt genom en egen nätverksnamnrymd.
- Hemkataloger, körmiljöns uttag och vanliga monteringsplatser döljs: `/home`, `/var/home`, `/root`, `/run`, `/tmp`, `/var/tmp`, `/mnt`, `/var/mnt`, `/media` och `/srv`.
- Körningsmappen är skrivbar. Övriga synliga systemfiler är skrivskyddade.
- Sessionens miljövariabler följer inte med.

Detta skyddar analysen från åtkomst till de dolda platserna och från att skicka data över nätet. Det isolerar inte alla filer på datorn från analysen. Lägg inte privata data på andra synliga systemplatser.

Program som öppnas separat på skrivbordet har sina vanliga behörigheter. Urklipp, webbläsare, AI-tjänster och administratörsåtkomst omfattas inte. Skyddsnivån krypterar inte projektmappen och hindrar inte andra processer med samma användares filbehörigheter från att läsa den.

[Använda skyddat material](PROJEKT.md#skyddat-material)

## Data och säkerhetskopior

Anteckningar och forskningsprojekt lagras som lokala filer. Vid uppdatering ersätts de medföljande filerna för Core, verktygskorten och Forskarhandboken. Lägg egna anteckningar utanför dessa systemunderhållna mappar. Automatisk krypterad säkerhetskopiering ingår inte; konfigurera säkerhetskopiering för både projekt och vault.

En körning innehåller en kopia av underlaget, även ursprungliga data och citat. Projektets `granskningsunderlag.json` kan dessutom innehålla tidigare citat som rättats i arbetsmaterialet. Kontrollera innehållet och mottagarens behörighet innan en körning eller ett helt projekt delas.

## Program och externa tjänster

Grundprofilen hämtas från Flathub och innehåller bland annat Zotero och LibreOffice. Obsidian och genvägar till molntjänster kräver ett separat val. Andra program och tillägg har egna villkor och behörigheter.

DegsellOS Core gör inga nätverksanrop. Vid en AI-konsultation väljer forskaren vilken text som kopieras till en annan tjänst. Zotero-importen i skrivbordsappen kontaktar Zoteros lokala API på samma dator.

## Systemavbildningar

GitHub Actions bygger systemavbildningen och signerar dess manifest med sigstore/cosign. Kontrollsummorna för installationsmedierna publiceras tillsammans med nedladdningarna. Bootc-klienten har ännu ingen automatiskt upprätthållen policy för dessa signaturer.

[Installation och kontrollsummor](INSTALLATION.md) · [Släpprocess](RELEASE.md)
