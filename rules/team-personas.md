# Team personas: build profiles from new interactions (all projects)

Profiles live in `~/.claude/people/`; the roster is `README.md` there. They exist so that persona reviews ("act as the tech lead") are grounded in what the person has actually said and done, not invented.

**Purpose: learn from your peers.** A profile records what a teammate's reviews teach: the standards they hold and the problems they catch. Use it to raise the work to that standard before they have to point it out. It is not a map for predicting a reviewer's objections and getting past them.

**Profile shape.** Frontmatter `name`, `handles` (`github`, `jira`), `role`, `org`, `projects`, `status`; then `# <Full Name>` and the sections `## Review lens`, `## Positions and decisions`, `## How they review` (what they check, and in what order), `## What they find clear` (the format and level of detail that make a change easy for them to review), `## Observation log`. File name `firstname-lastname.md`. The roster `README.md` is one table: Profile · Role · Org · GitHub · Seen in.

## Capture (going forward, every project)
- **When to capture.** In the course of normal work you will read a rostered teammate's content. When you do, append any **new, review-relevant** observation to their profile's Observation log at the end of that step. The sources that count:
  - GitHub: PR reviews, review comments, replies to reviews (`gh pr view <n> --comments`, `gh api repos/{o}/{r}/pulls/{n}/reviews|comments`);
  - Jira comments, QA results and ticket fields they wrote;
  - meeting transcripts;
  - Slack or chat text the user pastes.
- **Log format:** `- YYYY-MM-DD · <project> · <source ref: PR#/comment URL/Jira key> · <observation>`.
  - Write at most 1–3 bullets per interaction.
  - Skip anything already logged.
  - Don't announce it beyond a one-line mention.
- **What counts** (what the next change can learn from):
  - what they flag or request in reviews, and why;
  - their quality bar and the patterns they push, so the next change meets them;
  - stated technical or product positions and decisions;
  - the evidence that settles a question for them (a test, a measurement, the code path), so the next change brings it;
  - recurring questions they ask, so the next change answers them.
- **Upkeep:**
  - When the log has grown by about 5 entries, rewrite the **Review lens** section as a short distilled list.
  - Put durable positions under **Positions and decisions**, with date and source.
- **New people.** Add a profile, and a row in `README.md`, once someone appears as a reviewer or approver in two or more interactions. Capture their GitHub and Jira handles when you see them.
- **Start from now.** Don't back-mine history unless the user asks.

## Use
- **Persona reviewer prompts.** When a review panel includes a rostered person (e.g. the `skunexus-contract` panel), read their profile into the persona prompt. Give it their role, Review lens, positions, and the 10 most recent log entries.
- **Thin profiles.** If a profile is thin, say so in the review output, and lean on their documented role.
- **Label the output** "simulated <name> review". It is never that person's actual opinion. Never use a profile to impersonate the person in anything sent to others.

## Guardrails
- **Learn, don't game.** When a profile or persona review predicts an objection, fix its cause, or raise it with the reviewer openly. Never word or scope a change to slip it past them, hide a weakness from them, or flatter them.
- **Work only.** Record review and technical behaviour. No personal life, health or HR matters, and no judgements of character or competence ("careless", "slow").
- **Evidence and data minimisation.** Every bullet cites its source. Store no secrets, customer data or patient data.
- **The user's view.** If the user says to drop or change something about a person, do it immediately.
