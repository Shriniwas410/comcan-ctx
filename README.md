# 🧠 ComCan — Context Manager for AI Coding Agents

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-green.svg)](https://www.python.org/downloads/)

A **single Python package** that gives AI coding agents (Cursor, Claude Code, etc.) a complete cognitive architecture:

- **🔄 State Engine (RAM)** — Auto-generates a context file on every commit/branch switch via Git hooks
- **📚 Expertise Engine (Hard Drive)** — Structured JSONL records that accumulate project knowledge over time
- **🛡️ Security First** — Zero network access, secret scrubbing, no post-install scripts

Designed for **large codebases** where naive context dumps overwhelm LLM token windows.

### Why not just use Cursor/Copilot's native indexing?
Standard IDE indexing (RAG) is great at finding *where* code is, but terrible at knowing *why* it's there or how branches differ. 
- **Indexing vs. State:** IDE vector indexes don't understand that you just switched branches. ComCan's `CURRENT_STATE.md` is instantly updated via Git hooks to represent your exact branch reality.
- **RAG vs. Rules:** RAG discovers old code; it doesn't know what the *new* rules are. ComCan's `expertise` engine teaches agents the *current* architectural decisions.
- **Static `.md` vs. Dynamic JSONL:** Giant `.cursorrules` files cause merge conflicts and token bloat. ComCan uses domain-sharded, lock-safe JSONL ledgers that agents query surgically.

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

## Usage

### Record Expertise

```bash
# Quick convention recording
comcan learn database "Always use WAL mode for SQLite"

# Full record syntax
comcan record api --type failure "Auth tokens not refreshed" --resolution "Added retry with exponential backoff"

# Add a new domain
comcan add frontend
```

### Query Knowledge

```bash
# View all database expertise
comcan query database

# Search across everything
comcan search "authentication"

# Full context dump for agent injection
comcan prime
```

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
└── expertise/
    ├── database.jsonl          # Domain expertise (one per domain)
    ├── api.jsonl
    └── frontend.jsonl
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
