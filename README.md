# sports-skills (Unavailable)

## Status

The upstream repository `machina-sports/sports-skills` is currently not publicly accessible.

## What is sports-skills?

sports-skills was a unified data adapter library for 15 sports via ESPN public APIs:
- Soccer, NFL, NBA, MLB, NHL, Cricket, Tennis, Golf, F1, MMA, etc.
- Zero authentication required (all public data)
- Unified adapter pattern across all sports

**Original Repository:** https://github.com/machina-sports/sports-skills  
**License:** MIT  

## Current Solution

Since sports-skills is unavailable, PromptBet implements **public API fallback adapters** that directly interface with ESPN and other public sports data sources.

```
services/data-ingestion/app/adapters/
├── base.py       — BaseAdapter ABC
├── soccer.py     — Soccer adapter (ESPN public API)
└── [other sports]
```

This approach:
- ✓ Provides identical functionality
- ✓ Uses the same public data sources (ESPN, openfootball, etc.)
- ✓ No external library dependencies
- ✓ Full control over error handling and caching

## Future: When sports-skills Becomes Available

If the upstream repository becomes accessible again, we can easily swap implementations:

**Current (public API fallback):**
```python
from app.adapters.soccer import SoccerAdapter  # Uses ESPN directly
from app.adapters.nfl import NFLAdapter
```

**Future (if sports-skills available):**
```python
from sports_skills.soccer import SoccerAdapter
from sports_skills.nfl import NFLAdapter
```

The adapter interfaces remain identical, so the swap is seamless.

## Placeholder

This directory exists only to document that:
1. We're aware of sports-skills and its benefits
2. We have a fallback implementation in place
3. We plan to integrate it when available

See `ATTRIBUTIONS.md` at the repo root for full details.
