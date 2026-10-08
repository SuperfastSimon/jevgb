# JevGB: zakelijke onderbouwing (NL)

> **Disclaimer.** JevGB is een onofficieel communityproject. Het is niet verbonden aan of goedgekeurd door xAI. Grok is een handelsmerk van de eigenaar. TypeSafe en Jev zijn van TypeSafe. Dit is geen juridisch of fiscaal advies.

Externe feiten hebben een bron en een raadpleegdatum. Alle omzetgetallen zijn **verzonnen voorbeeldaannames**, geen marktdata. De Engelse versie ([BUSINESS.md](BUSINESS.md)) bevat dezelfde inhoud met alle links.

## 1. Voor wie

- **Grok Bot-gebruikers** die werk doorzetten naar Grok Build of subagents en zien dat hun tegoed sneller opgaat dan verwacht. De typische lekken: hele chats doorsturen, onderzoek opnieuw doen, herhaalde mislukte pogingen.
- **Grok Build-gebruikers** die vage, te lange opdrachten krijgen. Een gestructureerde brief met acceptatiecriteria en een "niet aanraken"-lijst maakt runs korter en veiliger.
- **Kleine teams** die lokaal en controleerbaar willen zien waar agent-tokens heen gaan, zonder data naar derden te sturen.

**Het pijnpunt.** Grok Build vraagt een xAI-abonnement of een apart betaalde API-sleutel ([x.ai](https://x.ai/news/grok-build-cli), geraadpleegd 2026-10-08). Volgens Engadget raken gratis gebruikers snel door hun tokens heen, en kosten SuperGrok-abonnementen $30 tot $300 per maand met wekelijkse limieten ([Engadget](https://www.engadget.com/2249020/how-to-use-spacexai-grok-build/), geraadpleegd 2026-10-08). Tokens die niet opgaan aan het herlezen van context, blijven over voor echt werk.

**Wat we niet verkopen:** gegarandeerde besparing. De geloofwaardigheid zit erin dat het grootboek ook verliesposten laat zien.

## 2. Licentie

- **Upstream** (Bodila51/grok-bot-jev) is MIT, gecontroleerd in `LICENSE` op 2026-10-08. Aanpassen, herverspreiden en commercieel gebruik mag, zolang copyright en licentietekst meegaan.
- **Keuze: MIT voor de hele repo.** Eén licentie, geen compatibiliteitsvragen, laagste drempel voor bedrijven. Apache-2.0 geeft een expliciete octrooilicentie en mag MIT-code bevatten, maar twee licenties in een kleine repo verwarren meer dan ze beschermen.
- **Naamsvermelding:** in `LICENSE` en `NOTICE`.
- MIT geeft **geen merkrechten**. Omdat "GB" verwijst naar een merk van een ander (Grok Bot), kunnen we zelf weinig merkrecht claimen.

## 3. Open core

**Altijd gratis (MIT):** de router, de offline classifier, de bewakers, de cache, de brief en het `build-result`-contract, het tokengrootboek, `jevgb report`, het lokale dashboard en de skills.
**Mogelijk betaald:** een gehost teamdashboard, een pro skill-pakket (brief-sjablonen en AGENTS.md-profielen per stack), installatie en ondersteuning, en extra's voor sponsors.

## 4. Inkomstenopties zonder creditcard

De opties hieronder zijn gekozen zonder **creditcard**-vereiste. Geld *ontvangen* vraagt meestal een **bankrekening en identiteitscontrole**, en dat is iets anders. Controleer elke aanmeldpagina zelf.

| Optie | Kosten (bron, 2026-10-08) | Creditcard nodig? | Toelichting / alternatief |
| --- | --- | --- | --- |
| **GitHub Sponsors** | 0% bij sponsoring vanaf persoonlijke accounts, tot 6% vanaf organisaties ([GitHub Docs](https://docs.github.com/en/sponsors/sponsoring-open-source-contributors/about-sponsorships-fees-and-taxes)) | **Nee** voor ontvangen. Wel bank- en belastinggegevens, Stripe Connect-verificatie, 2FA en een ondersteunde regio | **Beste eerste stap.** Uitbetaling kan ook via een fiscal host. |
| **Open Collective** (Open Source Collective) | 10% hostfee plus betaalkosten ([OSC](https://docs.oscollective.org/welcome-and-introduction-to-osc/fees)). Open Collective Europe: 6% | **Nee.** Uitbetaling als declaratie via PayPal of Wise | Transparant, handig voor bedrijven. |
| **Installatie / support** | alleen bankkosten | **Nee**: factuur en overboeking | Voor facturen is waarschijnlijk een KvK-inschrijving nodig. Controleer zelf KvK- en Belastingdienstregels. |
| **Pro skill-pakket** | afhankelijk van het platform | **Controleren.** Gumroad, Lemon Squeezy en de Ko-fi-shop betalen uit naar bank of PayPal, maar de voorwaarden verschillen | Alternatief: als sponsor-extra via GitHub Sponsors, of op factuur. |
| **Gehost teamdashboard** | betaalprovider + hosting | **Waarschijnlijk ja**: hosting vraagt meestal een kaart | Uitstellen. Alternatief: een **self-hosted teameditie** met licentie en support op factuur. |
| **Affiliate-links** | per programma | wisselt | Alleen voor tools die het project echt gebruikt. Altijd labelen. Nooit in de CLI of het lokale dashboard. Nooit suggereren dat het officieel van xAI is. |

## 5. Van bezoek naar inkomen

README (screenshot, quickstart, Sponsor-knop) → landingspagina op **GitHub Pages** (gratis) → documentatie → demo-GIF (gelabeld als gesimuleerd) → "powered by"-link in het dashboard (met `?ref=dashboard`; het dashboard stuurt zelf niets) → nieuwsbrief via **Buttondown** (gratis tot 100 abonnees, [prijzen](https://buttondown.com/pricing?plan=free), 2026-10-08) → sponsor, pakket of installatie.

Klikken meten we privacyvriendelijk met **GoatCounter** (gratis gehost bij redelijk gebruik, zonder unieke gebruikers-ID's, [goatcounter.com](https://www.goatcounter.com/), 2026-10-08), alleen op de publieke landingspagina, zonder cookies. Daarnaast gebruiken we het ingebouwde verkeersoverzicht van GitHub. **Nooit telemetrie in de CLI of het dashboard.**

## 6. Omzetmodel (formule)

```
R = N_gh·A_gh·(1 − f_gh) + N_oc·A_oc·(1 − f_oc − p_oc) + N_pack·P_pack·(1 − f_mor)
  + H_setup·r_uur + N_team·P_team·(1 − f_proc) − C_vast
N_gh + N_oc ≈ V · i · a · s   (bezoekers · installatie% · na een maand nog actief% · sponsor%)
```

**Voorbeeld met uitsluitend verzonnen aannames, geen marktdata:** V = 1.000, i = 5%, a = 40%, s = 25%. Dat geeft 5 sponsors: 4 × €5 via GitHub (0% fee) = €20 en 1 × €10 via OSC (10% + 3% aangenomen) = €8,70. Daarbij 3 pakketten × €19 (10% platformfee aangenomen) = €51,30, en 2 uur installatie × €60 = €120. Vaste kosten zijn €0 (gratis tiers).
**R ≈ €200 per maand onder deze verzonnen aannames.** Vervang de waarden na 30 dagen door eigen meetdata. In dit voorbeeld is installatiewerk de grootste hefboom.

## 7. Risico's

- **Afhankelijk van Grok Bot en Grok Build** (skills, `AGENTS.md`, `grok -p`). *Maatregel:* de brief is gewone markdown die in elke coding-agent werkt.
- **Afhankelijk van TypeSafe.** Aanmelden lag stil vanaf 22 september 2026 en ging op 27 september weer open, zonder gratis tegoed voor nieuwe accounts ([bericht](https://jevainews.com/news/typesafe-signups-paused/), bijgewerkt 2026-10-06). *Maatregel:* de offline classifier is de standaard.
- **Metingen opgevat als belofte.** *Maatregel:* schattingslabels, de kwaliteit van de basis, zichtbare verliesposten en SIMULATED-banners.
- **Merkrisico ("GB" staat voor Grok Bot).** De werknaam is nu **JevGB**. Het volledige woord "Grok" is uit naam, logo, pakket en commando verdwenen. Dat **verlaagt het risico, maar haalt het niet weg**: "GB" is een afkorting van Grok Bot, en dat staat ook zo in de README. Een rechthebbende kan nog steeds bezwaar maken (klacht, naamconflict op GitHub of PyPI, gedwongen naamswijziging). *Maatregelen:* een disclaimer (README, footer van de landingspagina, footer van het dashboard, dit document), geen logo's, kleuren of lettertypen van xAI, geen "officieel", "Grok" alleen beschrijvend gebruiken, en een beeldmerk dat los van de naam werkt.
  - **Naamcontrole** (2026-10-08): `jevgb` heeft PyPI 404 en npm 404 (vrij). Op GitHub vond ik 1 ongerelateerde repo (`qzqdz/jevgboost`) en 1 ongerelateerd account (`jevgbur`), geen duidelijke botsing. `jgb` is bezet op PyPI en wordt dus alleen als CLI-alias gebruikt.
  - **Reservenamen zonder enige verwijzing naar Grok:** **Handbrief** (PyPI 404, npm 404, GitHub 0 repo's) en **Keelbrief** (PyPI 404, npm 404, GitHub 0). Dit is geen merkonderzoek: check EUIPO/BOIP vóór je investeert.
- **Forks en concurrentie** zijn toegestaan onder MIT. *Maatregel:* snel leveren en eerlijk meten.
- **Tijd en administratie.** Check de Nederlandse inschrijvings- en belastingregels vóór de eerste factuur.

## 8. 30 / 60 / 90 dagen

- **Dag 1–30:** publieke repo (na jouw akkoord), site op GitHub Pages met GoatCounter, aanmelden bij GitHub Sponsors. Twee weken in shadow-modus op eigen werk draaien en het *echte* rapport publiceren, inclusief verlies. Demo-GIF maken (gelabeld als gesimuleerd).
- **Dag 31–60:** installatie plus logreview aanbieden op factuur, het skill-pakket als sponsor-extra testen, de nieuwsbrief starten, `?ref=` op alle links zetten en de classifier verbeteren met echte fouten.
- **Dag 61–90:** kanalen vergelijken en de zwakste schrappen. Bij vraag een self-hosted teameditie uitwerken. Het merkrisico opnieuw wegen en zo nodig hernoemen naar Handbrief of Keelbrief. Een transparantieverslag publiceren.
