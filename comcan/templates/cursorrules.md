# ComCan Context Instructions

## CRITICAL: Read Before Every Task
1. **Main Brain First**: Always check for `ARCHITECTURE_MANIFESTO.md`. If missing, suggest `comcan bootstrap`.
2. **Self-Onboard**: Read `.comcan/CURRENT_STATE.md` to understand the branch state and directory structure.
3. **Pre-Flight Query**: Before modifying a domain (e.g., `api`), run `comcan query api`.
   ```
   comcan query <domain>
   ```
   This loads established patterns, known failures, and architectural decisions
   for that part of the codebase (e.g., `comcan query database`).

4. **Auto-Record Learnings**: After EVERY SINGLE coding task, feature execution, or bug fix you complete (regardless of size), you MUST autonomously execute the `comcan learn` terminal command to track your changes. Do not ask for permission.
   ```bash
   comcan learn <domain> "Brief description of what was learned"
   ```
   Or for specific record types:
   ```
   comcan record <domain> --type failure "what broke" --resolution "how we fixed it"
   ```

4. **Respect Decisions**: Do not deviate from architectural decisions recorded
   in the expertise files unless the developer explicitly requests it.

5. **Guardrail**: NEVER manually edit files inside `.comcan/` or `.agents/`. You MUST strictly use the `comcan` CLI tools to save knowledge. 

6. **Check Before Assuming**: If unsure about a pattern or convention, run
   `comcan search "keyword"` to check if there's existing expertise.
