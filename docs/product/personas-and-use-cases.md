# Personas & Use Cases: Project Nova

*Compiled May 2026. Industry statistics are date-stamped to source. Sample sizes (e.g. "n=400K+") are reported as the source reports them; methodology should be inspected at the linked source before quoting in external materials.*

Project Nova is an LLM-driven cognitive agent — persistent memory, simulated affect (valence/arousal/anxiety/frustration/dopamine/confidence), Tree-of-Thoughts deliberation under stress, and post-game reflection — that plays games end-to-end. The product wedge against `modl.ai`, Razer QA Co-AI, and the wider AI-QA category (see [`competitive-landscape.md`](./competitive-landscape.md)) is **cognitive/affective fidelity for player-experience simulation**, not bug-hunting. The two ingredients that make a sale are (1) personas the buyer recognises as their actual segment, and (2) use cases that map to a budget line a studio is already spending.

This document inventories both.

---

## Part A: Persona Library

### TL;DR

Studios already think in personas — UA managers segment by acquisition source and LTV, designers segment by skill curve, monetisation PMs segment by spend tier. The persona system in Nova has to (a) align with one of those existing mental models so the buyer doesn't have to learn a new vocabulary, and (b) be granular enough that running 10 personas through a level produces 10 visibly different reports — otherwise the buyer concludes the agent is monolithic and personas are window-dressing.

The library below is built from four established taxonomies plus F2P revenue segmentation: Bartle (1996, MUD ethnography); Yee's Daedalus Project (2006, MMO factor analysis); Quantic Foundry's Gamer Motivation Model (Yee & Ducheneaut, n>1.75M survey respondents); BrainHex (Nacke, Bateman & Mandryk, neurobiological mapping); HEXAD (Marczewski, gamification); and the whale/dolphin/minnow segmentation that drives ~70% of mobile revenue. Each persona maps directly onto Nova's `AffectVector` so the agent's internal state has a non-trivial starting point — a "Casual Carla" agent should *begin* a session with elevated anxiety and low confidence, not converge there organically over 30 minutes.

The 10 personas below are designed to (a) be visibly different in deliverables, and (b) cover the segments that drive studio business decisions.

### Theoretical foundation

| Source | Year | What it gives Nova |
|---|---|---|
| **Bartle** — Hearts/Clubs/Diamonds/Spades; Achievers/Explorers/Socializers/Killers ([Wikipedia](https://en.wikipedia.org/wiki/Bartle_taxonomy_of_player_types)) | 1996 | Coarse but legendary. Most game designers know the four-quadrant model — useful as a familiarity hook. Built from MUD1 ethnography 1978–1996. |
| **Yee, Daedalus Project** — Achievement / Social / Immersion + 10 subcomponents ([Yee 2006 PDF](http://nickyee.com/pubs/Yee%20-%20Motivations%20(2007).pdf)) | 2006 | Empirically showed Bartle's quadrants are not mutually exclusive (cross-correlations < 0.10). Justifies multi-motivation personas. |
| **Quantic Foundry — Gamer Motivation Model** ([quanticfoundry.com](https://quanticfoundry.com/gamer-motivation-model/), [reference chart PDF](https://quanticfoundry.com/wp-content/uploads/2019/04/Gamer-Motivation-Model-Reference.pdf)) | 2015–present | Six clusters (Action, Social, Mastery, Achievement, Immersion, Creativity), each with 2 sub-motivations → 12 dimensions. n>1.75M respondents. Closest thing to a peer-reviewed industry standard. |
| **BrainHex** — Seeker/Survivor/Daredevil/Mastermind/Conqueror/Socialiser/Achiever ([Nacke, Bateman, Mandryk 2014](https://www.sciencedirect.com/science/article/abs/pii/S1875952113000086), n>50K) | 2011/2014 | Maps archetypes to brain reward systems (amygdala fear, OFC strategy, hippocampal exploration). Justifies affect baselines on neurobiological grounds, not just behavioural. |
| **HEXAD** — Marczewski; Achiever/Player/Socializer/Free Spirit/Philanthropist/Disruptor ([gamified.uk](https://www.gamified.uk/user-types/), [Tondello et al. 2016 scale](https://hcigames.com/user-types-hexad/)) | 2015 | Adds Disruptor (rule-breaker, exploit-finder) — useful for QA persona. |
| **F2P spend segmentation** — Whales/Dolphins/Minnows | F2P era, ~2010+ | Whales ≈70% of revenue, ~85–90% of players spend ≤$1/mo ([Udonis](https://www.blog.udonis.co/mobile-marketing/mobile-games/mobile-games-whales)). Indispensable for mobile economy testing. |
| **Csikszentmihalyi flow** ([Jenova Chen MFA thesis](https://www.jenovachen.com/flowingames/Flow_in_games_final.pdf)) | 1975/2006 | Sets the boredom/anxiety boundaries personas can be tuned around. |
| **Prospect theory** — Kahneman & Tversky ([1979 paper](https://web.mit.edu/curhan/www/docs/Articles/15341_Readings/Behavioral_Decision_Theory/Kahneman_Tversky_1979_Prospect_theory.pdf)) | 1979 | Loss aversion (~2× gain weight) gives a quantitative knob for risk-tolerance per persona. |

**AffectVector convention.** Each persona below specifies six baseline values. `valence ∈ [-1,1]`, all others `∈ [0,1]`. These are *starting* states; Nova's affect model should drive them dynamically per-event. Numbers are designer judgement informed by the source taxonomies, not measured on real players — they are knobs to tune, not ground truth.

---

### Persona 1 — Casual Carla (the post-work unwinder)

- **Backstory.** 34, marketing manager, plays 15–25 minutes/day on the train home and in bed. Match-3 and idle-clicker history. Doesn't know the word "gacha." Has paid $4.99 once, two years ago, to remove ads.
- **Affect baseline.** valence=+0.2, arousal=0.3, anxiety=0.4, frustration=0.1, dopamine=0.4, confidence=0.3
- **Decision biases.** Loss-averse (won't risk a 3-star streak for a chance at 5). Heavy exploitation, near-zero exploration. Time-pressure intolerant — any animation > 4s triggers app-switch.
- **Memory profile.** Forgets game state between sessions. Re-reads tooltips. No genre fluency.
- **Trigger thresholds.** Quits if frustration > 0.5 for 2 consecutive events. Will not retry a failed level more than twice in one session. Will spend $0 unless a "first purchase 80% off" prompt appears at the right valence moment.
- **Primary motivation.** Quantic Foundry: low Mastery, low Action, moderate Completion, high Calm/Discovery. BrainHex: Seeker.
- **Underpinning research.** GameAnalytics 2025 benchmarks — bottom-quartile D1 retention 10–11.5%, median session ~5 min, [Mistplay benchmarks](https://business.mistplay.com/resources/mobile-game-retention-benchmarks). "If value isn't clear in the first 5–15 minutes, players churn" ([GameAnalytics 2025](https://www.gameanalytics.com/reports/2025-mobile-gaming-benchmarks)).

### Persona 2 — Whale Wei (the high-spender)

- **Backstory.** 41, finance, plays one mid-core gacha (think Genshin/AFK Arena clone). Has spent $14,000 over three years on his main account. Active in Discord. Brags about pulls. Treats the game as a hobby with a budget line.
- **Affect baseline.** valence=+0.5, arousal=0.6, anxiety=0.2, frustration=0.2, dopamine=0.7, confidence=0.8
- **Decision biases.** Risk-seeking on cosmetics (sunk-cost on collection completion). Risk-averse on PvP rank loss. Anchored on best-in-slot meta — will spend to skip 6h grinds.
- **Memory profile.** Encyclopaedic. Knows every banner, drop rate, and pity counter. Cross-references YouTube tier lists.
- **Trigger thresholds.** Will spend on any limited-time character that completes a faction. Churns hard if a balance patch invalidates a $500 build (see Diablo Immortal post-controversy player exodus despite [$500M y1 revenue](https://www.destructoid.com/diablo-immortal-revenue-500000-first-year-blizzard/)).
- **Primary motivation.** Quantic Foundry: high Achievement (Power, Completion), high Mastery (Strategy). HEXAD: Achiever + Player.
- **Underpinning research.** Whales = ~50–70% of F2P revenue ([Udonis](https://www.blog.udonis.co/mobile-marketing/mobile-games/mobile-games-whales), [Game Marketing Genie](https://gamemarketinggenie.com/blog/market-to-whales-dolphins-minnows/)). Pareto holds: top ~20% of payers > 80% of revenue.

### Persona 3 — Dolphin Diego (the budget-conscious enthusiast)

- **Backstory.** 28, software dev, plays the same gacha as Wei but spends $20–40/month on the monthly pass and one battle pass. Hate-watches whale streamers. F2P-adjacent identity.
- **Affect baseline.** valence=+0.3, arousal=0.5, anxiety=0.35, frustration=0.3, dopamine=0.5, confidence=0.6
- **Decision biases.** Highly loss-averse on currency (will hoard primogems for 6 months). Optimisation-minded. Reads patch notes.
- **Memory profile.** Strong genre fluency, moderate game-specific. Looks up guides.
- **Trigger thresholds.** Cancels monthly pass if value-per-dollar drops; will re-subscribe within 2 weeks if a desired character drops.
- **Primary motivation.** Mastery + Achievement, with strong Completion sub-motivation.
- **Underpinning research.** Dolphins ~10–15% of payers ([devtodev paying-audience segmentation](https://www.devtodev.com/resources/articles/4-simple-methods-of-paying-audience-segmentation)).

### Persona 4 — Minnow Maya (the never-spender)

- **Backstory.** 22, college student, downloads 3 games a week, deletes 2, plays 1 for a month. Will watch a 30-second rewarded ad every time. Total spend across all games ever: $0.
- **Affect baseline.** valence=+0.1, arousal=0.4, anxiety=0.25, frustration=0.2, dopamine=0.45, confidence=0.5
- **Decision biases.** Time-rich, money-poor — will always pick the grind over the purchase. Tolerant of friction if reward is visible. Highly social-proof driven (Discord, TikTok).
- **Memory profile.** Average. Plays many games so cross-genre patterns are strong.
- **Trigger thresholds.** Quits any game with hard paywall walls before level 30. Stays for 100+ levels if grind is fair. Refers friends if she finds a good deal-free game.
- **Primary motivation.** Action + Social + low-cost Achievement.
- **Underpinning research.** Minnows = ~85–90% of installs, <10% of revenue ([Udonis](https://www.blog.udonis.co/mobile-marketing/mobile-games/mobile-games-whales)). Median F2P→pay conversion ~2.18% ([businessofapps.com 2026](https://www.businessofapps.com/data/app-conversion-rates/)).

### Persona 5 — Hardcore Hiroshi (the achiever)

- **Backstory.** 31, plays 4–6h/day on weekends, holds top-100 leaderboard ranks across 3 competitive titles. Watches esports. Owns a 240Hz monitor.
- **Affect baseline.** valence=+0.4, arousal=0.7, anxiety=0.5, frustration=0.5, dopamine=0.6, confidence=0.85
- **Decision biases.** Risk-seeking when behind, risk-averse when ahead (classic prospect-theory inversion). Exploration high in early-game, exploitation high in late-game. Will tolerate enormous frustration for marginal mastery gains.
- **Memory profile.** Deep, structured. Maintains spreadsheets.
- **Trigger thresholds.** Will not quit hard content; will quit a game perceived as RNG-dependent or pay-to-win after ~3 sessions of unfair losses.
- **Primary motivation.** Mastery (Challenge + Strategy), Competition. BrainHex: Conqueror + Mastermind.
- **Underpinning research.** Yee 2006 — Achievement-primary players ~20% of MMO sample ([Yee 2006 PDF](http://nickyee.com/pubs/Yee%20-%20Motivations%20(2007).pdf)).

### Persona 6 — Explorer Elena (the world-wanderer)

- **Backstory.** 38, fiction author, plays open-world RPGs (BotW, RDR2, Outer Wilds). Will spend 2 hours on a side-quest she stumbled into.
- **Affect baseline.** valence=+0.6, arousal=0.4, anxiety=0.2, frustration=0.15, dopamine=0.55, confidence=0.6
- **Decision biases.** Curiosity-driven exploration always wins over efficiency. Low time pressure tolerance for combat that interrupts exploration. Will deliberately ignore UI hints.
- **Memory profile.** Excellent for spatial/world detail, weak for stats.
- **Trigger thresholds.** Quits when the world feels closed (loading screens, invisible walls, on-rails sequences). Tutorial-resistant — wants to be dropped in.
- **Primary motivation.** Immersion (Discovery + Fantasy), Creativity. Bartle: Explorer. BrainHex: Seeker.
- **Underpinning research.** Yee 2006 Immersion subcomponents (Discovery, Role-Playing, Customisation, Escapism) — ~20% primary-Immersion in MMO sample.

### Persona 7 — Social Sam (the friend-anchor player)

- **Backstory.** 26, sales, only plays games friends are playing. Will install Among Us, Helldivers 2, Marvel Rivals because the group chat said so. Drops them when the chat moves on.
- **Affect baseline.** valence=+0.5, arousal=0.5, anxiety=0.3, frustration=0.25, dopamine=0.5, confidence=0.55
- **Decision biases.** Conformity — picks classes/builds friends pick. Low solo-play retention; high party-play retention. Will spend on cosmetics if friends notice.
- **Memory profile.** Game state forgotten between groups. Social state (who plays what) very strong.
- **Trigger thresholds.** Quits when the friend group moves on, regardless of game quality. Will return to a "dead" game if one friend re-invites.
- **Primary motivation.** Social (Community, Competition-with-friends). HEXAD: Socializer + Philanthropist.
- **Underpinning research.** Bartle Socializer; HEXAD Socializer (one of the three most common HEXAD types per [Tondello et al.](https://hcigames.com/user-types-hexad/)).

### Persona 8 — Streamer Sienna (the audience-driven player)

- **Backstory.** 24, 8K Twitch followers, plays whatever's trending. Looks for entertaining-fail moments. Will play a bad game for content if her chat finds it funny.
- **Affect baseline.** valence=+0.4, arousal=0.7, anxiety=0.4, frustration=0.6, dopamine=0.7, confidence=0.7
- **Decision biases.** Performance-for-audience overrides optimal play. Will choose risky strategies for spectacle. Will rage on camera (entertainment value).
- **Memory profile.** Surface-level across many games; deep in 1–2 mains.
- **Trigger thresholds.** Drops a game when concurrent viewer count drops. Will revisit any game with a major patch.
- **Primary motivation.** Social (recognition), Action (excitement), Creativity (storytelling).
- **Underpinning research.** Adjacent to Yee Achievement-Competition + Social-Relationship axes; behaviour increasingly studied as "performative play."

### Persona 9 — Tutorial-Hater Tomás (the impatient veteran)

- **Backstory.** 36, played games his whole life, instinctively skips tutorial popups, opens every menu within 30 seconds, presses every button.
- **Affect baseline.** valence=+0.3, arousal=0.6, anxiety=0.2, frustration=0.4, dopamine=0.5, confidence=0.85
- **Decision biases.** Exploration-via-experimentation. Distrusts hand-holding. Will rage-quit a forced tutorial that locks his input.
- **Memory profile.** Excellent genre transfer. Treats new games as "another roguelike."
- **Trigger thresholds.** Quits if the tutorial is unskippable and >5 minutes. Stays if dropped into mechanics with light onboarding.
- **Primary motivation.** Mastery (Challenge), Strategy. HEXAD: Free Spirit.
- **Underpinning research.** Tutorial drop-off can hit 92.4% before the first episode in a poor FTUE ([case study via Henry Morgan-Dibie](https://medium.com/@KingHenryMorgansDiary/the-92-4-drop-how-i-used-data-and-ai-to-fix-a-mobile-games-catastrophic-churn-ee3fc17b6b01)); average tutorial completion lands ~30% on the low end ([GameAnalytics funnels](https://www.gameanalytics.com/blog/exploring-gaming-funnels)). Veteran-style impatience is a documented churn driver.

### Persona 10 — Disruptor Devi (the exploit-hunter)

- **Backstory.** 19, speedruns games on YouTube, files bug reports for fun, finds the duping glitch in week one.
- **Affect baseline.** valence=+0.4, arousal=0.6, anxiety=0.15, frustration=0.3, dopamine=0.65, confidence=0.9
- **Decision biases.** Anti-exploitation of intended path. Will deliberately try edge-case input combinations. Treats QA as gameplay.
- **Memory profile.** Strong on engine/physics quirks, weak on narrative.
- **Trigger thresholds.** Stays in any game that has exploitable systems; quits sandboxes that are too safe.
- **Primary motivation.** Mastery (Challenge), Creativity (Design). HEXAD: Disruptor.
- **Underpinning research.** HEXAD Disruptor — least common type per [Tondello et al.](https://hcigames.com/user-types-hexad/) but disproportionately important for QA persona simulation. Useful for finding economy exploits before whales do.

### Optional 11 & 12 (slot for studio-specific tuning)

- **Accessibility Anya** — partial colour-blindness (deuteranopia), uses one-handed controls. Affect baseline elevated anxiety on dexterity-heavy events. Underpinning: ~21% of US gamers report a disability ([AFB 2025 low-vision survey](https://afb.org/aw/spring2025/low-vision-game-survey)); ~640M gamers with disabilities globally (2023 estimate). Embodies the accessibility-validation use case directly.
- **Returning Rishi** — installed at launch 2 years ago, churned at level 47, came back after a major patch. Memory profile: stale. Critical persona for live-ops re-engagement testing.

---

## Part B: Use Case Catalogue

Each use case names: **the buyer (role + budget owner), the pain (with citation), the deliverable, and a value estimate**. Honest signal in italics — not all of these are equally hot.

### 1. Tutorial / FTUE validation

- **Pain.** D1 retention industry median ~26–28% for top-quartile games on iOS; bottom-quartile 10–11.5% ([GameAnalytics 2025](https://www.gameanalytics.com/reports/2025-mobile-gaming-benchmarks)). Tutorial drop-off can be the single biggest funnel cliff — one published case showed 92.4% drop before first episode complete. Median tutorial-end retention ≈ 30%. Loading screens >4s contribute disproportionately.
- **How Nova solves it.** Run 10 personas × 3 tutorial variants. Each persona's `frustration` trajectory + drop-out timestamp is logged. Output: per-variant churn curve broken down by persona, peak-frustration timestamp, tooltip skip rate, time-to-first-meaningful-action.
- **Deliverable excerpt.** *"Variant B reduces Tutorial-Hater Tomás's frustration peak from 0.71 → 0.42 (skip-tutorial path added). However, Casual Carla's confidence remains < 0.4 at level 3 in all three variants — recommend stronger early reward signal at minute 2."*
- **Buyer.** Lead Game Designer or UA Manager (D1 retention ties directly to LTV/CAC payback).
- **Value.** A 2-pp lift in D1 retention on a $1M/mo UA spend → roughly $200K+/yr in payback efficiency. Studios will pay for a tool that demonstrably moves D1 by 2pp.
- **Honest read.** *Strongest entry use case. Direct, measurable, recurring. Almost every mobile studio re-iterates tutorials quarterly.*

### 2. Economy balance + monetisation testing

- **Pain.** F2P→pay median conversion 2.18%; top games 3–5%; social casino 8%+ ([businessofapps.com](https://www.businessofapps.com/data/app-conversion-rates/)). Whales = 50–70% of revenue, so persona-level paywall sensitivity is what actually drives the P&L. Bad launches are catastrophic — Battlefront II loot-box backlash wiped $3.1B from EA's market cap ([screenrant](https://screenrant.com/star-wars-battlefront-2-ea-stock-prices-loot-boxes/)). Diablo Immortal earned $500M y1 but burned the brand and triggered renewed [EU antitrust scrutiny in 2026](https://www.ad-hoc-news.de/boerse/news/ueberblick/diablo-immortal-faces-renewed-antitrust-scrutiny-over-monetization-in-2026/68958970).
- **How Nova solves it.** Run 5 economy variants × persona mix (Whale Wei + Dolphin Diego + Minnow Maya + Disruptor Devi). For each: predicted ARPDAU, paywall churn rate per persona, exploit detection (Devi runs the duping glitch path), reflection lessons ("this offer felt manipulative" — Wei refused).
- **Deliverable.** Economy heatmap + per-persona spend curve + free-text reflection summary.
- **Buyer.** Monetisation PM or Live-Ops Lead.
- **Value.** A 0.5pp conversion lift on a $100M ARR mid-core game = $500K/yr. Avoidance of one Battlefront-style backlash = nine-figure category.
- **Honest read.** *Highest-leverage use case but hardest to sell — buyer requires high trust that synthetic personas predict real spend behaviour. Likely needs a calibrated case study before enterprise will buy.*

### 3. A/B test pre-screening (cheap variant culling)

- **Pain.** Firebase A/B tests need ≥1,000 users + 14-day minimum runtime ([Firebase docs](https://firebase.google.com/docs/ab-testing/ab-concepts)) for Remote Config experiments. To test 5 economy variants serially = 10–14 weeks. Worse: every variant exposes real users to a potentially worse experience.
- **How Nova solves it.** Run all 5 variants against a 100-persona panel overnight. Pick the top 2 to expose to the live A/B. Real test still needed, but the 3 worst variants never reach a real user.
- **Deliverable.** Ranked variant report with per-persona simulated KPI lift, variance bands, and "this variant has a 14% chance of being meaningfully worse than baseline — do not ship to live test."
- **Buyer.** Data Science Lead, Live-Ops PM.
- **Value.** Analyst time saved (1 ML engineer-quarter to run 5 sequential tests vs 1 week to run 1 winner) + opportunity cost of bad variants reaching real users.
- **Honest read.** *Strong second use case. Lower buyer trust requirement than #2 because Nova is augmenting, not replacing, the live A/B.*

### 4. Soft-launch substitute / synthetic soft-launch

- **Pain.** Mobile soft-launch lasts 3–6 months in Canada/Australia/Philippines, with CPIs of 5K–50K in tier-1 markets ([GameAnalytics soft-launch guide](https://www.gameanalytics.com/blog/soft-launch-guide), [Upptic](https://upptic.com/how-to-tech-test-your-game-in-soft-launch/)). Total soft-launch UA budget commonly $500K–$2M+. Outcome often inconclusive (small sample sizes, region-specific behaviour).
- **How Nova solves it.** "Synthetic soft-launch" — predict KPIs (D1, D7, ARPDAU, tutorial completion) per persona before any UA spend. Pair with a small real soft-launch for calibration.
- **Deliverable.** Predicted-KPI report with confidence intervals, persona-level breakdown, recommended fixes before live launch.
- **Buyer.** Studio Head, Production Director.
- **Value.** A studio that compresses a 4-month soft-launch to 2 months saves both calendar time and ~$500K UA. Of all uses, this has the highest dollar value per engagement.
- **Honest read.** *Headline use case for marketing, but buyer trust bar is highest. Needs a calibrated case study — "we predicted Royal Match D7 within 1.5pp of actual" — before an exec authorises skipping any soft-launch budget.*

### 5. Live-ops content validation

- **Pain.** Gacha titles (Genshin, Star Rail, ZZZ) ship a major event every ~3–6 weeks plus weekly content drops ([Adjust gacha guide](https://www.adjust.com/blog/gacha-mechanics-for-mobile-games-explained/)). QA cycle on a weekly event runs ~1–3 days; missing one event window is 1/52 of annual revenue.
- **How Nova solves it.** Overnight 100-persona run on this week's event → frustration peaks, time-to-completion per persona, exploit detection, predicted conversion lift.
- **Deliverable.** "By morning" report; CI/CD-style integration.
- **Buyer.** Live-Ops Lead.
- **Value.** One avoided "broken event" weekend on a top-50 mobile title = $1M+ in apology rewards, churn, and patch-cost.
- **Honest read.** *High-frequency use case = high recurring revenue. Best fit for live-service studios already running weekly content cycles.*

### 6. Difficulty curve / late-game-fun validation

- **Pain.** Difficulty tuning is the single hardest part of game design that doesn't show up in paid playtests — paid testers play the first 30 minutes, not level 47. DDA exists ([Hunicke & Chapman 2004 Hamlet](https://users.cs.northwestern.edu/~hunicke/pubs/Hamlet.pdf), [Zohaib 2018 review](https://onlinelibrary.wiley.com/doi/10.1155/2018/5681652)) but only adjusts within shipped content; it doesn't tell designers *whether* level 47 is fun for the kind of player who survived levels 1–46.
- **How Nova solves it.** Long-horizon persona runs — "play 50 levels as Casual Carla, log frustration trajectory, flag levels where flow band is breached." Memory + reflection let the agent remember earlier mechanics.
- **Deliverable.** Per-level flow chart per persona, frustration spike heatmap, recommended difficulty interventions.
- **Buyer.** Game Designer, especially on long-tail puzzle/RPG titles.
- **Value.** Hard to monetise as a standalone product but indispensable as a bundled feature.
- **Honest read.** *Differentiator vs modl.ai-style imitation-learned bots, which struggle with long-horizon persona consistency. Sell as a feature, not a SKU.*

### 7. Localisation + accessibility validation

- **Pain.** Game localisation costs $0.10–$0.18/word + $40–$80/h LQA ([Transphere 2026](https://www.transphere.com/game-localization-costs/)); narrative-heavy titles can hit $25K–$100K+ per language; AAA titles with 10+ languages cross 7 figures. ~640M gamers globally have a disability; ~21% of US gamers ([AFB 2025](https://afb.org/aw/spring2025/low-vision-game-survey)).
- **How Nova solves it.** Persona variants for colour-blindness, motor impairment (one-handed input restriction), text-reading speed, language fluency. Run them through onboarding + first paywall to flag failures.
- **Deliverable.** Per-locale and per-accessibility-profile completion rates, screenshots flagged with text-overflow / cultural-issue annotations.
- **Buyer.** Localisation Lead, Accessibility Specialist (where the role exists), increasingly the QA Director under regulatory pressure.
- **Value.** Catching one localised paywall string that mistranslates a price = direct refund avoidance. Capturing the 21% accessibility market = revenue upside.
- **Honest read.** *Underrated. Regulatory pressure (EU EAA 2025, US ADA case law) is making accessibility QA a budget line item it wasn't 3 years ago.*

### 8. Competitive analysis — running personas through a competitor's game

- **Pain.** Studios manually playtest competitors. Every UA Manager wants to know "where does Royal Match lose users at minute 7." No automated way to do this at scale.
- **How Nova solves it.** Studio uploads competitor APK; Nova runs 100 personas; report identifies friction points and monetisation patterns.
- **Deliverable.** Competitive teardown — funnel comparison vs studio's own game, by persona.
- **Buyer.** UA Lead, Studio Head.
- **Value.** Replaces ~$50K of consulting work (e.g. Naavik or GameRefinery deliverables) with a one-day automated run.
- **Honest read.** *Ethical/ToS gray zone (most games' ToS prohibit automated play). Pitch carefully. Likely a "shadow" use case studios use but don't talk about.*

### 9. UA creative-to-game alignment

- **Pain.** UA creatives (TikTok ads) often misrepresent gameplay to drive installs. Result: high CPI, terrible D1 because installed-user expectation ≠ real game.
- **How Nova solves it.** Run "creative-shaped persona" (the user who clicked *that* ad) through the first session and measure expectation-vs-reality gap.
- **Deliverable.** "This ad attracts Casual Carla; the first 90 seconds of the game require Hardcore Hiroshi skill. Expected D1 mismatch: -8pp."
- **Buyer.** UA Manager.
- **Value.** Direct CAC efficiency. Closes a known gap between marketing and game teams.
- **Honest read.** *Niche but specific. Could be a wedge into UA-team budgets, which are 10× larger than QA budgets.*

### 10. Pre-pitch / publisher-deck simulation

- **Pain.** Indies pitch publishers with "we think this will retain at 35% D1." Publishers don't believe them. Negotiating leverage = whoever has data.
- **How Nova solves it.** Indie runs Nova on a vertical slice; gets a defensible KPI prediction; brings it to the publisher pitch.
- **Deliverable.** "Nova-projected D1 / D7 / ARPDAU for vertical slice."
- **Buyer.** Indie devs, accelerators (e.g. Kowloon Nights, Raw Fury).
- **Value.** Low ACV but high volume; potentially a self-serve product tier.
- **Honest read.** *Best PLG / bottom-up wedge. Probably the path to a freemium tier.*

---

## Part C: Market Sizing

| Market | Size | Source |
|---|---|---|
| Global games market 2025 | $188.8B (some forecasts $197B) | [Newzoo 2025 free report](https://investgame.net/wp-content/uploads/2025/09/2025_Newzoo_Free_Global_Games_Market_Report.pdf), [PocketGamer.biz](https://www.pocketgamer.biz/newzoo-global-games-market-set-to-hit-1888bn-in-2025/) |
| Global games market 2026 forecast | ~$205B | Newzoo via [Outlook Respawn](https://respawn.outlookindia.com/gaming/gaming-news/global-games-market-set-for-189b-in-2025-newzoo-report) |
| Mobile gaming 2025 | $103–108B (~52–55% of total) | Newzoo 2025; [MAF 2026 stats](https://maf.ad/en/blog/mobile-gaming-statistics/) |
| Game QA outsourcing market 2025 | $2.5B; 15% CAGR | [openpr / statsndata](https://www.openpr.com/news/4437665/game-qa-testing-outsourcing-market-set-to-boom-rapidly) |
| Game QA services (broader) | $5B (2025) → $15B (2033) | statsndata; [growthmarketreports](https://growthmarketreports.com/report/game-qa-services-market) |
| Game QA services (narrower CAGR view) | $1.12B (2024) → $2.77B (2033) at 10.7% CAGR | growthmarketreports |
| Crowd-playtest spend (representative) | PlaytestCloud Pro Basic $1,175/mo, $69/token; Antidote flexible | [PlaytestCloud pricing](https://www.playtestcloud.com/pricing), [Antidote](https://antidote.gg/pricing/) |
| Soft-launch UA (typical) | $500K–$2M+; 3–6 mo duration; CPI 5K–50K tier-1 | [GameAnalytics soft-launch guide](https://www.gameanalytics.com/blog/soft-launch-guide), [Upptic](https://upptic.com/how-to-tech-test-your-game-in-soft-launch/) |
| AI-in-gaming VC investment (5y total) | $1.8B; 65% of deal value in content generation | [InvestGame](https://investgame.net/news/ai-s-ever-growing-presence-in-gaming-1-8b-in-vc-investments/) |
| Q3 2025 gaming startup funding | $1B total; >$230M into "gametech" (incl. automated QA) | [InvestGame digest](https://investgame.net/news/digest/51-2025/) |
| Gaming M&A 2025 | $161B record (EA $55B buyout, Netflix $82.7B WB) | [PocketGamer.biz](https://www.pocketgamer.biz/games-industry-manda-hit-a-record-161bn-in-2025/) |
| AI-focused gaming startups | First-round valuations 2.5× non-AI peers | InvestGame |
| Gamers with disabilities (global, 2023) | ~640M | [AFB 2025 / industry estimates](https://afb.org/aw/spring2025/low-vision-game-survey) |

**Bottom-up TAM sketch for synthetic playtesting.** If Nova captures even 10% of the $2.5B QA outsourcing market by 2028, that's $250M ARR — a category-leader outcome. More conservative SAM: focus only on top-200 mobile studios with live-ops products at $5K–$50K MRR each = $12M–$120M ARR ceiling on the live-ops use case alone (#5).

---

## Synthesis: which combinations open the biggest door

Best fit between Nova-as-it-stands today and what studios will actually pay for:

1. **Tutorial validation × Casual Carla / Tutorial-Hater Tomás / Hardcore Hiroshi panel.** Lowest buyer-trust bar (D1 retention is measurable in 24h, comparable to A/B baseline), fastest sale, recurring need (every quarterly update re-tunes onboarding), already a budget line. **This is the wedge.** It also produces the most concrete deliverable for marketing — "we improved D1 by 2pp" lands harder than any synthetic-soft-launch claim.
2. **Live-ops content validation × full persona panel.** Highest recurrence (weekly cycles), highest contract value via overnight runs becoming part of the ship train. Requires demonstrated reliability before adoption. Best 12-month-out target.
3. **A/B test pre-screening × economy variants.** Augments rather than replaces the existing process, so trust bar is moderate. Hits the data-science buyer who is already comfortable with statistical claims.

**Use cases to position but not lead with.**
- *Synthetic soft-launch* (#4): great marketing line, hardest sell. Use as a stretch ambition in the sales narrative; build credibility via #1 first.
- *Economy balance* (#2): biggest upside but biggest trust gap. Needs a flagship case study — likely one paid pilot with a tier-2 mobile studio willing to share calibration data.
- *Competitive teardowns* (#8): valuable but ToS-fragile.

**Three surprising findings worth highlighting in pitch decks.**

1. **The accessibility market is much larger than studios act on.** ~640M gamers with disabilities and ~21% of US gamers self-report a disability ([AFB 2025](https://afb.org/aw/spring2025/low-vision-game-survey)) — yet accessibility QA is still a discretionary line item in most studios. EU EAA 2025 enforcement is starting to change that. A persona-driven accessibility validation pipeline is a regulatory tailwind.
2. **Mobile retention has *deteriorated* into 2025.** GameAnalytics 2025 — top-quartile D1 26.5–27.7%, *worse* than 2023's 28–29%. Median D7 fell from 4–5% to 3.4–3.9% ([GameAnalytics 2025](https://www.gameanalytics.com/reports/2025-mobile-gaming-benchmarks)). The pain is getting worse, not better — so the willingness-to-pay for retention tooling is higher than 2023 baselines suggest.
3. **Whale concentration is more extreme than the textbook says.** "Top 1% of payers can drive >50% of revenue" is now the working assumption, and Pareto routinely understates it. ([Udonis](https://www.blog.udonis.co/mobile-marketing/mobile-games/mobile-games-whales), [devtodev](https://www.devtodev.com/resources/articles/4-simple-methods-of-paying-audience-segmentation)). Implication for Nova: even getting whale-persona behaviour 70% right is enough to be the most valuable persona in the library, because the variance it captures dwarfs every other segment combined.

---

## Sources

- [Bartle taxonomy — Wikipedia](https://en.wikipedia.org/wiki/Bartle_taxonomy_of_player_types)
- [Yee — Motivations for Play in Online Games (2006/2007)](http://nickyee.com/pubs/Yee%20-%20Motivations%20(2007).pdf)
- [Quantic Foundry — Gamer Motivation Model](https://quanticfoundry.com/gamer-motivation-model/) and [reference chart PDF](https://quanticfoundry.com/wp-content/uploads/2019/04/Gamer-Motivation-Model-Reference.pdf)
- [Nacke, Bateman & Mandryk — BrainHex (2014)](https://www.sciencedirect.com/science/article/abs/pii/S1875952113000086) and [HCI Games Group BrainHex](https://hcigames.com/user-types-hexad/)
- [Marczewski HEXAD framework](https://www.gamified.uk/user-types/) and [Tondello et al. HEXAD Scale](https://hcigames.com/user-types-hexad/)
- [Csikszentmihalyi Flow applied — Jenova Chen MFA Thesis](https://www.jenovachen.com/flowingames/Flow_in_games_final.pdf)
- [Kahneman & Tversky 1979 Prospect Theory](https://web.mit.edu/curhan/www/docs/Articles/15341_Readings/Behavioral_Decision_Theory/Kahneman_Tversky_1979_Prospect_theory.pdf)
- [Hunicke & Chapman — Hamlet DDA](https://users.cs.northwestern.edu/~hunicke/pubs/Hamlet.pdf); [Zohaib 2018 DDA review](https://onlinelibrary.wiley.com/doi/10.1155/2018/5681652)
- [GameAnalytics 2025 Mobile Gaming Benchmarks](https://www.gameanalytics.com/reports/2025-mobile-gaming-benchmarks); [GameAnalytics funnels guide](https://www.gameanalytics.com/blog/exploring-gaming-funnels); [GameAnalytics soft-launch guide](https://www.gameanalytics.com/blog/soft-launch-guide)
- [Mistplay retention benchmarks](https://business.mistplay.com/resources/mobile-game-retention-benchmarks); [MAF 2026 mobile gaming statistics](https://maf.ad/en/blog/mobile-gaming-statistics/)
- [Newzoo 2025 Free Global Games Market Report (PDF)](https://investgame.net/wp-content/uploads/2025/09/2025_Newzoo_Free_Global_Games_Market_Report.pdf); [PocketGamer.biz on Newzoo](https://www.pocketgamer.biz/newzoo-global-games-market-set-to-hit-1888bn-in-2025/)
- [Game QA outsourcing market — openpr/statsndata](https://www.openpr.com/news/4437665/game-qa-testing-outsourcing-market-set-to-boom-rapidly); [growthmarketreports Game QA Services](https://growthmarketreports.com/report/game-qa-services-market)
- [PlaytestCloud pricing](https://www.playtestcloud.com/pricing); [Antidote pricing](https://antidote.gg/pricing/)
- [Firebase A/B Testing concepts](https://firebase.google.com/docs/ab-testing/ab-concepts); [Phiture on Google Play Experiments](https://phiture.com/asostack/google-play-experiments-a-technical-deep-dive-into-the-new-updates/)
- [Udonis — what is a whale](https://www.blog.udonis.co/mobile-marketing/mobile-games/mobile-games-whales); [devtodev paying-audience segmentation](https://www.devtodev.com/resources/articles/4-simple-methods-of-paying-audience-segmentation); [Game Marketing Genie on whales](https://gamemarketinggenie.com/blog/market-to-whales-dolphins-minnows/)
- [Diablo Immortal $500M y1 — Destructoid](https://www.destructoid.com/diablo-immortal-revenue-500000-first-year-blizzard/); [Diablo Immortal antitrust 2026](https://www.ad-hoc-news.de/boerse/news/ueberblick/diablo-immortal-faces-renewed-antitrust-scrutiny-over-monetization-in-2026/68958970)
- [Battlefront II loot-box backlash $3.1B impact — Screenrant](https://screenrant.com/star-wars-battlefront-2-ea-stock-prices-loot-boxes/); [Variety coverage](https://variety.com/2017/digital/news/star-wars-video-game-controversy-microtransaction-loot-box-1202621913/)
- [F2P/freemium conversion rates — businessofapps 2026](https://www.businessofapps.com/data/app-conversion-rates/)
- [Adjust gacha mechanics guide](https://www.adjust.com/blog/gacha-mechanics-for-mobile-games-explained/); [HoYoverse engine teardown — Naavik](https://naavik.co/digest/zzz-hoyoverse-friendliest-gacha/)
- [Transphere — game localisation cost 2026](https://www.transphere.com/game-localization-costs/); [Transphere LQA guide](https://www.transphere.com/guide-to-game-localization-quality-assurance/)
- [AFB low-vision games survey 2025](https://afb.org/aw/spring2025/low-vision-game-survey); [Game Accessibility — Grokipedia](https://grokipedia.com/page/Game_accessibility)
- [InvestGame AI-in-gaming VC](https://investgame.net/news/ai-s-ever-growing-presence-in-gaming-1-8b-in-vc-investments/); [InvestGame Q3 2025 digest](https://investgame.net/news/digest/51-2025/); [PocketGamer.biz games M&A 2025](https://www.pocketgamer.biz/games-industry-manda-hit-a-record-161bn-in-2025/)
- [Henry Morgan-Dibie 92.4% drop case study](https://medium.com/@KingHenryMorgansDiary/the-92-4-drop-how-i-used-data-and-ai-to-fix-a-mobile-games-catastrophic-churn-ee3fc17b6b01)
- [Upptic — soft-launch tech testing](https://upptic.com/how-to-tech-test-your-game-in-soft-launch/)
