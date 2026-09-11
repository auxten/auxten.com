# auxten.com — Project Guide

## Deployment
- After any content/code change: auto commit & deploy via `wrangler pages deploy . --project-name=auxten-com`

## Blog Writing Style Guide

Inspired by satproto.org's approach — technical confidence with conversational honesty.

### Tone
- **Confident but self-aware.** State things directly. Don't hedge with "I think" or "it seems." But freely admit failures, limitations, and absurdities. Self-deprecation builds credibility.
- **Conversational, not casual.** Write like you're explaining to a smart friend over coffee — not a conference talk, not a Reddit post. Contractions are fine. Slang is not.
- **Honest about trade-offs.** Never oversell. If something doesn't scale, say so. If something is hacky, own it. Readers trust writers who acknowledge downsides.

### Sentence Structure
- **Short declarative sentences for key points.** "I decided to buy a Mac Mini." "It worked." One idea per sentence when it matters.
- **Longer sentences for context and backstory**, but keep them under ~30 words. If a sentence needs a semicolon and two commas, split it.
- **Vary rhythm.** Alternate short punchy lines with longer explanatory ones. Monotone sentence length puts people to sleep.

### Paragraphs
- **2-4 sentences max.** Dense walls of text kill engagement. Break aggressively.
- **One idea per paragraph.** If you're making a second point, start a new paragraph.
- **Lead with the point, then explain.** Don't build up to a conclusion — state it, then justify.

### Technical Explanation
- **Plain-language summary first, then details.** "Think of it as SQLite for big data" before diving into columnar storage internals.
- **Anchor new concepts to familiar ones.** Use "think of it as X but Y" comparisons. Readers understand new things through old things.
- **Show, don't lecture.** Concrete examples (code, numbers, screenshots) beat abstract description. "7 watts — less than an LED light bulb" is better than "very low power consumption."

### Structure
- **Chronological narrative with section breaks.** Each `##` heading is a chapter in a story, not a documentation section.
- **Headings should intrigue.** "Then Everything Broke" > "Infrastructure Challenges." "WhatsApp Was Terrible" > "Communication Issues."
- **Use `---` between major sections** to give readers visual breathing room.

### Voice & Personality
- **First person, active voice.** "I built" not "was built." "I tried" not "an attempt was made."
- **Inject humor through observation, not jokes.** "Imagine being in the other room and suddenly hearing your Mac Mini screaming an auto-play video at full volume." The humor comes from the situation, not from trying to be funny.
- **Bold key phrases** for scannability. Readers skim — make sure skimmers catch the important bits.
- **Rhetorical honesty.** If the results were modest, say so: "One of my accounts went from 0 to 35 followers. Better than nothing, right?"

### Things to Avoid
- Marketing speak ("revolutionary," "game-changing," "seamless")
- Unnecessary qualifiers ("very," "really," "quite," "somewhat")
- Passive constructions when active reads better
- Over-explaining things the audience already knows
- Emoji in prose (reserve for UI screenshots only)
