# How to use Hippo

## Basic rule

Open Claude (or Codex) with this vault as the project. Begin a fresh task with "Start Hippo" so it reads [[Contract]], [[Profile]], and [[State]] and searches relevant notes. Then describe the result you want in ordinary language. Durable results are saved to the vault; casual conversation stays in the chat.

## After a lecture

New Moodle files arrive in the module's `Materials/` folder by themselves (see [[Moodle downloads]]). Handwritten GoodNotes notes can be exported to `Materials/Handwritten notes/` when assistant help is wanted.

> Start Hippo. Lecture 2 for Example Module just arrived from Moodle. Summarise the main ideas, connect them to my earlier notes, and save the result. Don't quiz me yet.

## Study session

> Start Hippo. Quiz me on Example Module Lecture 1, one question at a time. Explain my mistakes and save the quiz, feedback, and weak topics.

Other useful requests:

> Give me one exercise at my level. Let me solve it before showing the answer.

> Review my solution, point out the first mistake, and let me correct it myself.

> Make a revision plan for this module using my exam date and saved weak topics.

## Deadlines

Give the exact date, time, module, and whether it's an exam or submission; the assistant saves it in [[Profile]] (and the calendar, if connected).

## When finishing

> Stop here and save what we covered, my weak points, and the next step.

## File locations

- Source files: `mindAssistant/Modules/<Module>/Materials/`
- Module results: `mindAssistant/Modules/<Module>/Notes/`
- Cross-module notes and plans: `mindAssistant/Notes/`
- Agents: `mindAssistant/Agents/`

Related: [[Contract]] · [[Profile]] · [[State]] · [[Modules overview]]
