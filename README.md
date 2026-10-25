<p align="center">
  <b>English</b> · <a href="README.es.md">Español</a>
</p>

<p align="center">
  <img src="og.png" alt="Lucid. Vibe coding, awake. Lead the design · Use what works · Commit &amp; control · Inspect everything · Defend" width="100%">
</p>

<p align="center">
  <a href="https://opcastil11.github.io/lucid-coding/"><b>Manifesto</b></a> ·
  <a href="https://opcastil11.github.io/lucid-coding/guide.html"><b>Guide (EN)</b></a> ·
  <a href="https://opcastil11.github.io/lucid-coding/guia.html"><b>Guía (ES)</b></a> ·
  <a href="SIGNATORIES.md"><b>Sign it</b></a>
</p>

<p align="center">
  <img alt="Version" src="https://img.shields.io/badge/version-1.0-1f4fd8">
  <img alt="License: CC BY-SA 4.0" src="https://img.shields.io/badge/license-CC%20BY--SA%204.0-b45309">
  <img alt="Languages" src="https://img.shields.io/badge/languages-EN%20%7C%20ES-131820">
  <img alt="Evidence" src="https://img.shields.io/badge/evidence-21%2C310%20prompts%20measured-5b6573">
</p>

# Lucid coding

**Vibe coding, awake.** Lucid coding is a methodology for building software with AI agents at full speed, while a human stays in charge of design, testing and security.

The idea comes from lucid dreaming: the dream and its speed stay the same, but you know you are dreaming and you can steer it. The agent executes. The human designs and defends. Both inspect.

> **Backed by data:** 21,310 prompts · 1,548 sessions · 195 projects · 11 months of daily work with AI agents.

## Contents

- [The manifesto](#the-manifesto)
- [LUCID in five letters](#lucid-in-five-letters)
- [The seven pillars](#the-seven-pillars)
- [Operating rules](#operating-rules)
- [Antipatterns it fixes](#antipatterns-it-fixes)
- [Evidence](#evidence)
- [Get started in four weeks](#get-started-in-four-weeks)
- [Sign the manifesto](#sign-the-manifesto)
- [FAQ](#faq)
- [License and citation](#license-and-citation)

## The manifesto

> We build software with AI agents every day. We keep their speed, but we code awake. That is why we value:
>
> **Architecture decided by humans** over code the AI improvises
> **Templates and repos that already work** over building from scratch
> **Continuous execution, one change at a time** over long plans with no commits
> **Product tested by hand** over automated coverage nobody looked at
> **Security reviewed by a person** over blind trust in the AI
>
> There is value in the items on the right, and we use them: the AI writes code and tests. But when they conflict, the items on the left win.

**Rule zero:** the agent is confidently wrong. Verify everything.

## LUCID in five letters

The five letters work the same way in English and Spanish.

| | English | Español | Who leads | Pillars |
|:-:|---|---|---|---|
| **L** | Lead the design | Liderar el diseño | 🟧 human | Architecture |
| **U** | Use what works | Usar lo que funciona | 🟦 AI, guided | Foundations · Method |
| **C** | Commit & control | Commit y control | 🟦 AI, traced | Proceed · Control & auditability |
| **I** | Inspect everything | Inspeccionar todo | 🟧🟦 human or agent | QA |
| **D** | Defend | Defender | 🟧 human | Security |

## The seven pillars

| # | Pillar | In one line |
|:-:|---|---|
| I | **Foundations** | Start from code and architectures that already exist and that you know. Templates over scratch. |
| 0 | **Architecture** | The soul of the code: what to build and how. The human's creativity lives here, and it is not delegated. |
| 1 | **Proceed** | Always forward. In execution the AI leads: terminal, browser, everything it can do. It does not hand work back. |
| 2 | **Method** | Prebuilt method templates per kind of build, turned into hard rules. Every repeated error becomes a new rule. |
| 3 | **QA** | Intensive, mostly human product QA, element by element. The AI automates unit tests and controlled automations. |
| 4 | **Security** | Still coded "by hand", with all available review time. **Never 100% delegated to the AI.** |
| 5 | **Control & auditability** | On a team, log sessions and prompts, linked to their commits. A written AI-use policy makes code security and credential use auditable. |

## Operating rules

0. **Bounded context.** Every change fits before the first context compaction. Each one runs a full GIED cycle (Generate, Integrate, Evaluate, Debug).
1. **Short, direct prompts.** Anything permanent goes in the context file, not in every message.
2. **One change per prompt.** Another AI must be able to audit it from the prompt and the diff alone.
3. **Concrete references, never adjectives.** Give a URL, a repo, the exact technical name and a test case.
4. **Numbered options.** The agent proposes 2–3 paths; the human answers with a number. "Proceed" always has an object.
5. **Every prompt ends in a commit.** Keep few active branches, each with a clear purpose.
6. **Multi-agent means separate branches.** One branch and one worktree per agent, with no exceptions.
7. **Credentials: defined, inventoried, rotatable.** Use environment variables and a vault. A dev key given to the agent goes in the inventory and is rotated before production.
8. **What worked twice becomes a template.** The agent should not reinvent; it should load.
9. **Model by task** *(proposal, under validation)*. Use the most capable model for architecture, security and audits.

The agent also gets three standing orders: suspect everything it reports, run e2e tests and check production, and face an **adversarial agent with a clean context** that attacks the code against rules written beforehand.

## Antipatterns it fixes

| Antipattern | Symptom | Fixed by |
|---|---|---|
| Backlog lives in the agent's head | "What's left?" every day | BACKLOG file + wrap-up event |
| Giant multi-topic sessions | The agent compacts and forgets the plan | Rule 0 |
| "Proceed" with no object | The agent guesses what you approved | Rule 4 |
| Believing the agent | "Done" with no proof; the bug shows up in production | Rule zero, e2e |
| The builder reviews itself | The agent defends its own code | Adversarial agent |
| Security delegated to the AI | Nobody read the auth code | Pillar 4 |
| Credentials without an inventory | Dev keys reach production unrotated | Rule 7 |

## Evidence

Lucid coding was distilled from one developer's year of daily work with AI coding agents, and the whole history was measured: every typed prompt from November 2025 to October 2026, plus every project context file. Compactions come from the transcripts the tool retains (the last month). **Every rule in Lucid coding comes from this data.** Counts come from regular expressions and are approximate.

| Signal | Measured | What it revealed |
|---|---:|---|
| Prompts analyzed | 21,310 | 1,548 sessions, 195 projects |
| Messages of three words or fewer | 27% | The human steers rather than specifies |
| "Proceed" and variants | ~1,230 | Approving is the main act |
| "What's left?" / "Shall we close?" | ~410 | The backlog lived in the agent |
| Compactions in the last month | 840 | One every ~6 prompts; 52% of sessions compacted |
| Design, logo and i18n complaints | ~360 | Requirements that were never written |
| Context files / largest | 135 / 226 KB | The agent's memory grew without a ceiling |

With this loop, a complete SaaS product went from idea to production in 17 hours.

**Measure your own transcripts and compare.** That is the point of publishing.

## Get started in four weeks

| When | Step | What to do |
|---|---|---|
| Week 1 | **Set up** | Create the five files (CONTEXT, INVARIANTS, BACKLOG, STATUS, LOG). Write invariants. Set up env vars, a vault and a credential inventory. Save kickoff and wrap-up templates. |
| Weeks 2–3 | **Practice** | Every prompt ends in a commit, every session closes before compaction and every milestone passes the human gate. Log the friction. |
| Week 4 | **Measure** | Count compactions per session, "what's left?" and design corrections. Then compare with before and adjust. |

## Sign the manifesto

If the values resonate, add one line to [`SIGNATORIES.md`](SIGNATORIES.md) and open a pull request titled `Sign: <your name>`. Details are in [`CONTRIBUTING.md`](CONTRIBUTING.md).

Experience reports are even more valuable: what you tried, on what kind of project, and what happened. Open an issue with the **Experience report** template.

## FAQ

**Is this anti vibe coding?** No. It keeps the speed and adds awareness. The right-hand items of the manifesto still have value.

**Is it tied to one tool?** No. It was developed with Claude Code, but the concepts are generic: a context file (CLAUDE.md, AGENTS.md…), isolated branches and written procedures.

**Who is it for?** Developers who already work with AI agents. The security pillar requires being able to read code.

**Why "proceed"?** It is the word typed most often in the measured sessions. The working title was the Spanish *«Proceda»*.

## License and citation

The manifesto and the guide are licensed under [CC BY-SA 4.0](LICENSE). You can copy, translate and adapt them with attribution, under the same license. Citation metadata is in [`CITATION.cff`](CITATION.cff).

