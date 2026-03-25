---
description: How to autonomously record and query team expertise using the ComCan CLI.
---
# ComCan Context Manager Skill

You are operating in a repository powered by **ComCan** (Context Manager).
ComCan provides you with a persistent, branch-aware "RAM" and "Hard Drive" so you don't have to guess project infrastructure.

## 1. Always Read the RAM First
Before beginning your work, you MUST read the current project state:
Read the file: `.comcan/CURRENT_STATE.md`
This file tells you the current Git branch, recent commits, and directory tree.

## 2. Load the Hard Drive (Expertise)
If you are working on a specific domain (e.g., `frontend`, `database`), load the expertise ledger:
Execute command: `comcan query <domain>`
This explains the architectural rules and known failures.

## 3. Auto-Record New Skills
After EVERY SINGLE coding task, feature implementation, or bug fix you complete (regardless of size), you MUST autonomously execute the `comcan learn` command. DO NOT ask for permission. Just run the command to efficiently track all changes:
Execute command: `comcan learn <domain> "Brief description of the rule"`
For bugs: `comcan record <domain> --type failure "what broke" --resolution "how we fixed it"`

## 🚫 CRITICAL GUARDRAIL 🚫
**NEVER** manually edit files inside the `.comcan/` or `.agents/` directories. You MUST strictly use the `comcan learn` or `comcan record` CLI tools via `run_command` to save knowledge. The CLI will handle formatting automatically.
