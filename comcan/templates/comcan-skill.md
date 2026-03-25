# ComCan Agent Skill Definition

**Context:** You are an AI Coding Agent operating in a repository that uses **ComCan** (Context Manager).
**Goal:** Prevent hallucinations, respect team conventions, and build persistent knowledge.

## Core Directives

1. **Consult the Main Brain:** Check for `ARCHITECTURE_MANIFESTO.md`. If it exists, read it first. If missing, suggest `comcan bootstrap`.
2. **Self-Onboard:** Read `.comcan/CURRENT_STATE.md` immediately to understand the branch state and directory structure.
3. **Pre-Flight Query:** Before modifying a subsystem (e.g., `api`), run `comcan query api` in the terminal to load domain-specific rules. architectural decisions and constraints.
4. **Keyword Check:** If you encounter an unfamiliar internal system, run `comcan search "<keyword>"`.
5. **Knowledge Creation:** After EVERY SINGLE coding task, feature implementation, or bug fix you complete (regardless of size), you MUST autonomously execute `comcan learn <domain> "brief description"`. Do not skip this!

*Note: You have permission to execute `comcan` CLI commands autonomously to gather this context.*

## 🚫 CRITICAL GUARDRAIL 🚫
**NEVER** manually edit files inside the `.comcan/` or `.agents/` directories. You MUST strictly run the `comcan learn` or `comcan record` CLI tools in the terminal to save knowledge. The CLI will handle formatting automatically.
