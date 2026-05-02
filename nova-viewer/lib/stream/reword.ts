/**
 * Convert third-person LLM reasoning into first-person internal monologue.
 * Pass-through when the text already reads first-person. Conservative —
 * applies only well-known patterns; safe to leave unmatched text alone.
 */

interface Rule {
  pattern: RegExp;
  replace: string | ((match: string, ...groups: string[]) => string);
}

// Order matters — more specific patterns first.
const RULES: Rule[] = [
  // Third-person verb agreement: collapse "<subject> <verb>s" → "I <verb>"
  // when the subject is a Nova-referring noun/pronoun. Done first so that
  // the trailing "s" is stripped before bare-subject rewrites fire.
  {
    pattern: /\b(?:she|he|they|nova|the agent)\s+(\w+?)s\b/gi,
    replace: (_m, verb) => `I ${verb.toLowerCase()}`,
  },

  // Multi-word phrases that expand to single pronoun
  { pattern: /\bthe agent\b/gi, replace: (m) => (isCapital(m) ? "I" : "I") },
  { pattern: /\bnova\b/gi, replace: (m) => (isCapital(m) ? "I" : "I") },

  // Pronouns
  { pattern: /\bher\b/gi, replace: "my" },
  { pattern: /\bhis\b/gi, replace: "my" },
  { pattern: /\btheir\b/gi, replace: "my" },
  { pattern: /\bshe\b/gi, replace: "I" },
  { pattern: /\bhe\b/gi, replace: "I" },
  { pattern: /\bthey\b/gi, replace: "I" },
];

function isCapital(s: string): boolean {
  return s.length > 0 && s[0] === s[0].toUpperCase() && s[0] !== s[0].toLowerCase();
}

export function rewordFirstPerson(text: string): string {
  if (!text) return text;
  let out = text;
  for (const rule of RULES) {
    out = out.replace(rule.pattern, rule.replace as never);
  }
  return out;
}

const ELLIPSIS = "…";

export function truncate(text: string, max: number): string {
  if (text.length <= max) return text;
  // Reserve 1 char for the ellipsis.
  const cut = max - 1;
  const slice = text.slice(0, cut);
  // Try to break at the last space within the trailing window.
  const window = Math.min(12, cut);
  const tail = slice.slice(cut - window);
  const lastSpace = tail.lastIndexOf(" ");
  const breakAt = lastSpace >= 0 ? cut - window + lastSpace + 1 : cut;
  return slice.slice(0, breakAt) + ELLIPSIS;
}
