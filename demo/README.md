# SmartChatbox Demo

Real LLM-powered multi-turn interview → coherent prompt synthesis.

**NO MOCKS** - Uses actual Claude API.

## Quick Start

```bash
# 1. Set your API key
export ANTHROPIC_API_KEY='your-key-here'

# 2. Install dependencies
pip install fastapi uvicorn anthropic httpx

# 3. Run the server
cd demo
python server.py

# 4. Open browser
# http://localhost:8000
```

## What It Does

1. **Multi-turn Interview**: Claude asks contextual follow-up questions
2. **Real-time Confidence**: Watch confidence build as you provide context
3. **Coherent Synthesis**: Final prompt reads like a human expert wrote it (NOT template-filled)

## Files

| File | Purpose |
|------|---------|
| `server.py` | FastAPI backend with real Claude API integration |
| `index.html` | Frontend UI with live status updates |
| `test_real_llm.py` | Test script for real conversation flow |
| `test_final_prompt.py` | Test script to get final synthesized prompt |

## Example Conversation

```
User: "I need help with my marketing"
Claude: "What specific challenge are you trying to solve?" (20% confidence)

User: "B2B SaaS, struggling with lead generation"
Claude: "What have you tried so far?" (60% confidence)

User: "Content marketing, but low engagement"
Claude: "I understand. Ready to create your prompt." (75% confidence)

→ Final synthesized prompt (NOT template-filled!)
```

## Architecture

```
Frontend (index.html)
    ↓ POST /api/session/{id}/message
FastAPI Server (server.py)
    ↓
SmartRefiner (orchestration/tools/smart_refiner.py)
    ↓
Real Claude API (claude-sonnet-4-20250514)
```
