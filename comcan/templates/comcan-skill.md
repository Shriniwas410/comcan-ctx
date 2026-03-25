# ComCan Agent Skill Definition

**Context:** You are an AI Coding Agent operating in a repository that uses **ComCan** (Context Manager).
**Goal:** Prevent hallucinations, respect team conventions, and build persistent knowledge.

## Core Directives

1. **Self-Onboard:** Read `.comcan/CURRENT_STATE.md` immediately to understand the branch state and directory structure.
2. **Pre-Flight Query:** Before modifying a subsystem (e.g., `api`), run `comcan query api` in the terminal to load all domain-specific architectural decisions and constraints.
3. **Keyword Check:** If you encounter an unfamiliar internal system, run `comcan search "<keyword>"`.
4. **Knowledge Creation:** If you spend time debugging a tricky issue, run `comcan learn <domain> "lesson learned"` so the next agent doesn't repeat your mistake.

*Note: You have permission to execute `comcan` CLI commands autonomously to gather this context.*

## 🚫 CRITICAL GUARDRAIL 🚫
**NEVER** manually edit files inside the `.comcan/` or `.agents/` directories. You MUST strictly run the `comcan learn` or `comcan record` CLI tools in the terminal to save knowledge. The CLI will handle formatting automatically.
