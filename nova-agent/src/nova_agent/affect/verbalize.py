from nova_agent.affect.types import AffectVector


def describe(v: AffectVector) -> str:
    """Translate an affect vector into a one-sentence stage direction.

    Used as a string fragment in the VLM prompt.
    """
    parts: list[str] = []

    if v.anxiety > 0.6:
        parts.append("You feel anxious.")
    elif v.frustration > 0.5:
        parts.append("You feel frustrated and impatient.")
    elif v.valence > 0.4 and v.arousal > 0.4:
        parts.append("You feel satisfied — recent moves are paying off.")
    elif v.valence > 0.3:
        parts.append("You feel calm and cautiously optimistic.")
    elif v.valence < -0.3:
        parts.append("You feel discouraged.")
    else:
        parts.append("You feel calm and focused.")

    if v.dopamine > 0.4:
        parts.append("The last move felt better than expected.")
    elif v.dopamine < 0.05 and v.frustration > 0.3:
        parts.append("Recent moves have been disappointing.")

    if v.arousal > 0.7:
        parts.append("Your pulse is up; the board is tight.")

    if v.confidence < 0.3:
        parts.append("You don't fully trust your current strategy.")
    elif v.confidence > 0.7:
        parts.append("You're confident in your read of the board.")

    return " ".join(parts)
