# JevGB: business rationale

> **Disclaimer.** JevGB is an unofficial community project. It is not affiliated with or endorsed by xAI. Grok is a trademark of its owner. TypeSafe and Jev belong to TypeSafe. Nothing here is legal or tax advice.

All external facts below carry a source and an access date. All revenue numbers are **illustrative assumptions**, not market data.

## 1. Who it is for

- **Grok Bot users** who hand work to Grok Build or subagents and see their included usage run out faster than expected. Long chats that get forwarded whole, research that gets redone, and retries that loop are the typical leaks.
- **Grok Build users** who get vague, overlong prompts from a bot or a teammate. A structured brief with acceptance criteria and a do-not-touch list makes runs shorter and safer.
- **Small teams** who want a local, auditable view of where agent tokens go, without sending data to a third party.

**The pain point.** Access to Grok Build comes with an xAI plan or a separately billed API key ([x.ai news](https://x.ai/news/grok-build-cli); [continuumcode guide](https://continuumcode.ai/guides/grok-cli/), both accessed 2026-10-08). Engadget describes free users running out of tokens quickly and paid SuperGrok plans from $30 to $300 per month with weekly usage limits ([Engadget](https://www.engadget.com/2249020/how-to-use-spacexai-grok-build/), accessed 2026-10-08). Usage is capped, so tokens not spent on re-reading context are tokens left for real work. JevGB's job is to make that visible and, where the data supports it, smaller.

**What we don't sell:** guaranteed savings. The product's credibility rests on the ledger showing negatives too.

## 2. License

- **Upstream:** [Bodila51/grok-bot-jev](https://github.com/Bodila51/grok-bot-jev) is MIT (checked in the cloned `LICENSE`, 2026-10-08). MIT allows modification, redistribution and commercial use, as long as the copyright notice and license text stay with the code.
- **Choice: MIT for the whole repository.** We use the same license as upstream: one license, no compatibility questions, and minimal friction for companies trying it. Apache-2.0 would add an explicit patent grant and is compatible with including MIT code (keep the MIT notice), but mixing two licenses in a small repo confuses contributors more than it protects them. Revisit if a company contributor asks for a patent grant.
- **Attribution:** `LICENSE` keeps the upstream copyright line, and `NOTICE` lists what was taken from upstream.
- **What the license doesn't cover:** the name and logo. MIT grants no trademark rights. Because "GB" abbreviates a third-party brand (Grok Bot), our own claim to the name is weak (see Risks).

## 3. Open core: what stays free, what could be paid

| Free forever (MIT) | Possible paid layer |
| --- | --- |
| Router, offline classifier, guards, cache | **Hosted team dashboard**: aggregates several people's ledgers, trends, alerts on negative-net tasks |
| Handoff brief + `build-result` contract | **Pro skill pack**: curated brief templates and AGENTS.md profiles per stack (FastAPI, Next.js, data pipelines), tuned rule sets |
| Token ledger, `jevgb report`, local dashboard | **Setup and support**: install, tune rules on real logs, a one-off audit report |
| Skills for Grok Bot and Grok Build | **Sponsor perks**: priority issues, roadmap vote, logo in README |

Anyone may fork and sell the MIT core. The moat is trust, maintenance speed and honest measurement, not code secrecy.

## 4. Revenue options without a credit card

The options below were chosen to avoid any **credit card** requirement. Receiving money usually needs a **bank account and identity checks**, which is a different thing. Requirements change, so verify each signup page before relying on it.

| Option | Fees (source, accessed 2026-10-08) | Needs a credit card? | Notes / alternative |
| --- | --- | --- | --- |
| **GitHub Sponsors** | 0% on sponsorships from personal accounts; up to 6% from organization accounts ([GitHub Docs](https://docs.github.com/en/sponsors/sponsoring-open-source-contributors/about-sponsorships-fees-and-taxes)) | **No** for receiving. Needs bank + tax info, Stripe Connect identity check, 2FA, supported region ([GitHub Docs](https://docs.github.com/en/enterprise-cloud@latest/sponsors/receiving-sponsorships-through-github-sponsors/setting-up-github-sponsors-for-your-personal-account)) | **Best first step.** Can pay out via a fiscal host instead of your own bank. |
| **Open Collective** (Open Source Collective host) | 10% host fee plus processor fees ([OSC fees](https://docs.oscollective.org/welcome-and-introduction-to-osc/fees)). Open Collective Europe lists 6% ([OC docs](https://github.com/opencollective/documentation/blob/main/fiscal-hosts/fiscal-hosts.md)) | **No** for receiving. Payouts as expenses via PayPal or Wise ([example expense page](https://opencollective.com/opensource/expenses/340472)) | Transparent budget, good for companies that won't sponsor individuals. Check whether an EU host suits better. |
| **Paid setup / support** | none beyond bank costs | **No**: invoice and bank transfer | Needs a business registration for invoicing in NL (check KvK / Belastingdienst rules yourself). |
| **Pro skill pack** (digital download) | depends on platform | **Verify.** Merchant-of-record shops (Gumroad, Lemon Squeezy, Ko-fi shop) pay out to bank or PayPal, but signup terms vary | Alternative without a processor: sell via invoice, or make the pack a sponsor-tier perk on GitHub Sponsors (no extra processor). |
| **Hosted team dashboard** | processor + hosting | **Likely yes** somewhere: most cloud hosts ask for a card on file, and subscription billing needs a processor account | Postpone. Alternative: a **self-hosted team edition** sold as a license plus support via invoice. No hosting and no card. |
| **Ethical affiliate / referral links** | program-specific | Varies | Only for tools the project actually uses. Label every link as affiliate. Keep them out of the CLI and the local dashboard. Never imply an official xAI partnership. |

## 5. Traffic-to-income funnel

```text
discovery ──▶ README / landing ──▶ install + demo ──▶ real use (ledger) ──▶ trust ──▶ sponsor / buy pack / book setup
```

| Stage | Asset | Privacy-friendly tracking | No-card tool |
| --- | --- | --- | --- |
| Discovery | Posts showing a *real* `jevgb report` (with negatives), a demo GIF of the dashboard labeled "simulated" | count only landing visits | — |
| README | screenshot, 3-line quick start, Sponsor button (`.github/FUNDING.yml`) | GitHub's built-in repo traffic insights | GitHub (free) |
| Landing page | `site/index.html`, hero + how it works + measured savings + sponsor CTA | page and referrer counts, no cookies, no unique IDs | **GoatCounter** hosted is free for reasonable public use and doesn't track users with unique identifiers ([goatcounter.com](https://www.goatcounter.com/), accessed 2026-10-08). Host on **GitHub Pages** (free for public repos). |
| Docs | handoff contract, brand, this doc | same | GitHub Pages |
| Dashboard "powered by" link | footer link to the landing page with `?ref=dashboard` | the `ref` shows up as a path/referrer count on the landing page. **The dashboard itself sends nothing** and loads no remote resources. | — |
| Newsletter | monthly changelog + one real measurement | subscriber count only | **Buttondown** is free up to 100 subscribers ([pricing](https://buttondown.com/pricing?plan=free), accessed 2026-10-08). Verify whether signup asks for a card. |
| Conversion | GitHub Sponsors tiers, pack, setup booking via email | count clicks on sponsor CTA via `?ref=` on outbound links | GitHub Sponsors, Open Collective |

Rules: no telemetry in the CLI or the local dashboard, ever. Tracking happens only on the public landing page, and it is cookieless.

## 6. Revenue model (formula)

Monthly net revenue:

```
R = N_gh·A_gh·(1 − f_gh)
  + N_oc·A_oc·(1 − f_oc − p_oc)
  + N_pack·P_pack·(1 − f_mor)
  + H_setup·r_hour
  + N_team·P_team·(1 − f_proc)
  − C_fixed
```

with sponsor counts driven by the funnel: `N_gh + N_oc ≈ V · i · a · s`, where V = monthly unique visitors, i = install rate, a = share still active after a month, s = share of active users who sponsor.

**Illustrative example. Every value below is an invented assumption, chosen only to show the arithmetic. None of them is market data.**

| symbol | meaning | assumed value |
| --- | --- | --- |
| V | landing + repo unique visitors / month | 1,000 *(assumption)* |
| i | install rate | 5% *(assumption)* → 50 installs |
| a | active after a month | 40% *(assumption)* → 20 active |
| s | active users who sponsor | 25% *(assumption)* → 5 sponsors |
| N_gh, A_gh, f_gh | 4 sponsors × €5, fee 0% (personal accounts, per GitHub Docs) | €20 |
| N_oc, A_oc, f_oc, p_oc | 1 backer × €10, host 10% (OSC), processor 3% *(assumption)* | €8.70 |
| N_pack, P_pack, f_mor | 3 packs × €19, platform fee 10% *(assumption)* | €51.30 |
| H_setup, r_hour | 2 h × €60 *(assumption)* | €120 |
| N_team | hosted team edition not launched | €0 |
| C_fixed | GitHub Pages + GoatCounter + Buttondown free tiers | €0 |

R ≈ 20 + 8.70 + 51.30 + 120 + 0 − 0 = **€200 per month under these made-up assumptions.** Replace each value with your own measured numbers (GitHub traffic, GoatCounter, sponsor dashboard) after 30 days. The useful output is the *sensitivity*: in this example, setup hours dominate, so paid setup is the first lever to test.

## 7. Risks

- **Platform dependency (Grok Bot / Grok Build).** The integration relies on Grok Bot skills and on Grok Build reading `AGENTS.md` and offering headless `grok -p` ([docs.x.ai](https://docs.x.ai/build/overview), accessed 2026-10-08). Any change there can break the handoff. *Mitigation:* the brief is plain markdown that works pasted into any coding agent. Keep the contract tool-agnostic.
- **TypeSafe dependency.** Signups paused on 2026-09-22, reopened on 2026-09-27 without free credits for new accounts ([report](https://jevainews.com/news/typesafe-signups-paused/), updated 2026-10-06). *Mitigation:* the offline classifier is the default. Jev is optional.
- **Measurement misunderstood as a promise.** *Mitigation:* the "estimate" labels, basis quality, visible negatives, and SIMULATED banners on demo data.
- **Trademark ("GB" abbreviates Grok Bot).** The working name is **JevGB**. Dropping the full word "Grok" from the name, logo, package and command **lowers the risk but doesn't remove it**. "GB" is an abbreviation of Grok Bot, the README spells that out once, and the docs describe the product next to Grok Bot and Grok Build. A rights holder could still argue that the name trades on their brand, which could mean a complaint, a GitHub/PyPI name dispute, or a forced rename. It also limits any trademark claim of our own. *Mitigations:* a clear non-affiliation disclaimer (README, landing page footer, dashboard footer, this doc); no xAI logos, colors or fonts; no "official" wording; "Grok" used only descriptively (to say what it works with), never in the brand; a neutral domain if one is bought; a name-independent mark, so a rename only swaps the wordmark.
  - **Name checks**, done 2026-10-08:
    - **`jevgb`** (current): PyPI `/pypi/jevgb/json` → 404 (free); npm `registry.npmjs.org/jevgb` → 404 (free); GitHub repository-name search → 1 unrelated result (`qzqdz/jevgboost`, 0 stars); GitHub user search → 1 unrelated account (`jevgbur`). There was no obvious collision. `jgb` is taken on PyPI, so it is only a CLI alias, not a package name.
    - **Fallback names without any Grok reference:**
      - **Handbrief**: PyPI → 404; npm → 404; GitHub repository-name search → 0 results.
      - **Keelbrief**: PyPI → 404; npm → 404; GitHub repository-name search → 0 results.
    - (Also checked earlier: *Leanhand* had no hits. *Terso* and *Ledgerline* were taken on PyPI and npm. The previous working name `jevgrokbot` was free, but it contained the full word "Grok".)
    - These checks are not a trademark search. Run one (e.g. EUIPO/BOIP) before investing in a name.
- **Forks and competition.** MIT allows it. *Mitigation:* ship fast, publish honest measurements, keep the community.
- **Maintainer time and admin.** Invoicing and sponsorship income have tax implications. Check Dutch registration and tax rules before the first invoice.

## 8. 30 / 60 / 90 days

**Days 1–30: credible launch**
- Create the public repo (after the owner approves), with `FUNDING.yml` and topics, and publish `site/` on GitHub Pages with GoatCounter.
- Apply to GitHub Sponsors (bank route or fiscal host). Open an Open Collective page if companies ask.
- Run JevGB in **shadow mode** on your own Grok Bot work for two weeks. Publish the *real* `jevgb report`, negatives included.
- Record the demo GIF from the dashboard (labeled simulated) and post one write-up.

**Days 31–60: first income tests**
- Offer a fixed-scope "setup + log review" (invoice). Aim for 2 to 3 conversations, not volume.
- Draft the pro skill pack (3 stacks). Test it as a sponsor-tier perk before choosing a shop.
- Start the Buttondown newsletter (monthly). Add a `?ref=` to every outbound link and compare sources in GoatCounter.
- Improve the classifier using real misclassifications from shadow logs.

**Days 61–90: decide what to scale**
- Compare channels by sponsor clicks and setup requests. Drop the weakest.
- If teams ask, specify a **self-hosted team edition** (license + support via invoice) before considering hosting.
- Re-check the trademark risk. If there's any signal from xAI or a registry, rename to Handbrief or Keelbrief (prepared fallbacks).
- Publish a 90-day transparency note: users, income, costs, measured savings.
