# ComCan Context Instructions

## CRITICAL: Read Before Every Task
1. **Current State**: ALWAYS read `.comcan/CURRENT_STATE.md` first to understand:
   - What branch you're on
   - What changed recently (commits + file diffs)
   - The project's directory structure

2. **Domain Expertise**: Before modifying code in a specific area, run:
   ```
   comcan query <domain>
   ```
   This loads established patterns, known failures, and architectural decisions
   for that part of the codebase (e.g., `comcan query database`).

3. **Auto-Record Learnings**: After solving a complex issue or establishing a new
   pattern, you MUST autonomously open the terminal and save the lesson without asking the developer:
   ```bash
   comcan learn <domain> "description of what was learned"
   ```
   Or for specific record types:
   ```
   comcan record <domain> --type failure "what broke" --resolution "how we fixed it"
   ```

4. **Respect Decisions**: Do not deviate from architectural decisions recorded
   in the expertise files unless the developer explicitly requests it.

5. **Check Before Assuming**: If unsure about a pattern or convention, run
   `comcan search "keyword"` to check if there's existing expertise.
