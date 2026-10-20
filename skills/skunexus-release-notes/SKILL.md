---
name: skunexus-release-notes
description: >-
  Determine the next version (patch / minor / major) and draft the GitHub release notes for a
  SkuNexus package or repository release - short, meaningful bullets for the consumer of the code
  (the developer who bumps the dependency), grouped by area, with no narrative. Both the version and
  the notes come from the real changes between the last release tag and `master` - which may hold
  several merged feature branches - never from a single feature branch. Ticket artifacts
  (.ai/<TICKET>/pr.md, backend-summary.md, fe-handoff.md) help find what matters, the diff decides.
  Use it whenever the developer wants release notes, a version decision, a changelog entry or a
  release description: "write the release notes", "what version should this be", "is this a minor or
  a major", "prepare the release for custom-fields", "what goes into the release", "describe this
  release". Creates the GitHub release only as a DRAFT, after explicit approval of the exact text;
  publishing is left to the developer.
  Do NOT trigger for: PR descriptions (skunexus-backend-pr), FE handoff (skunexus-fe-handoff), or
  per-ticket backend documentation (skunexus-backend-summary).
---

# Release version + release notes

Two deliverables, in this order:

1. **The version** - patch, minor or major, with a point-by-point justification.
2. **The release notes** - short bullets for **the consumer of the code**: a developer deciding
   whether to bump the dependency and what they get or have to do when they do. Every bullet answers
   "what changes for me?". No story of the ticket, no reasoning, no implementation tour - the PR
   description is where the why and the how live.

## The range: last tag → `master`

A release is cut from `master`, and `master` may by then hold **several merged feature branches**
(or an `rc` branch that accumulated several features). The version is decided by **everything** in
the range, not by any single branch: three patch-level fixes and one new interface make a minor;
one BC break anywhere makes a major.

```
git fetch --tags origin
git tag --sort=-v:refname | head -5                 # last release tag
git log --oneline --merges <last-tag>..origin/master  # which PRs / branches went in
git log --oneline <last-tag>..origin/master
git diff --stat <last-tag>..origin/master
git diff <last-tag>..origin/master -- composer.json # requirement changes
```

- **Final version and final notes - only from `<last-tag>..origin/master`.**
- **Preview before the merge** (the developer asks "what will this be" while the branch is still
  open): use `<last-tag>..<branch>` **and** check that `master` has nothing after the last tag
  (`git log <last-tag>..origin/master` empty). If `master` already has other merged work, include it
  - the preview is `<last-tag>..master` plus the branch. Label the result as a **preview** and say
  it must be re-checked against `master` after the merge.
- Map every commit in the range to a ticket / PR. For each ticket read `.ai/<TICKET>/pr.md`,
  `backend-summary.md`, `fe-handoff.md` if present - they point at what matters. The diff is the
  final authority.

## Deciding the version

Semantic versioning, `x.y.z`. Every package is versioned independently.

| Level | When |
|---|---|
| **patch** (`z`) | a fix in the code, **nothing new**, BC kept |
| **minor** (`y`) | patch conditions **+ something new**: new class, new test class, new interface, new database column, new endpoint, new GraphQL field - BC kept |
| **major** (`x`) | the above **+ a BC break** |

### What IS a BC break

- in an **interface**: changed return type of an existing method, added parameter, **new method**,
  removed method
- removed or renamed **class**
- removed database column or changed its definition (**including its name**)
- a breaking GraphQL change (e.g. renaming or removing an existing field)
- removed **`public` / `protected`** method of a class
- changed signature of a **`public` / `protected`** method of a class (e.g. `something($string)` →
  `something(string $string)` or `something($string): string`) - anyone who extended the class and
  overrode the method gets a fatal error

### What is NOT a BC break

- **constructor changes** of a class (new injected dependency, promotion, reordering) - excluded on
  purpose by the code of conduct in the `skunexus-be-core` README, otherwise every new dependency
  would be a major
- a class / method that was **added and changed inside the same range** - nobody could depend on it
  yet (e.g. a class created on a feature branch and renamed before release)
- new methods on a **class** (not an interface) - see the subclass check below

### Check for subclasses before trusting "no BC break"

Changed or new `public` / `protected` methods on a class can still collide with an override in a
consumer. Search the client repositories and the core for subclasses of every class whose methods
changed:

```
cd <dir with all skunexus-* checkouts> && for r in skunexus-*; do grep -rlnE 'extends (ClassA|ClassB)\b' "$r/app" "$r/src" 2>/dev/null | sed "s|^|$r: |"; done
```

A hit with an override of a changed method is a BC break for that consumer - report it.

### Dependencies between packages

If the range changes `composer.json` requirements: a package that now requires **only** a new major
of a dependency (or needed code changes to work with it) is itself a **major**; a package that allows
**both** majors (`^1.0|^2.0`) and works unchanged is a **minor**. A BC break in a part of the
dependency the package does not use does not force a major - the criterion is real usage.

### Present the decision

In chat: the last tag, the range, the proposed version, then one line per criterion - what is new
(why not patch), each BC-break category checked with the evidence (why not major), the subclass scan
result. The version is the developer's call to accept; until accepted, treat it as a proposal.

## What goes into the notes

Anything that changes the contract a consumer relies on:

- new / changed / removed **GraphQL fields, arguments, sorting, filtering**
- new / changed **REST endpoints, commands, events, plugin hooks**
- new **extension points** (interfaces, registries, overridable methods) and how to use them in one line
- **config keys, env vars, permissions**
- **migrations** and data changes run on deploy
- **behavior changes** of existing features (including bug fixes the consumer can observe)
- **BC breaks** and **required actions** (what the consumer must change) - always, in their own section
- a reassurance line **only** when a consumer could reasonably fear a change (e.g. "`value_type` is
  unchanged") - not as a general "nothing else changed"

## What stays out

- internal class renames, refactors, property promotion, code style
- tests, `.gitignore`, `.ai/` artifacts, CI files
- lock file changes that do not change the package's own requirements
- the reasoning behind a decision, alternatives considered, review history
- anything you cannot point to in the diff

If an item is borderline, leave it out and mention it to the developer below the draft
("left out: ...") so they can put it back.

## Writing rules

- **Group by area** (`## <grid / domain / feature>`), short heading - not by ticket. Several tickets
  touching the same area share one heading.
- **One bullet = one fact, one line.** GitHub renders release bodies as GFM, so a wrapped line
  becomes a hard break - never wrap a bullet.
- Lead with the name the consumer uses: field / argument / command / config key in backticks.
- After a ` - ` add at most one short clause that makes the fact meaningful (what it gives, what it
  replaces). No second sentence.
- Lowercase start of bullets, no trailing period - matches the existing notes.
- English. Plain hyphen `-` as a dash, not `—` / `–`.
- Breaking changes go in `## Breaking changes` at the **top**, each with the required action.
- End with the `**Full Changelog**` compare link `<last-tag>...<new-tag>`.
- Read 2-3 previous notes (`gh release view <tag> --json body -q .body`) and keep their tone.

Template and a real example: [`references/template.md`](references/template.md).

## Output and the GitHub gate

There is **no per-ticket artifact** for release notes - a release spans several tickets, so it does
not belong in any `.ai/<TICKET>/`. The GitHub release itself is the record.

1. Show the version decision and the notes draft **in chat** (notes as a fenced `markdown` block),
   followed by a short "left out" list and whether it is a preview or the final range.
2. Iterate with the developer until both are approved.
3. **Creating or editing a GitHub release is a write to GitHub** - do it only after explicit
   approval of the exact text and version, and only when asked. Always as a **draft**: put the body
   in a file **outside the repository** and run `gh release create <tag> --target master --title <tag>
   --notes-file <file> --draft` (or `gh release edit <tag> --notes-file <file>` on an existing draft).
   Then read it back (`gh release view <tag> --json body -q .body`) and diff against the file.
4. **Never publish the release.** A draft creates no tag - GitHub creates the tag and publishes the
   version only when the developer clicks **Publish** in the GitHub UI. The moment a version reaches
   consumers is the developer's call, the same as taking a PR out of draft.
