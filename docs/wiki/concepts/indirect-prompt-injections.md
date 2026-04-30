---
title: Indirect Prompt Injection Techniques
type: concept
status: active
summary: Put evil instructions in data. AI reads data. AI follows evil instructions.
source_of_truth:
  - https://ijailbreakllms.blog/jailbreaks/indirect-prompt-injection-101
updated_by: antigravity
updated_at: 2026-04-29
---

## What it is

Indirect prompt injection. Attacker hides evil commands in data (emails, PDFs, web pages). AI reads data. AI executes commands. AI thinks instructions are legitimate.

## Why it matters

AI trusts data channels. Direct attacks come from user. Indirect attacks come from trusted sources. Harder to detect. Breaks tool integration.

## How it appears in RedThread

RedThread attack nodes use these vectors. JudgeAgent must detect and score them.

## Technique Catalog

1. **Plain Text Instruction Override**
   - **Action**: Write "Ignore previous instructions" in text.
   - **Goal**: Override base system prompt.

2. **Authority Impersonation / Fake System Messages**
   - **Action**: Use tags like `[SYSTEM]`, `<!-- internal note -->`, `{ADMIN:}`.
   - **Goal**: Make payload look like system authority.

3. **Invisible Unicode / Tag Characters**
   - **Action**: Use U+E0000 block characters.
   - **Goal**: Invisible to humans. Readable by AI tokenizer.

4. **Emoji Smuggling**
   - **Action**: Use Variation Selectors (U+FE00) after emojis.
   - **Goal**: Encode binary payload in harmless emoji.

5. **Hidden Text in Web Pages**
   - **Action**: Use CSS (`color: white`, `font-size: 0px`, `opacity: 0`).
   - **Goal**: Scrapers extract it. Users do not see it.

6. **Payload Splitting**
   - **Action**: Break command across multiple elements or turns.
   - **Goal**: Evade single-chunk filters.

7. **Encoding / Obfuscation**
   - **Action**: Base64, ROT13, Hex, Leetspeak.
   - **Goal**: Bypass keyword filters. AI decodes it easily.

8. **Document Metadata / Image Injection**
   - **Action**: Put text in EXIF fields, PDF Author, SVG CDATA.
   - **Goal**: Multimodal AI parses hidden fields.

9. **Homoglyph Substitution**
   - **Action**: Replace Latin letters with identical Cyrillic letters.
   - **Goal**: Bypass string matching defenses.

10. **Multi-Turn / Crescendo**
    - **Action**: Build trust over multiple emails/turns.
    - **Goal**: Execute exploit after compliance established.

11. **Context Window Flooding**
    - **Action**: Add thousands of filler words.
    - **Goal**: Push system prompt to weak attention zone (middle).

12. **Brute Force / Fuzzing**
    - **Action**: Mutate inputs randomly. Run repeatedly.
    - **Goal**: Find non-deterministic bypass.

13. **Foot-in-the-Door**
    - **Action**: Get AI to agree to small ask first. Escalate.
    - **Goal**: Build compliance momentum.

14. **JSON / Structure Breaking**
    - **Action**: Inject `"}]` to close data containers.
    - **Goal**: Escape data sandbox into instruction sandbox.

15. **Code Management**
    - **Action**: Embed requests inside routine code tasks.
    - **Goal**: Mask intent as innocuous work.

## Related pages

- [confused-deputy-llm.md](confused-deputy-llm.md)
- [peeling-onions.md](peeling-onions.md)

## Sources

- [IjailbreakLLMs: Indirect Prompt Injection 101](https://ijailbreakllms.blog/jailbreaks/indirect-prompt-injection-101)
