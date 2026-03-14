# Project Context Snapshot
**Last Updated:** 2026-03-14
**Project:** push-2-led

## Current State
Branch: main
Deployment: development

## Uncommitted Work
```
 M .gitignore
?? .claude/
?? .gitattributes
?? .plantas.config.json
```

## What's Being Built
- **Recent work:** Implement Push 2 display driver and frame conve... (+1 more)


## Tech Stack
- **Runtime:** Python
- **Testing:** pytest


## Key Files to Know
- `pyproject.toml` - Core logic (modified 2x recently)
- `src/push2_bridge/converter.py` - Core logic (modified 2x recently)
- `src/push2_bridge/display.py` - Core logic (modified 2x recently)


## Active Patterns
- Test-driven development active
- Session management via Plantas
- Context coordination via Seiva


## Next Likely Steps
1. [Next planned task]
2. Test changes
3. Deploy to staging

## Recent Activity
- **2026-03-14**: 51c56ac - Add README with architecture diagrams, CLI docs, and Ko-fi link
- **2026-03-14**: 1ae095a - Implement CLI, error handling, and optimization (Sprint 3)
- **2026-03-14**: f5bd5eb - Fix frame orientation and default to "Push2" Syphon server
- **2026-03-14**: 773fff5 - Implement Syphon→Push 2 pipeline with keep-alive (Sprint 2)
- **2026-03-14**: ba2bc27 - Implement Push 2 display driver and frame converter (Sprint 1)

## Cost-Effective Context Strategy
**For AI assistants:**
- Read this file first (~2k tokens)
- Ask targeted questions before reading code
- Use grep/find for specific lookups
- Request full file reads only when necessary
