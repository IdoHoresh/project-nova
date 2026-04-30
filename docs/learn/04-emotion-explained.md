# 04 — Emotion Explained

> How Nova "feels" things, and why that's not as fluffy as it sounds.

## Important upfront caveat

Nova does **not** literally feel anything. She has no consciousness, no subjective experience, no inner life. When this doc says "Nova feels frustrated," it means **a software variable named `frustration` is currently high, and that variable is influencing her decisions in ways that resemble how frustration influences humans**.

This is called a **functional emotion** in the literature. Useful for engineering. Honest about what's actually happening.

With that out of the way:

## Why emotion in an AI agent matters

If Nova is just a VLM in a loop, she's interchangeable with thousands of other "AI plays game" demos. The emotion system is what makes her interesting:

1. **It produces visibly different play.** A high-anxiety Nova plays cautiously. A frustrated Nova plays impulsively. Same VLM, different behavior.
2. **It mirrors how real humans play.** Real players' moods shift over a session; their decisions change accordingly. Nova's emotion system is an attempt to model that.
3. **It makes the demo watchable.** Mood gauges, dopamine pulses, anxiety indicators — these are visual signals on the brain panel that make the AI's internal state legible to a viewer.

## The core variables

Nova's emotional state is a small vector of scalar variables. Each one has a defined range, an update rule, and an effect on her decisions:

| Variable | Range | What it represents |
| --- | --- | --- |
| `valence` | -1 to +1 | How "good" or "bad" Nova feels right now |
| `arousal` | 0 to 1 | How alert / tense / activated she is |
| `dopamine` | 0 to 1 | Recent reward signal (spikes on good moves, decays fast) |
| `frustration` | 0 to 1 | Accumulated negative outcomes |
| `anxiety` | 0 to 1 | Risk of imminent loss |
| `confidence` | 0 to 1 | Belief that current strategy is working |

Six numbers, total. Updated every move. Translated into natural language and injected into the VLM's prompt.

## The two-axis core: valence and arousal

The first two variables — `valence` and `arousal` — come from a model in psychology called **Russell's circumplex** (1980). It's a way of organizing emotional states on a 2D map:

```
                    HIGH AROUSAL
                         ↑
              angry     ●●●     excited
                       ●   ●
                      ●     ●
                     ●       ●
   NEGATIVE ←──────●           ●──────→ POSITIVE
   VALENCE        ●             ●        VALENCE
                   ●           ●
                    ●         ●
                     ●       ●
                       ●   ●
              sad      ●●●     calm
                         ↓
                    LOW AROUSAL
```

A high-valence/high-arousal state is "excited." High-valence/low-arousal is "calm." Low-valence/high-arousal is "anxious." Low-valence/low-arousal is "depressed."

For Nova, `valence` and `arousal` together describe the basic shape of her current mood. The other variables (dopamine, frustration, anxiety, confidence) are more specific signals layered on top.

## The dopamine signal

This is the most scientifically anchored part of the emotion system.

In real brains, dopamine is **not** a "happy chemical." It's a signal that responds to **prediction error** — the difference between what you expected and what actually happened. This was demonstrated by Wolfram Schultz, Peter Dayan, and Read Montague in 1997 in a famous paper that mathematically connected dopamine to a concept from machine learning called **temporal-difference learning**.

The equation is:

```
δ = (actual reward) − (expected reward)
```

If you expected a small win and got a big one, δ is positive — dopamine spikes — you "feel good." If you expected a win and got nothing, δ is negative — dopamine dips below baseline — you feel disappointed. If everything was as expected, δ is zero — dopamine stays at baseline — you feel nothing in particular.

Nova implements this directly:

```python
delta = actual_score_gain − expected_score_gain
```

`expected_score_gain` is computed by a small "value function" — either a hand-tuned heuristic that predicts how much the next move should earn, or a tiny machine-learning regressor trained on past games.

The resulting `delta` (called RPE — **reward prediction error**) drives:
- A positive spike in `dopamine` if `delta > 0`
- An increase in `frustration` if `delta < 0` (and a decrease if `delta > 0`)
- A small shift in `valence` and `confidence`

This is the most replicated finding in computational neuroscience over the past 25 years. It's the safest claim in the project.

### Worked example

Nova is mid-game. The board has two adjacent 8s and two adjacent 16s.

She swipes right.

Her value function predicted: "this swipe should yield about 24 points (the 8s and 16s won't all merge — only one pair will, plus a small bonus)."

What actually happened: both pairs merged in a chain reaction. Score went up by 56.

```
delta = 56 − 24 = +32 (normalized to about +0.4)
```

Big positive surprise. Dopamine spikes. `dopamine = 0.7`. Frustration drops. Valence ticks up. The brain panel shows a bright cyan pulse on the dopamine bar.

Now her next prompt includes: *"You feel a rush of satisfaction. The last move was much better than expected."* That phrasing influences how she reasons about the next move.

## Frustration

Where dopamine spikes on positive surprise, **frustration** accumulates on negative outcomes. Each time Nova makes a move with negative RPE, frustration ticks up. A streak of bad moves pushes it high.

When frustration is high, the prompt tells Nova: *"You feel impatient. You want to make a big play."* The VLM, reading this, becomes more likely to take risky high-payoff moves — exactly like a frustrated human gambler.

This is grounded in the **frustration-aggression literature** (Berkowitz 1989) and **frustrative non-reward** (Amsel 1992). High frustration biases toward riskier, more impulsive choices.

A satisfying merge resets frustration partially. Long-term frustration relief comes from reflection ("maybe I should change strategy").

## Anxiety

Where frustration is about the past (recent bad outcomes), **anxiety** is about the future (imminent risk).

Anxiety rises when:
- Empty cells drop below ~3 (game-over is close)
- A trauma-tagged memory is currently surfaced (Nova "recalls" a past loss on a similar board)
- Recent moves had high arousal but low valence (something stressful happening)

When anxiety is high, the prompt tells Nova: *"You feel nervous. The board is tight. You want to play safe."* The VLM responds by being more conservative.

Above a threshold (`anxiety > 0.6` plus other conditions), the system triggers **Tree-of-Thoughts deliberation** — Nova generates multiple candidate moves, evaluates each, and picks the best instead of doing a single fast call. This is the analog of Kahneman's **System 2** kicking in when the situation is hard.

The Yerkes-Dodson law (1908) is the loose inspiration: at moderate arousal/anxiety, performance is best. At very high anxiety, performance breaks down ("choking under pressure" — Beilock & Carr 2001). Honest caveat: the original Yerkes-Dodson study was on mice and has had mixed replications in humans, so we cite it as inspiration, not law.

## Confidence

`confidence` rises when Nova's recent moves match her predictions (small positive RPEs in a row). It falls when predictions are wrong (big surprises in either direction — both excitement and disappointment chip away at confidence because they signal the value function is poorly calibrated).

Effect: high confidence allows for bolder strategic play. Low confidence biases toward heuristic / "safe" moves.

## How the VLM "feels" the emotions

The VLM doesn't see numbers — it sees text. A small templating function turns the numeric vector into a sentence:

```
valence:     -0.3
arousal:     +0.7
dopamine:     0.2
frustration:  0.4
anxiety:      0.7
confidence:   0.4
```

becomes:

> *"You feel anxious. Your pulse is up. The last few moves disappointed you. You don't fully trust your current strategy."*

That sentence gets injected into the prompt sent to Claude. Claude, reading it, adjusts its reasoning — exactly like an actor reading stage directions.

This is the **appraisal step** from Croissant et al. (2024) Chain-of-Emotion: emotion is computed numerically, then verbalized into the prompt to influence the LLM's downstream output.

## Why this whole thing works

Researchers (Li et al. 2023, EmotionPrompt; EAI in NeurIPS 2024) have shown empirically that injecting emotional context into LLM prompts measurably changes the LLM's outputs. The mechanism is unclear — the LLM might be picking up on associations from training data ("anxious" prompts are followed by more cautious-sounding responses, etc.). Whatever the mechanism, the effect is real and consistent.

So Nova's emotional state isn't theatre. It actually shapes the moves she picks. Whether the LLM "experiences" the emotion is a separate philosophical question we don't need to settle — what matters for the project is that the architecture produces visibly different play under different emotional states.

## Summary

| Variable | Spikes on | Effect on play |
| --- | --- | --- |
| valence | Cumulative good outcomes | Good mood → broader thinking |
| arousal | Tight boards, recent surprises | Activated → faster reactions |
| dopamine | Better-than-expected merges | Positive reinforcement, mood lift |
| frustration | Streaks of bad moves | Impatient, risk-taking |
| anxiety | Game-over proximity, trauma | Conservative, may trigger ToT |
| confidence | Accurate predictions | Bolder strategic moves |

## Further reading

- **Schultz, Dayan & Montague (1997). A neural substrate of prediction and reward.** *Science.* The dopamine-as-RPE paper.
- **Russell (1980). A circumplex model of affect.** The valence-arousal map.
- **Croissant et al. (2024). An appraisal-based chain-of-emotion architecture for affective language model game agents.** *PLOS ONE.* The closest prior work.
- **Li et al. (2023). EmotionPrompt.** Empirical evidence that emotional context shifts LLM outputs.
- **Berkowitz (1989). Frustration-aggression hypothesis: examination and reformulation.** Frustration → risky choices.
- **Eysenck et al. (2007). Anxiety and cognitive performance: Attentional Control Theory.** Anxiety on cognition.
