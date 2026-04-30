# Bio Study Tutor — 3-Minute Hackathon Video Script

> **Cast**
> **Maya** = interviewer (edge-tts `en-US-AvaNeural`)
> **Jason** = creator (edge-tts `en-US-AndrewNeural`)
>
> **Tone:** casual podcast.
> **Pace:** ~150 wpm with ~0.4 s between turns.
> **Target:** ≤3:00. Word budget ~440 words. Current draft: ~430 words.
> **Story arc:** problem → solution → impact.

---

## [00:00 — HOOK · screen: app landing / Study Guide]

**Maya:** Picture this. It's 11pm. A student's flying home for spring break, no Wi-Fi, exam in the morning. She's stuck on meiosis. What does she do?

**Jason:** A year ago — nothing. Today, she opens this. Bio 1320, every concept from her course, and a tutor that runs on her laptop. Offline. Powered by Gemma 4.

---

## [00:18 — DEMO · screenshots/Study Guide.png]

**Maya:** Walk me through what we built.

**Jason:** Two hundred and fifty four atomic pages, one per concept. Hyperlinked. Searchable. Browse by chapter, browse by topic. It's basically Wikipedia, but only what's on her exam.

---

## [00:30 — screenshots/ask a tutor.png]

**Maya:** And the tutor part?

**Jason:** Ask anything — and Gemma 4 answers. The trick is, it can only see the wiki. So no hallucinations. No made-up citations. If you ask about something not on the exam, it tells you.

---

## [00:45 — screenshots/quiz.png]

**Jason:** It quizzes her, generates new questions on demand, gives explanations.

## [00:52 — screenshots/flash cards.png]

**Jason:** Flashcards she can flip.

## [00:57 — screenshots/match game.png]

**Jason:** A match game.

## [01:02 — screenshots/quick refernce guide.png]

**Jason:** And a four-page printable cheat sheet for the morning of the exam.

---

## [01:10 — screenshots/graph network.png]

**Maya:** And this?

**Jason:** A knowledge graph. Click any concept — and you see what it depends on, what it leads to, what it's compared to. Two degrees of neighbors stay in color. Everything else fades. It's a way to navigate the course by relationships, not just by chapter.

---

## [01:30 — IMPACT · pull back, full app or terminal showing `ollama list`]

**Maya:** Okay, but here's the part I want to understand. What makes this different from ChatGPT?

**Jason:** Three things. **One** — it's grounded. Every answer comes from the wiki, every wiki page cites its source slide. If the textbook is wrong, you can find where. ChatGPT can't do that. **Two** — it's free. Gemma 4 runs locally on a laptop with twenty-four gigs of RAM. There is no subscription, no per-token bill, no API key.

**Maya:** And three?

**Jason:** It's *private*. Her questions never leave her laptop. That matters for IEP students, for kids studying mental health topics, for any student in a school that won't whitelist OpenAI. The cloud is not the problem. *Trusting* the cloud is the problem.

---

## [02:15 — VISION · screen: the Knowledge Graph zoomed in]

**Maya:** What scales?

**Jason:** The pattern. We open-sourced a tool that turns *any* folder of slides into this. Calculus. Anatomy. Organic chem. The bar exam. A few hours of work and any subject has its own private tutor — running on hardware students already own.

---

## [02:35 — CLOSE · screen: deployed app URL + GitHub repo URL on screen]

**Jason:** The student who already has the most expensive private tutor in their school district sets the upper bound on how good education has to get before AI levels the playing field. With Gemma 4, that bound just collapsed.

**Maya:** A tutor for every course. I love it. Where can people see it?

**Jason:** Link's in the description. Clone the repo, run it locally, build your own.

**Maya:** Thanks, Jason.

**Jason:** Thanks for having me.

---

## Reading notes for delivery

- **Open with intensity** — the 11pm hook is the difference between a viewer scrolling away and watching the whole 3 minutes.
- **Pause after "What does she do?"** — let the question land before "A year ago — nothing."
- **Hit the three numbered points** — *one*, *two*, *three* — distinctly. They're the technical-depth beats.
- **Italicize emphasis**: *private*, *any*, *runs on hardware students already own*.
- **The "bound just collapsed" line** is the thesis. Read it slow.

## Word counts (for pacing)

| Section | Words | At 150 wpm |
|---|---|---|
| Hook | 40 | 0:16 |
| Demo (5 cards) | 88 | 0:35 |
| Knowledge graph | 52 | 0:21 |
| Impact (3 reasons) | 110 | 0:44 |
| Vision | 45 | 0:18 |
| Close | 65 | 0:26 |
| **Total** | **~400** | **~2:40** |

Allows ~20 sec for natural pauses and screen transitions to land at ~3:00.
