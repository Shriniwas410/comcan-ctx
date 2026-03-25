# 🧠 ComCan — Context Manager for AI Coding Agents

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-green.svg)](https://www.python.org/downloads/)

> **ComCan** gives AI coding agents (Cursor, Copilot, Claude Code) a persistent, enterprise-grade cognitive architecture.

Most developers solve the "AI context problem" by pasting random `.md` files or relying on the IDE's automatic vector search. These approaches fail in large enterprise repositories because the AI agent loses track of *what branch you are on*, *what commits you just made*, and *what the strict architectural rules are*. 

ComCan solves this by installing an invisible cognitive architecture directly into your Git repository:

- 🔄 **State Engine (The AI's RAM)** — Automated Git hooks (`post-commit`, `post-checkout`) generate a branch-accurate `CURRENT_STATE.md`. It surgically truncates directory trees and diffs to fit perfectly within the AI's token window.
- 📚 **Expertise Engine (The AI's Hard Drive)** — Uses lock-safe JSONL domain ledgers. Record wisdom once with `comcan learn`, and agents query it surgically thereafter.
- 🧠 **Main Brain (Manifesto)** — [NEW in v0.2.0] Synthesizes all scattered expertise into a centralized, human-readable `ARCHITECTURE_MANIFESTO.md`. This is the high-level Source of Truth for the whole repo.
- 🤖 **Autonomous Onboarding (Bootstrap)** — [NEW in v0.2.0] Scrapes existing repos to detect tech stacks (Node, Python, Docker, etc.) and auto-suggests initial architectural rules.
- 🛡️ **Enterprise Security** — Zero network access, secrets scrubbing, and path validation.
Standard IDE indexing (RAG) is great at finding *where* code is, but terrible at knowing *why* it's there or how branches differ. 
- **Indexing vs. State:** IDE vector indexes don't understand that you just switched branches. ComCan's `CURRENT_STATE.md` is instantly updated via Git hooks to represent your exact branch reality.
- **RAG vs. Rules:** RAG discovers old code; it doesn't know what the *new* rules are. ComCan's `expertise` engine teaches agents the *current* architectural decisions.
- **Static `.md` vs. Dynamic JSONL:** Giant `.cursorrules` files cause merge conflicts and token bloat. ComCan uses domain-sharded, lock-safe JSONL ledgers that agents query surgically.

### Philosophy: Why isn't domain learning "Automatic"?
Automatic codebase indexing (RAG) is prone to massive amounts of noise and hallucination. An AI cannot automatically deduce your team's *architectural intent* just by reading code. If a developer pastes a bad pattern from StackOverflow, an automated AI indexer treats that bad code as a "truth" to learn from. 

ComCan treats AI knowledge like documentation. The `comcan learn` command acts as a **conscious architectural ledger**. When you or an agent establishes a rule (*"Always use exponential backoff for the auth API"*), it is explicitly recorded and saved to a Git-tracked `.jsonl` file. This guarantees that your AI agent is operating on 100% accurate, PR-reviewed instructions, free from automated scraping noise.

## Quick Start

```bash
pip install comcan-ctx
cd your-project/
comcan init
```

That's it. ComCan will:
1. Create `.comcan/` directory with a `CURRENT_STATE.md` context file
2. Install Git hooks to auto-update context on commits and branch switches
3. Create `.cursorrules` so Cursor reads the context automatically

## Comprehensive Usage Guide

### Step 1: Initialize or Bootstrap

In a new repo:
```bash
comcan init
```

In a **legacy repo** you want to "Self-Onboard":
```bash
comcan bootstrap
```
*This scrapes the repo structure, identifies your tech stack, and generates your first `ARCHITECTURE_MANIFESTO.md` brain.*

### Step 2: Create Logical Domains

Break your project down into logical domains (e.g., `api`, `database`, `frontend`, `auth`).
```bash
comcan add database
comcan add auth
```

### Step 3: Record Expertise (The Core Loop)

Whenever you solve a tricky bug, establish a new convention, or finalize an architectural decision, record it immediately. You can do this yourself, or instruct Cursor/Claude to run this command for you:
```bash
# 1. Quick convention recording
comcan learn database "Always use WAL mode for SQLite to prevent locking"

# 2. Full record syntax (for detailed bug post-mortems)
comcan record api --type failure "Auth tokens not refreshed" --resolution "Added retry with exponential backoff"
```

### Step 4: The AI Injects the Knowledge

You are now done! When you ask Cursor a question like *"Write a new database fetch function"*, its custom `.cursorrules` file will silently instruct it to aggressively run:
```bash
comcan query database
```
The AI context window is instantly injected with all the recorded wisdom for that exact domain *before* it generates a single line of code.

### Step 5: Code & Commit

As you write code, change files, and switch branches, ComCan's Git hooks will silently rebuild `.comcan/CURRENT_STATE.md` in the background. The AI will always know exactly what branch it is on and what the latest commits accomplished.

### Step 6: Autonomous Agent Skills (Auto-Learn)

ComCan requires absolutely zero manual upkeep once initialized. 

When you run `comcan init`, it natively generates instruction files for your AI agents:
1. `.cursorrules` and `.cursor/rules/comcan.mdc` (For Cursor users)
2. `.agents/skills/comcan/SKILL.md` (For Antigravity users)

These files explicitly instruct your AI to **Autonomously run the `comcan learn` terminal command** after it completes a complex coding task or bug fix. The AI will read your codebase, infer the architectural rules itself, and update the JSONL ledgers in the background entirely on its own!

#### How to trigger in Cursor:
Cursor natively discovers `comcan.mdc` in the `.cursor/rules/` folder. You do not need to do anything. Simply ask Cursor to fix a bug in the Chat or Composer, and watch it organically launch the terminal and run `comcan learn` when it finishes writing the code.

#### How to trigger in Antigravity:
Antigravity natively discovers `SKILL.md` in the `.agents/skills/comcan/` folder. When you are pair programming with Antigravity, it will read this skill folder at startup. It will autonomously execute `run_command("comcan query")` before it writes code, and `run_command("comcan learn")` after you approve its changes.

### Monitor State

```bash
# Dashboard
comcan status

# Manual sync (usually automatic via hooks)
comcan sync

# Health check
comcan doctor
```

## How It Works

```
1. comcan init        → Creates .comcan/, hooks, .cursorrules
2. You commit code    → Hook fires, CURRENT_STATE.md auto-updates
3. AI reads context   → Agent starts with full project awareness
4. AI solves problem  → You record the lesson with comcan learn
7. git push           → Teammates' agents get smarter too
```

## Enterprise Features

ComCan is purpose-built to solve the "AI Cold Start Problem" for large engineering teams:

### 1. Iterative Knowledge Building 🧠
Instead of pasting the same rules over and over, developers use `comcan learn` to permanently record patterns, bugs, and architectural decisions into domain-specific ledgers. AI agents query these automatically.

### 2. Branch-Aware Context 🔀
`CURRENT_STATE.md` regenerates on every `git checkout` and `git commit`. If Dev A is on `feature-auth` and Dev B is on `bugfix-ui`, their agents see completely different, branch-accurate contextual states.

### 3. Conflict-Free Merging 🤝
ComCan configures `.gitattributes` to use `merge=union` for expertise JSONL files. Multiple developers can record new knowledge on different branches simultaneously without ever triggering a merge conflict.

### 4. Concurrent Agent Safety 🔒
Multiple agents running in parallel? No problem. The expertise engine uses advisory file-locking with atomic temp-file rotation. Multiple IDE tools or CI scripts can write to the same domain simultaneously without data corruption.

### 5. Token Budget Efficiency 📉
Dumping an enterprise codebase into an LLM window causes hallucinations and massive API costs. ComCan uses a multi-model token budget engine (o200k_base tokenizer aware) to mathematically allocate context window limits across the directory tree, commits, diffs, and expertise records.

## Architecture

```
.comcan/
├── CURRENT_STATE.md           # Auto-generated (branch, commits, tree)
├── comcan.config.yaml         # Configuration
├── comcan-skill.md            # Generic AI instructions
└── expertise/
    ├── database.jsonl          # Domain expertise (one per domain)
    ├── api.jsonl
    └── frontend.jsonl

ARCHITECTURE_MANIFESTO.md      # The "Main Brain" (centralized report)
```

### Context Budget Profiles

ComCan uses only ~5% of the model's context window, leaving 90%+ for actual work, via the `context_budget.py` engine (`tiktoken o200k_base`).

| Profile | Context Window | ComCan Budget | Target Models |
|---------|---------------|---------------|---------------|
| `standard` | 128k | ~6,400 tokens | GPT-4o, Claude 3.5 Sonnet |
| `large` | 200k | ~10,000 tokens | Claude 4, Cursor default |
| `max` | 1M+ | ~50,000 tokens | Gemini 2.5 Pro Max, Claude Opus |

*Note: Why use a budget? Without a token budget, dumping a large enterprise repo into an LLM causes severe "Lost in the Middle" syndrome and drains API credits. ComCan protects your context window by mathematically prioritizing recent commits, diffs, and surgical domain expertise.*

### Native AI Skills & PR Workflows

During `comcan init`, the CLI generates three native AI instruction files:
1. `.cursorrules` (Legacy IDE rules)
2. `.cursor/rules/comcan.mdc` (Cursor Rules format)
3. `.comcan/comcan-skill.md` (Portable generic AI skill)

**Human-in-the-Loop Security**: When an AI agent runs `comcan learn` to solve a problem, it writes directly to `.comcan/expertise/domain.jsonl`. Because this file is tracked in Git, the new "AI Skill" shows up in the Pull Request diff. If the AI hallucinates a bad rule, the Senior Engineer reviewing the PR rejects it. Bad AI knowledge never makes it to the `main` branch.

## CLI Reference

| Command | Description |
|---------|-------------|
| `comcan init` | Interactive setup wizard |
| `comcan bootstrap` | [v0.2.0] Scrape repo and generate initial brain |
| `comcan manifesto` | [v0.2.0] Generate ARCHITECTURE_MANIFESTO.md |
| `comcan bridge <branch>` | [v0.2.0] Import expertise from another branch |
| `comcan sync` | Regenerate context state |
| `comcan add <domain>` | Create expertise domain |
| `comcan learn <domain> "lesson"` | Quick-record a convention |
| `comcan record <domain> --type <type> "content"` | Full record syntax |
| `comcan query [domain]` | View domain expertise |
| `comcan search <query>` | Search all expertise |
| `comcan prime [domains...]` | Full context for agent injection |
| `comcan status` | Context dashboard |
| `comcan forget <domain> <id>` | Delete a record |
| `comcan doctor` | Health & security check |

## Security

ComCan is designed to **never trigger security scanners**:

- ✅ No `shell=True` — all subprocess calls target only `git`
- ✅ No `setup.py` — pure `pyproject.toml`, no post-install scripts
- ✅ No network access — zero HTTP calls, no telemetry
- ✅ No `eval()`/`exec()` — plain readable Python
- ✅ Secret scrubbing — API keys stripped before writing state files
- ✅ Path validation — all writes scoped to Git repo root

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT — see [LICENSE](LICENSE).
