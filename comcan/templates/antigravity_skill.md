---
description: How to autonomously record and query team expertise using the ComCan CLI.
---
## 1. Consult the Main Brain First
Before doing ANYTHING else, check for the file: `ARCHITECTURE_MANIFESTO.md`.
This is the "Source of Truth" for the repository architecture. If it exists, read it immediately.
If it is missing, you MUST suggest that the user runs `comcan bootstrap` to generate it.

## 2. Read the RAM (Current State)
Read the file: `.comcan/CURRENT_STATE.md`
This file tells you the current Git branch, recent commits, and directory tree.

## 3. Load the Hard Drive (Expertise)
If you need deeper domain-specific rules (e.g., `api`), use the expertise ledger:
Execute command: `comcan query <domain>`
This explains the architectural rules and known failures.

## 3. Auto-Record New Skills
After EVERY SINGLE coding task, feature implementation, or bug fix you complete (regardless of size), you MUST autonomously execute the `comcan learn` command. DO NOT ask for permission. Just run the command to efficiently track all changes:
Execute command: `comcan learn <domain> "Brief description of the rule"`
For bugs: `comcan record <domain> --type failure "what broke" --resolution "how we fixed it"`

## 🚫 CRITICAL GUARDRAIL 🚫
**NEVER** manually edit files inside the `.comcan/` or `.agents/` directories. You MUST strictly use the `comcan learn` or `comcan record` CLI tools via `run_command` to save knowledge. The CLI will handle formatting automatically.
