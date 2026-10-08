# JevGB: korte samenvatting (NL)

> Onofficieel communityproject. Niet verbonden aan of goedgekeurd door xAI. Grok is een handelsmerk van de eigenaar.

**Wat is het?** Een kleine open-source router (MIT) die Grok Bot aanroept vóór duur werk. Gebaseerd op [Bodila51/grok-bot-jev](https://github.com/Bodila51/grok-bot-jev), met bronvermelding.

**Wat is er nieuw ten opzichte van upstream?**
- **Overdracht aan Grok Build** (`handoff_build`): codewerk gaat als compacte brief naar Grok Build (doel, repo, bestanden, randvoorwaarden, acceptatiecriteria, wat niet aangeraakt mag worden, samengevatte context), in plaats van de hele chat. Grok Build meldt terug met een kort `build-result`-blok dat de bot direct kan doorgeven.
- **Echte tokenboekhouding**: per taak een schatting van baseline (wat er anders verstuurd was), actual (wat er nu verstuurd is) en router-overhead, opgeslagen als JSONL. `jevgb report` en het dashboard vatten het samen, inclusief taken waar het méér kostte dan het opleverde.
- **Bewakers** die besparing waarschijnlijk maken (niet gegarandeerd): contextbudget, cache met verlooptijd, dubbele tool-calls overslaan, stoppen na herhaalde dezelfde fout, samenvatting vóór overdracht.
- **Werkt offline en gratis**: zonder `TYPESAFE_API_KEY` gebruikt hij vaste regels (Engels en Nederlands). Geen netwerk, geen account.
- **Dashboard** (lokaal, zonder CDN), **landingspagina**, **logo** en **merkgids**.

**Creditcard?** TypeSafe Jev is betaald. Volgens een [extern bericht van 6 oktober 2026](https://jevainews.com/news/typesafe-signups-paused/) beginnen nieuwe accounts met $0 tegoed. Bellen vraagt om opgeladen tegoed (kaart) of een kortingscode. Gebruik daarom `classifier: local`, dan werkt alles zonder kaart. Grok Build zelf vraagt een xAI-abonnement of API-sleutel.

**Wat het níét belooft:** geen gegarandeerde tokenbesparing. Alle getallen zijn schattingen (tiktoken als benadering, of tekens/4), niet de tokenizer van Grok. De demo-cijfers zijn **gesimuleerd** met nep-tekst.

**Snel proberen**
```bash
git clone https://github.com/SuperfastSimon/jevgb.git && cd jevgb
python3 -m venv .venv && .venv/bin/pip install -e ".[tokens,dev]"
.venv/bin/python -m pytest -q
.venv/bin/python scripts/demo_savings.py     # gesimuleerd rapport
.venv/bin/jevgb dashboard                       # http://127.0.0.1:8765
```

Broncode: https://github.com/SuperfastSimon/jevgb (publiek, MIT). GitHub Pages en Sponsors zijn nog niet ingeschakeld.
