# Scientific & Academic Foundations: Project Nova

## TL;DR — what Nova draws on

Nova sits at the intersection of three established research traditions plus one piece of original engineering. From the **language-agent literature** (Voyager, Generative Agents, Reflexion, Tree of Thoughts, ReAct, CoALA) Nova inherits its skill-library and memory-augmented action loop, its valence-weighted reflection step, and its tree-search deliberation. From **classical cognitive architectures** (ACT-R, Soar, CLARION) it inherits the long-standing principle that intelligent behavior needs modular declarative + procedural memory plus a chunking/reflection process that compiles experience into reusable rules. From **affective science** (Russell's circumplex, Mehrabian's PAD, the OCC appraisal model, Picard's affective computing, Schultz's RPE account of dopamine) it inherits a continuous valence-arousal mood representation and an RPE-style dopamine signal that directly biases policy.

For studios, Nova's pitch lines up with the **player-modeling and automated-playtesting** literature (MDA, Csikszentmihalyi's flow channel, Bartle's taxonomy, Quantic Foundry's 12-motivation model, EA SEED's deep-RL game-testing work, the DDA literature), and with the recent **GUI-grounded agent benchmarks** (OSWorld, WebArena, Mind2Web, Cradle, SIMA, Anthropic computer use, Set-of-Mark prompting) that map the path from "Nova plays 2048" to "Nova plays any game a human can play."

The one piece without obvious direct precedent is **trauma tagging** — Nova explicitly marks catastrophic-loss episodes and gives them elevated retrieval weight. The closest scientific cousins are McGaugh's amygdala-driven emotional-memory consolidation, the avoidance-learning tradition, and prioritized experience replay in deep RL. We treat that combination as legitimizing lineage but flag the specific implementation (LLM-narrated, semantically retrievable trauma memories that bias future deliberation) as, as far as we can find, novel.

---

## 1. LLM-driven agent architecture

### Voyager (Wang et al., 2023) — the lifelong-learning skill-library template
- **Citation:** Wang, G., Xie, Y., Jiang, Y., Mandlekar, A., Xiao, C., Zhu, Y., Fan, L., Anandkumar, A. (2023). "Voyager: An Open-Ended Embodied Agent with Large Language Models." arXiv:2305.16291.
- **Method:** GPT-4 + automatic curriculum + ever-growing library of executable-code skills + iterative self-verification, in Minecraft. No fine-tuning.
- **What Nova borrows:** The skill-library-as-procedural-memory pattern and the in-context self-verification loop that Nova's reflection step descends from.
- **Source:** https://arxiv.org/abs/2305.16291

### Generative Agents (Park et al., 2023) — the memory + reflection architecture
- **Citation:** Park, J.S., O'Brien, J.C., Cai, C.J., Morris, M.R., Liang, P., Bernstein, M.S. (2023). "Generative Agents: Interactive Simulacra of Human Behavior." UIST '23. arXiv:2304.03442.
- **Method:** A memory stream of natural-language observations, weighted retrieval (recency + importance + relevance), a reflection step that synthesizes higher-level abstractions, and a planning module.
- **What Nova borrows:** The memory-stream + reflection + weighted-retrieval pattern is Nova's blueprint at the cognitive layer; post-game rule extraction is the same shape as Park et al.'s reflections, applied to game traces.
- **Source:** https://arxiv.org/abs/2304.03442

### CoALA (Sumers, Yao, Narasimhan, Griffiths, 2024) — the framework Nova fits in
- **Citation:** Sumers, T.R., Yao, S., Narasimhan, K., Griffiths, T.L. (2024). "Cognitive Architectures for Language Agents." TMLR. arXiv:2309.02427.
- **Method:** Descriptive framework organizing language agents around modular memory (working / episodic / semantic / procedural), a structured action space (internal vs. external), and a generalized decision loop. Explicitly bridges ACT-R/Soar and modern LLM agents.
- **What Nova borrows:** The *vocabulary*. Nova's components map cleanly onto CoALA's taxonomy — citing CoALA lets the pitch say "Nova is a CoALA-shaped agent."
- **Source:** https://arxiv.org/abs/2309.02427

### Reflexion (Shinn et al., 2023) — verbal reinforcement learning
- **Citation:** Shinn, N., Cassano, F., Berman, E., Gopinath, A., Narasimhan, K., Yao, S. (2023). "Reflexion: Language Agents with Verbal Reinforcement Learning." NeurIPS 2023. arXiv:2303.11366.
- **Method:** No weight updates — the agent verbally reflects on a trial's outcome and writes it into an episodic-memory buffer consumed by the next trial.
- **What Nova borrows:** Directly. Nova's post-game reflection that extracts semantic rules into the memory store is the Reflexion pattern with affect-coloring added.
- **Source:** https://arxiv.org/abs/2303.11366

### Tree of Thoughts (Yao et al., 2023) — the deliberation step
- **Citation:** Yao, S., Yu, D., Zhao, J., Shafran, I., Griffiths, T.L., Cao, Y., Narasimhan, K. (2023). "Tree of Thoughts: Deliberate Problem Solving with Large Language Models." NeurIPS 2023. arXiv:2305.10601.
- **Method:** Generalizes Chain-of-Thought to a tree of evaluated branches with self-evaluation, lookahead, and backtracking. Lifts GPT-4 on Game of 24 from ~4% to ~74%.
- **What Nova borrows:** Directly — "Tree-of-Thoughts deliberation" is a named Nova feature; each move generates and evaluates candidate plans rather than greedy-decoding.
- **Source:** https://arxiv.org/abs/2305.10601

### ReAct (Yao et al., 2022) — interleaved reasoning + acting
- **Citation:** Yao, S., Zhao, J., Yu, D., Du, N., Shafran, I., Narasimhan, K., Cao, Y. (2022). "ReAct: Synergizing Reasoning and Acting in Language Models." ICLR 2023. arXiv:2210.03629.
- **Method:** Interleaves reasoning traces with action tokens; reduces hallucination and improves interactive-decision benchmarks.
- **What Nova borrows:** The basic reason-then-act loop. Every Nova turn is in the ReAct lineage.
- **Source:** https://arxiv.org/abs/2210.03629

### SIMA (DeepMind, 2024) — generalist agent across commercial games
- **Citation:** SIMA Team, DeepMind (2024). "Scaling Instructable Agents Across Many Simulated Worlds." arXiv:2404.10179.
- **Method:** Single instructable agent trained on 9 commercial games (No Man's Sky, Teardown, etc.) using only pixels in and keyboard/mouse out. ~600 skills, transfer across games.
- **Relevance to Nova:** Canonical citation for "an LLM-style generalist that plays commercial games via the human interface." Underwrites Nova's "any game" generalization story.
- **Source:** https://arxiv.org/abs/2404.10179

### Cradle (Tan et al., BAAI, 2024) — General Computer Control
- **Citation:** Tan, W. et al. (2024). "Cradle: Empowering Foundation Agents Towards General Computer Control." arXiv:2403.03186.
- **Method:** Multimodal foundation model takes screenshots in, emits low-level mouse+keyboard out. Demonstrated on RDR2, Stardew Valley, Cities: Skylines, productivity apps.
- **Relevance to Nova:** Most direct prior art for a foundation-model agent operating arbitrary games via screen+input.
- **Source:** https://arxiv.org/abs/2403.03186

### Anthropic Computer Use (Anthropic, 2024) — frontier-lab validation
- **Citation:** Anthropic (October 2024). "Introducing computer use, a new Claude 3.5 Sonnet, and Claude 3.5 Haiku."
- **Method:** Claude 3.5 Sonnet exposes a public-beta API for screen-input + mouse/keyboard-output computer control.
- **Why it matters:** Frontier-vendor validation that computer-use agents are the next product surface.
- **Source:** https://www.anthropic.com/news/3-5-models-and-computer-use

### MemGPT / Letta (Packer et al., 2023) — long-term memory for LLMs
- **Citation:** Packer, C. et al. (2023). "MemGPT: Towards LLMs as Operating Systems." arXiv:2310.08560.
- **Method:** OS-style hierarchical memory tiers; the LLM pages information into/out of context via tool calls.
- **What Nova borrows:** The agent-managed-memory pattern. Nova's persistent-across-games memory store is in this tradition.
- **Source:** https://arxiv.org/abs/2310.08560

### A-MEM (Xu et al., 2025) — recent agentic memory work
- **Citation:** Xu, W. et al. (2025). "A-MEM: Agentic Memory for LLM Agents." NeurIPS 2025. arXiv:2502.12110.
- **Method:** Zettelkasten-inspired memory; each note auto-generates tags, keywords, and semantic links to existing notes.
- **What Nova borrows:** The latest evidence that structured agentic memory beats flat vector recall — same intuition behind Nova's typed entries and post-game semantic rules.
- **Source:** https://arxiv.org/abs/2502.12110

---

## 2. Classical cognitive architectures

### ACT-R (Anderson, Lebiere, CMU)
- **Citation:** Anderson, J.R., Bothell, D., Byrne, M.D., Douglass, S., Lebiere, C., Qin, Y. (2004). "An integrated theory of the mind." *Psychological Review*, 111(4), 1036-1060.
- **Concept Nova borrows:** The **declarative** (fact chunks with subsymbolic activation that decays and is reinforced by use) vs. **procedural** (IF-THEN production rules) split. Nova's typed-memory store and rule extraction map to declarative/procedural respectively; activation-by-recency-frequency-context informs Nova's retrieval weighting.
- **Source:** https://act-r.psy.cmu.edu/

### Soar (Newell, Laird, Rosenbloom)
- **Citations:** Laird, Newell, Rosenbloom (1987). "Soar: An architecture for general intelligence." *Artificial Intelligence*, 33(1), 1-64. Laird (2012). *The Soar Cognitive Architecture*, MIT Press.
- **Concept Nova borrows:** **Universal subgoaling** (spawn a subgoal when stuck) + **chunking** (compile the subgoal's lesson into a new production rule). Nova's "deliberate when uncertain, then write the lesson back as a rule" loop is contemporary subgoaling-plus-chunking with an LLM in place of Soar's symbolic engine.
- **Source:** https://arxiv.org/pdf/2205.03854 (Laird 2022 intro)

### CLARION (Sun)
- **Citation:** Sun, R. (2006). "The CLARION cognitive architecture." In *Cognition and Multi-Agent Interaction*.
- **Concept Nova borrows:** The **dual-process distinction** — implicit (fast, subsymbolic) vs. explicit (slow, symbolic) processes. Nova's snap heuristics vs. Tree-of-Thoughts deliberation = System 1 vs. System 2, which CLARION formalizes.
- **Source:** https://en.wikipedia.org/wiki/CLARION_(cognitive_architecture)

### Sigma (Rosenbloom)
- **Citation:** Rosenbloom, P.S., Demski, A., Ustun, V. (2016). "The Sigma cognitive architecture and system." *JAGI*, 7(1), 1-103.
- **Concept Nova borrows conceptually:** Functional-elegance bet — grand-unified cognition from a small set of primitives. Nova's small-module composition (LLM + memory + affect + deliberation) is in the same minimalist spirit.
- **Source:** https://arxiv.org/pdf/2101.02231

### OpenCog Hyperon (Goertzel et al.)
- **Citation:** Goertzel, B. et al. (2023). "OpenCog Hyperon: A Framework for AGI at the Human Level and Beyond." arXiv:2310.18318.
- **Concept Nova borrows conceptually:** The **cognitive-synergy** thesis — integrating heterogeneous modules outperforms any single one. Nova is a small applied instance.
- **Source:** https://arxiv.org/abs/2310.18318

---

## 3. Affect / emotion modeling

### Russell's Circumplex Model — Nova's MoodGauge is literally this
- **Citation:** Russell, J.A. (1980). "A circumplex model of affect." *Journal of Personality and Social Psychology*, 39(6), 1161-1178.
- **Concept:** Affect is a 2D continuous space — **valence** (pleasant ↔ unpleasant) × **arousal** (activation ↔ deactivation). Discrete emotion labels fall at expected angles on the circle.
- **How Nova uses it:** The MoodGauge directly renders valence × arousal. Frustration/anxiety = high-arousal-negative-valence; dopamine-spike confidence = high-arousal-positive-valence; calm = low-arousal-positive-valence. The most directly cite-able piece of psychology in Nova.
- **Source:** https://pdodds.w3.uvm.edu/research/papers/others/1980/russell1980a.pdf

### PAD Model (Mehrabian & Russell)
- **Citation:** Mehrabian, A. (1996). "Pleasure-arousal-dominance: A general framework for describing and measuring individual differences in temperament." *Current Psychology*, 14(4), 261-292.
- **Concept:** Three orthogonal dimensions — Pleasure, Arousal, **Dominance** (agency/control axis on top of valence-arousal).
- **Relevance to Nova:** Nova's "confidence" signal maps to dominance. Cite if pitching the affect model as 3D.
- **Source:** https://en.wikipedia.org/wiki/PAD_emotional_state_model

### OCC Model (Ortony, Clore, Collins)
- **Citation:** Ortony, A., Clore, G.L., Collins, A. (1988). *The Cognitive Structure of Emotions*. Cambridge University Press.
- **Concept:** Appraisal theory — 22 emotion types defined by the cognitive appraisal that produces them (events vs. agents vs. objects; pleased/displeased; approving/disapproving). Emotions arise from how an agent evaluates a situation against its goals.
- **Relevance to Nova:** Classical justification for *deriving* emotions from gameplay outcomes rather than asserting them. Nova's appraisal step (board state + outcome → affect change) sits in this tradition.
- **Source:** https://www.cambridge.org/core/books/cognitive-structure-of-emotions/87ED4D16E77B2DFF433F3400DB3C0D34

### Picard — Affective Computing (the field-founding text)
- **Citation:** Picard, R.W. (1997). *Affective Computing*. MIT Press.
- **Concept:** Founded the discipline. Genuine intelligence and natural HCI require machines that recognize, model, and (sometimes) express emotion.
- **Relevance to Nova:** Legitimacy citation for "we built an affect module into our agent." Nova is downstream of Picard's program.
- **Source:** https://mitpress.mit.edu/9780262661157/affective-computing/

### Schultz — Dopamine reward-prediction-error (RPE)
- **Citation:** Schultz, W., Dayan, P., Montague, P.R. (1997). "A neural substrate of prediction and reward." *Science*, 275(5306), 1593-1599.
- **Concept:** Dopamine neurons fire in proportion to (obtained reward − expected reward) — positive RPE when better than expected, no firing when as expected, depression when worse. The neural substrate of TD-learning.
- **How Nova uses it:** Nova's dopamine signal is a Schultz RPE — predicted vs. realized score-delta, residual drives an arousal/valence update. The most scientifically load-bearing single citation Nova has.
- **Source:** https://www.gatsby.ucl.ac.uk/~dayan/papers/sdm97.pdf

### Csikszentmihalyi — Flow
- **Citation:** Csikszentmihalyi, M. (1990). *Flow: The Psychology of Optimal Experience*. Harper & Row.
- **Concept:** Optimal engagement lives in the narrow channel between boredom (skill > challenge) and anxiety (challenge > skill). Requires clear goals, immediate feedback, matched difficulty.
- **Relevance to Nova:** The bridge from Nova-as-cognitive-agent to Nova-as-playtesting-product. Nova's reported anxiety/boredom curves proxy for where a human would fall out of flow.
- **Source:** https://en.wikipedia.org/wiki/Flow_(psychology)

---

## 4. Memory + reflection in LLMs

(Reflexion and Generative Agents are covered in Section 1; not duplicated here.)

### Self-Refine (Madaan et al., 2023)
- **Citation:** Madaan, A. et al. (2023). "Self-Refine: Iterative Refinement with Self-Feedback." NeurIPS 2023. arXiv:2303.17651.
- **Method:** A single LLM plays generator, critic, and refiner in a loop. ~20% absolute improvement across 7 tasks.
- **What Nova borrows:** The generator-critic-refiner pattern is a building block of Nova's deliberation step.
- **Source:** https://arxiv.org/abs/2303.17651

### Self-Consistency (Wang et al., 2022)
- **Citation:** Wang, X. et al. (2022). "Self-Consistency Improves Chain of Thought Reasoning in Language Models." ICLR 2023. arXiv:2203.11171.
- **Method:** Sample many reasoning traces, marginalize, take the most consistent answer.
- **What Nova borrows:** Justifies sampling multiple candidate moves rather than greedy-decoding the first thought.
- **Source:** https://arxiv.org/abs/2203.11171

### Tulving — episodic vs. semantic memory
- **Citations:** Tulving, E. (1972). "Episodic and semantic memory." In *Organization of Memory*, Academic Press. Tulving (1985). "Memory and consciousness." *Canadian Psychology*, 26(1), 1-12.
- **Concept:** Episodic memory (specific past experiences, autonoetic awareness) is functionally and neurally distinct from semantic memory (general knowledge, noetic awareness), though they interact.
- **How Nova uses it:** Nova stores game traces as episodic ("on game 47 I lost by merging too eagerly") and reflection-derived rules as semantic ("avoid early merges in upper-left quadrant"). Architecturally load-bearing and the cleanest cognitive-psychology citation Nova has.
- **Source:** https://psycnet.apa.org/record/1973-08477-007

---

## 5. Player modeling + game AI research

### MDA Framework (Hunicke, LeBlanc, Zubek, 2004)
- **Citation:** Hunicke, R., LeBlanc, M., Zubek, R. (2004). "MDA: A Formal Approach to Game Design and Game Research." AAAI Workshop on Challenges in Game AI.
- **Concept:** Mechanics → Dynamics → Aesthetics. Designers work mechanics-up; players experience aesthetics-down. Eight aesthetics: Sensation, Fantasy, Narrative, Challenge, Fellowship, Discovery, Expression, Submission.
- **Relevance to Nova:** Lingua franca of game-design research. Nova's value proposition lives at the dynamics layer and is measured against intended aesthetics.
- **Source:** https://users.cs.northwestern.edu/~hunicke/MDA.pdf

### Bartle — Player Taxonomy (1996)
- **Citation:** Bartle, R. (1996). "Hearts, clubs, diamonds, spades: Players who suit MUDs." *Journal of MUD Research*, 1(1).
- **Concept:** Four canonical player types — Achievers, Explorers, Socializers, Killers — on a 2D grid of acting-vs-interacting × players-vs-world.
- **Relevance to Nova:** Historical precedent for "playtesting AI must model multiple archetypes, not one." Nova's affect-conditioned policy variants are downstream cousins.
- **Source:** https://en.wikipedia.org/wiki/Bartle_taxonomy_of_player_types

### Yee — Quantic Foundry Gamer Motivation Model
- **Reference:** Yee, N. (2016+). The Gamer Motivation Profile. Quantic Foundry.
- **Concept:** 12-motivation factor-analytic model from 400,000+ surveys, grouped into 6 axes: Action, Social, Mastery, Achievement, Immersion, Creativity.
- **Relevance to Nova:** Empirically-validated successor to Bartle, with commercial credibility (200+ studios use it). Lets Nova target a six-axis motivation profile rather than generic engagement.
- **Source:** https://quanticfoundry.com/gamer-motivation-model/

### Augmenting Automated Game Testing with Deep RL (Bergdahl et al., EA SEED, 2020)
- **Citation:** Bergdahl, J., Gordillo, C., Tollmar, K., Gisslén, L. (2020). "Augmenting Automated Game Testing with Deep Reinforcement Learning." IEEE CoG. arXiv:2103.15819.
- **Method:** Deep-RL agents for FPS test coverage, exploit detection, difficulty mapping at EA.
- **Relevance to Nova:** Strongest industry citation that ML agents can do real game-QA work. Nova's pitch: "what EA SEED did with deep RL, we now do with an LLM cognitive agent that also models affect."
- **Source:** https://arxiv.org/abs/2103.15819

### Dynamic Difficulty Adjustment — Zohaib review (2018)
- **Citation:** Zohaib, M. (2018). "Dynamic Difficulty Adjustment (DDA) in Computer Games: A Review." *Advances in HCI*, 2018, 5681652.
- **Concept:** Surveys performance-, affect- (EEG/GSR/HRV), and hybrid DDA. Concludes DDA reliably affects flow/engagement with mixed effect sizes.
- **Relevance to Nova:** Nova reports anxiety/frustration internally — the same signals DDA systems try to read off the player physiologically. Nova can serve as a cheap *simulated player* for tuning DDA curves before human trials.
- **Source:** https://onlinelibrary.wiley.com/doi/10.1155/2018/5681652

### PCGML survey (Summerville et al., 2018)
- **Citation:** Summerville, A. et al. (2018). "Procedural Content Generation via Machine Learning (PCGML)." *IEEE Transactions on Games*, 10(3), 257-270. arXiv:1702.00539.
- **Concept:** Surveys ML-driven PCG for levels, maps, narratives, cards; names content critique/analysis as PCGML use cases.
- **Relevance to Nova:** Natural pairing — Nova plays content, PCGML generates content, two close the loop for synthetic playtesting at scale.
- **Source:** https://arxiv.org/abs/1702.00539

---

## 6. Computer-use / GUI-grounded agents (the generalization roadmap)

### OSWorld (Xie et al., NeurIPS 2024)
- **Citation:** Xie, T., Zhang, D., Chen, J. et al. (2024). "OSWorld: Benchmarking Multimodal Agents for Open-Ended Tasks in Real Computer Environments." NeurIPS 2024. arXiv:2404.07972.
- **Method:** 369 tasks across Ubuntu/Windows/macOS in real apps. Humans 72%, best frontier model 12%.
- **Relevance to Nova:** The headline benchmark for "how good are computer-use agents really" — the gap is the opportunity Nova's roadmap targets.
- **Source:** https://arxiv.org/abs/2404.07972

### WebArena (Zhou et al., 2023)
- **Citation:** Zhou, S. et al. (2023). "WebArena: A Realistic Web Environment for Building Autonomous Agents." arXiv:2307.13854.
- **Method:** 812 long-horizon tasks across e-commerce, forums, Gitea, and CMS sites.
- **Source:** https://arxiv.org/abs/2307.13854

### Mind2Web (Deng et al., 2023)
- **Citation:** Deng, X. et al. (2023). "Mind2Web: Towards a Generalist Agent for the Web." NeurIPS 2023.
- **Method:** 2,000+ open-ended web tasks across 137 sites in 31 domains.
- **Source:** https://github.com/OSU-NLP-Group/Mind2Web

### Set-of-Mark Prompting (Yang et al., 2023)
- **Citation:** Yang, J., Zhang, H., Li, F., Zou, X., Li, C., Gao, J. (2023). "Set-of-Mark Prompting Unleashes Extraordinary Visual Grounding in GPT-4V." arXiv:2310.11441.
- **Method:** Use SAM/SEEM to segment a screenshot, overlay numbered marks on each region, then ask the LMM to "click region 7." Lifts visual grounding into LMM range.
- **Relevance to Nova:** When Nova generalizes from 2048's structured API to arbitrary game GUIs, SoM is the canonical screen-grounding technique to cite.
- **Source:** https://arxiv.org/abs/2310.11441

### AppAgent / Mobile-Agent / AndroidWorld
- **AppAgent reference:** Zhang, C. et al. (2023). "AppAgent: Multimodal Agents as Smartphone Users." (Tencent QQGYLab) https://github.com/TencentQQGYLab/AppAgent
- **AndroidWorld reference:** Rawles, C. et al. (2024). "AndroidWorld: A Dynamic Benchmarking Environment for Autonomous Agents."
- **Relevance to Nova:** The mobile equivalents — important if Nova ever pivots to mobile-game playtesting, which is a much larger market than desktop.

(Cradle, SIMA, Anthropic computer use are covered in Section 1.)

---

## 7. Aversive memory / trauma (the unusual one)

This is the area where Nova's design is most original. The cleanest scientific lineage we can construct:

### Schultz dopamine RPE (already cited in Section 3)
- Negative RPE is the neural substrate of "things were worse than I expected." Trauma in Nova is a strongly-negative-RPE event with downstream memory consequences. This is the bottom layer.

### McGaugh — amygdala-modulated emotional memory consolidation
- **Citation:** McGaugh, J.L. (2004). "The amygdala modulates the consolidation of memories of emotionally arousing experiences." *Annual Review of Neuroscience*, 27, 1-28.
- **Concept:** Emotionally arousing experiences are preferentially consolidated into long-term memory via amygdala-driven stress-hormone and noradrenergic modulation. Adaptive: surviving and remembering aversive events.
- **Relevance to Nova:** Neuroscience justification for the trauma-tagging mechanism. "Catastrophic-loss memories should have elevated retrieval weight" is exactly what McGaugh's literature predicts a brain would do.
- **Source:** https://pubmed.ncbi.nlm.nih.gov/15217324/

### Avoidance learning (two-factor theory and successors)
- **Reference:** Krypotos, A.-M., Effting, M., Kindt, M., Beckers, T. (2015). "Avoidance learning: a review of theoretical models and recent developments." *Frontiers in Behavioral Neuroscience*, 9, 189.
- **Concept:** Aversive Pavlovian conditioning produces defensive responses; instrumental avoidance learning then develops flexible policies that prevent re-encounter.
- **Relevance to Nova:** Nova's trauma-tag-then-avoid loop is behaviorally an avoidance-learning mechanism on top of an LLM substrate.
- **Source:** https://www.frontiersin.org/articles/10.3389/fnbeh.2015.00189/full

### Prioritized Experience Replay (Schaul et al., 2015)
- **Citation:** Schaul, T., Quan, J., Antonoglou, I., Silver, D. (2015). "Prioritized Experience Replay." ICLR 2016. arXiv:1511.05952.
- **Method:** Sample replay transitions in proportion to TD-error magnitude rather than uniformly. SOTA on 41/49 Atari games at the time.
- **Relevance to Nova:** Clearest computational precedent for "high-surprise events deserve disproportionate retrieval weight." Nova's trauma weighting is conceptually prioritized replay over LLM-narrated episodic memories instead of (s,a,r,s') tuples.
- **Source:** https://arxiv.org/abs/1511.05952

### Honest gap statement
We could not find a paper that does *all of*: (a) LLM-driven agent, (b) episodic memory store, (c) explicit semantic tagging of aversive episodes, (d) elevated retrieval weight at deliberation time conditioned on that tag, (e) tag narrated in natural language by the agent itself. Recent fear-conditioning-inspired RL exists (e.g., "Avoiding Death through Fear Intrinsic Conditioning," arXiv:2506.05529) but lives in pixel-RL, not language-agent territory. Nova's trauma-tagging should be presented as **novel, grounded in prioritized replay (RL) + amygdala emotional consolidation (neuroscience) + avoidance learning (behavioral psychology).** Honest and defensible.

---

## Synthesis: Nova's intellectual position

Nova is a **CoALA-shaped language agent** in the **Voyager / Generative Agents / Reflexion lineage** — in-context skill libraries and verbal reflection rather than gradient updates. Its deliberation step is **Tree of Thoughts**, its action loop is **ReAct**, its post-game rule extraction is **Reflexion**.

On top of that skeleton sits an **affect module rooted in Russell's valence-arousal circumplex**, with mood updates driven by a **Schultz-style dopamine RPE**, appraisal logic in the **OCC tradition**, and a confidence axis from **PAD**. Most LLM-agent papers omit affect or treat it as decoration; Nova treats it as a first-class policy-biasing signal. Picard (1997) is the field-level legitimacy.

Below the affect module is an **episodic + semantic memory split in the Tulving tradition**, implemented in the **MemGPT / A-MEM agentic-memory style**, with a **trauma-tagging mechanism** that conceptually draws on **McGaugh's amygdala-driven emotional consolidation**, **avoidance learning**, and **prioritized experience replay** — though the specific implementation appears original.

For studios, the value proposition is grounded in **MDA**, **Csikszentmihalyi's flow channel**, **Bartle / Yee** player modeling, and the deep-RL playtesting line opened by **EA SEED**. The "any game" roadmap is mapped by **OSWorld**, **WebArena**, **Cradle**, **SIMA**, and **Anthropic computer use**, with **Set-of-Mark** as the workhorse screen-grounding technique.

In one sentence: **Nova is what you get when you take a CoALA-style LLM agent, install Russell + Schultz as the affect substrate, install Tulving + Reflexion as the memory substrate, add a McGaugh-inspired trauma-tagging layer that's novel, and aim the whole thing at the playtesting use cases EA SEED, MDA, and Quantic Foundry have already legitimized.**

---

## Citations bibliography

### LLM agents
1. Wang, G. et al. (2023). "Voyager: An Open-Ended Embodied Agent with Large Language Models." arXiv:2305.16291. https://arxiv.org/abs/2305.16291
2. Park, J.S. et al. (2023). "Generative Agents: Interactive Simulacra of Human Behavior." UIST '23. arXiv:2304.03442. https://arxiv.org/abs/2304.03442
3. Sumers, T.R., Yao, S., Narasimhan, K., Griffiths, T.L. (2024). "Cognitive Architectures for Language Agents." TMLR. arXiv:2309.02427. https://arxiv.org/abs/2309.02427
4. Shinn, N. et al. (2023). "Reflexion: Language Agents with Verbal Reinforcement Learning." NeurIPS 2023. arXiv:2303.11366. https://arxiv.org/abs/2303.11366
5. Yao, S. et al. (2023). "Tree of Thoughts: Deliberate Problem Solving with Large Language Models." NeurIPS 2023. arXiv:2305.10601. https://arxiv.org/abs/2305.10601
6. Yao, S. et al. (2022). "ReAct: Synergizing Reasoning and Acting in Language Models." ICLR 2023. arXiv:2210.03629. https://arxiv.org/abs/2210.03629
7. SIMA Team, DeepMind (2024). "Scaling Instructable Agents Across Many Simulated Worlds." arXiv:2404.10179. https://arxiv.org/abs/2404.10179
8. Tan, W. et al. (2024). "Cradle: Empowering Foundation Agents Towards General Computer Control." arXiv:2403.03186. https://arxiv.org/abs/2403.03186
9. Anthropic (October 2024). "Introducing computer use, a new Claude 3.5 Sonnet, and Claude 3.5 Haiku." https://www.anthropic.com/news/3-5-models-and-computer-use
10. Packer, C. et al. (2023). "MemGPT: Towards LLMs as Operating Systems." arXiv:2310.08560. https://arxiv.org/abs/2310.08560
11. Xu, W. et al. (2025). "A-MEM: Agentic Memory for LLM Agents." NeurIPS 2025. arXiv:2502.12110. https://arxiv.org/abs/2502.12110
12. Madaan, A. et al. (2023). "Self-Refine: Iterative Refinement with Self-Feedback." NeurIPS 2023. arXiv:2303.17651. https://arxiv.org/abs/2303.17651
13. Wang, X. et al. (2022). "Self-Consistency Improves Chain of Thought Reasoning in Language Models." ICLR 2023. arXiv:2203.11171. https://arxiv.org/abs/2203.11171

### Cognitive architectures
14. Anderson, J.R. et al. (2004). "An integrated theory of the mind." *Psychological Review*, 111(4), 1036-1060.
15. Laird, J.E., Newell, A., Rosenbloom, P.S. (1987). "Soar: An architecture for general intelligence." *Artificial Intelligence*, 33(1), 1-64. [See also Laird (2022) intro: arXiv:2205.03854.]
16. Sun, R. (2006). "The CLARION cognitive architecture: Extending cognitive modeling to social simulation." In *Cognition and Multi-Agent Interaction*, Cambridge University Press.
17. Rosenbloom, P.S., Demski, A., Ustun, V. (2016). "The Sigma cognitive architecture and system." *Journal of Artificial General Intelligence*, 7(1), 1-103.
18. Goertzel, B. et al. (2023). "OpenCog Hyperon: A Framework for AGI at the Human Level and Beyond." arXiv:2310.18318. https://arxiv.org/abs/2310.18318

### Affect / emotion
19. Russell, J.A. (1980). "A circumplex model of affect." *Journal of Personality and Social Psychology*, 39(6), 1161-1178.
20. Mehrabian, A. (1996). "Pleasure-arousal-dominance: A general framework for describing and measuring individual differences in temperament." *Current Psychology*, 14(4), 261-292.
21. Ortony, A., Clore, G.L., Collins, A. (1988). *The Cognitive Structure of Emotions*. Cambridge University Press.
22. Picard, R.W. (1997). *Affective Computing*. MIT Press.
23. Schultz, W., Dayan, P., Montague, P.R. (1997). "A neural substrate of prediction and reward." *Science*, 275(5306), 1593-1599.
24. Csikszentmihalyi, M. (1990). *Flow: The Psychology of Optimal Experience*. Harper & Row.

### Memory (cognitive psychology)
25. Tulving, E. (1972). "Episodic and semantic memory." In *Organization of Memory*, Academic Press.
26. Tulving, E. (1985). "Memory and consciousness." *Canadian Psychology*, 26(1), 1-12.

### Player modeling + game AI
27. Hunicke, R., LeBlanc, M., Zubek, R. (2004). "MDA: A Formal Approach to Game Design and Game Research." AAAI Workshop.
28. Bartle, R. (1996). "Hearts, clubs, diamonds, spades: Players who suit MUDs." *Journal of MUD Research*, 1(1).
29. Yee, N. (2016+). The Quantic Foundry Gamer Motivation Model. https://quanticfoundry.com/gamer-motivation-model/
30. Bergdahl, J., Gordillo, C., Tollmar, K., Gisslén, L. (2020). "Augmenting Automated Game Testing with Deep Reinforcement Learning." IEEE CoG. arXiv:2103.15819. https://arxiv.org/abs/2103.15819
31. Zohaib, M. (2018). "Dynamic Difficulty Adjustment (DDA) in Computer Games: A Review." *Advances in Human-Computer Interaction*, 2018, 5681652.
32. Summerville, A. et al. (2018). "Procedural Content Generation via Machine Learning (PCGML)." *IEEE Transactions on Games*, 10(3), 257-270. arXiv:1702.00539. https://arxiv.org/abs/1702.00539

### Computer-use agents
33. Xie, T. et al. (2024). "OSWorld: Benchmarking Multimodal Agents for Open-Ended Tasks in Real Computer Environments." NeurIPS 2024. arXiv:2404.07972. https://arxiv.org/abs/2404.07972
34. Zhou, S. et al. (2023). "WebArena: A Realistic Web Environment for Building Autonomous Agents." arXiv:2307.13854. https://arxiv.org/abs/2307.13854
35. Deng, X. et al. (2023). "Mind2Web: Towards a Generalist Agent for the Web." NeurIPS 2023.
36. Yang, J. et al. (2023). "Set-of-Mark Prompting Unleashes Extraordinary Visual Grounding in GPT-4V." arXiv:2310.11441. https://arxiv.org/abs/2310.11441
37. Zhang, C. et al. (2023). "AppAgent: Multimodal Agents as Smartphone Users." https://github.com/TencentQQGYLab/AppAgent
38. Rawles, C. et al. (2024). "AndroidWorld: A Dynamic Benchmarking Environment for Autonomous Agents."

### Aversive memory / trauma lineage
39. McGaugh, J.L. (2004). "The amygdala modulates the consolidation of memories of emotionally arousing experiences." *Annual Review of Neuroscience*, 27, 1-28.
40. Krypotos, A.-M., Effting, M., Kindt, M., Beckers, T. (2015). "Avoidance learning: a review of theoretical models and recent developments." *Frontiers in Behavioral Neuroscience*, 9, 189.
41. Schaul, T., Quan, J., Antonoglou, I., Silver, D. (2015). "Prioritized Experience Replay." ICLR 2016. arXiv:1511.05952. https://arxiv.org/abs/1511.05952
