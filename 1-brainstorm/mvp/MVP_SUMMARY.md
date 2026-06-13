# 2-Day MVP Summary - Quick Reference

## 📊 OVERVIEW

```
Project: Zalopay Knowledge Bot MVP
Timeline: 1 week
Tech: FastAPI, Confluence API, sentence-transformers, async Python
Cost: $1 USD (Claude API tokens)
Result: Working chatbot with agents, RAG, and Teams integration
```

---

## ⚡ WHAT YOU GET (End of Day 2)

### Working Features ✅
```
1. Confluence Integration
   └─ Fetches documents from 2 Confluence spaces (ENG, PRODUCT)

2. Semantic Search (RAG)
   └─ Local embeddings (sentence-transformers)
   └─ In-memory vector store
   └─ Returns relevant documents with citations

3. 3 Agents + Communication
   ├─ CentralRouterAgent (1) - classifies queries, routes to departments
   ├─ EngineeringAgent - answers technical questions
   ├─ ProductAgent - answers product questions
   └─ Agents can call each other for cross-dept queries

4. Response Generation
   └─ LLM integration (Qwen 3.5 via AgentBase)
   └─ Personalized by role (Engineer vs PM)
   └─ Always includes Confluence citations

5. Teams Integration
   └─ Webhook receiver for Teams messages
   └─ Sends responses back to Teams
   └─ Markdown formatting with links

6. Web API
   └─ /chat endpoint for testing (without Teams)
   └─ /health, /status endpoints
   └─ Error handling + logging
```

### Code Quality ✅
```
✅ Full type hints
✅ Async/await throughout
✅ Error handling
✅ Comprehensive logging
✅ Proper docstrings
✅ Test suite included
✅ Ready to extend
```

---

## 📅 2-DAY BREAKDOWN

### DAY 1: Foundation (5 hours)

**Morning (2.5h):**
1. Create project structure (15 min)
2. Implement BaseAgent abstract class (30 min)
3. Build Confluence API client (40 min)

**Afternoon (2.5h):**
4. Create embeddings generator (20 min)
5. Build simple vector store (40 min)
6. Create retriever (20 min)
7. Setup SQLite database (20 min)
8. Test everything (20 min)

**Result:** RAG pipeline working, can search Confluence

---

### DAY 2: Agents + Integration (5 hours)

**Morning (2.5h):**
1. Implement CentralRouter agent (30 min)
2. Build EngineeringAgent (20 min)
3. Build ProductAgent (20 min)
4. Add agent-to-agent communication (20 min)

**Afternoon (2.5h):**
5. Create Teams webhook handler (30 min)
6. Build FastAPI application (30 min)
7. Write tests (20 min)
8. Integration testing + fixes (20 min)
9. Final validation (20 min)

**Result:** Complete working system, end-to-end

---

## 🚀 IMPLEMENTATION PATH

### Step 1: Setup (5 min)
```bash
mkdir zalopay-bot-mvp
cd zalopay-bot-mvp

# Create these files manually (or use Claude Code):
# - requirements.txt
# - .env.example
# - config.py
# - Folder structure: agents/, integrations/, rag/, storage/, tests/
```

### Step 2: Copy Prompts
Open **CLAUDE_CODE_PROMPTS.md** and copy each prompt into Claude Code.

### Step 3: Execute in Order

**Day 1:**
```
Prompt 1: Project structure
Prompt 2: BaseAgent
Prompt 3: Confluence
Prompt 4: Embeddings
Prompt 5: Vector store
Prompt 6: Retriever
Prompt 7: Database
→ Test with: python -c "from agents.base import BaseAgent"
```

**Day 2:**
```
Prompt 8: CentralRouter
Prompt 9: EngineeringAgent
Prompt 10: ProductAgent
Prompt 11: Agent communication
Prompt 12: Teams handler
Prompt 13: FastAPI app
Prompt 14: Tests
Prompt 15: Integration tests
→ Test with: python main.py & curl http://localhost:8000/health
```

### Step 4: Validate
```bash
# Run tests
pytest tests/ -v

# Start server
python main.py

# In another terminal, test
curl "http://localhost:8000/chat?query=How%20do%20we%20deploy?user_role=engineer"

# Should return JSON with response + citations
```

---

## 📋 FILE CHECKLIST (15 total)

```
agents/
├─ __init__.py
├─ base.py                 ← Prompt 2
├─ central_router.py       ← Prompt 8
├─ engineering_agent.py    ← Prompt 9
└─ product_agent.py        ← Prompt 10

integrations/
├─ __init__.py
├─ confluence.py           ← Prompt 3
└─ teams.py                ← Prompt 12

rag/
├─ __init__.py
├─ embeddings.py           ← Prompt 4
├─ vector_store.py         ← Prompt 5
└─ retriever.py            ← Prompt 6

storage/
├─ __init__.py
└─ db.py                   ← Prompt 7

tests/
├─ __init__.py
├─ test_agents.py          ← Prompt 14
└─ test_integration.py     ← Prompt 15

Root/
├─ main.py                 ← Prompt 13
├─ config.py               ← Prompt 1
├─ requirements.txt        ← Prompt 1
├─ .env.example            ← Prompt 1
└─ .gitignore (optional)
```

---

## 💻 HOW TO USE CLAUDE CODE

### Start Claude Code
```bash
# Install if needed
npm install -g @anthropic-ai/claude-code

# Start in project directory
cd zalopay-bot-mvp
claude code init
```

### Workflow
```
1. Open CLAUDE_CODE_PROMPTS.md
2. Read "CONTEXT" section at top
3. For each prompt:
   a) Copy prompt text
   b) Paste into Claude Code chat
   c) Wait for response
   d) Review + accept code
   e) Claude Code creates file automatically
4. Continue to next prompt
```

### Quick Test After Each Major Component
```bash
# After BaseAgent
python -c "from agents.base import BaseAgent; print('✅')"

# After Confluence
python -c "from integrations.confluence import ConfluenceClient; print('✅')"

# After agents
python -c "from agents.central_router import CentralRouterAgent; print('✅')"

# After FastAPI
python main.py &
sleep 2
curl http://localhost:8000/health
```

---

## 🎯 EXPECTED OUTPUT - END OF DAY 2

### Terminal 1: Start Server
```bash
$ python main.py
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Loaded 150 documents from Confluence
INFO:     Central router agent initialized
INFO:     Product agent initialized
INFO:     Engineering agent initialized
INFO:     Teams handler ready
```

### Terminal 2: Test Chat
```bash
$ curl "http://localhost:8000/chat?query=How%20do%20we%20deploy&user_role=engineer"

{
  "response": "Based on our deployment guide, we use Kubernetes with GitLab CI/CD pipeline. Here's the process:\n\n1. Create deployment manifest\n2. Push to main branch\n3. GitLab CI builds image\n4. Deploy to staging\n5. Manual promotion to prod\n\nSee details in the deployment guide.",
  "citations": [
    {
      "title": "Deployment Guide",
      "url": "https://zalopay.atlassian.net/wiki/spaces/ENG/pages/12345/Deployment"
    },
    {
      "title": "CI/CD Pipeline Setup",
      "url": "https://zalopay.atlassian.net/wiki/spaces/ENG/pages/67890/CICD"
    }
  ],
  "department": "engineering",
  "confidence": 0.92
}
```

### Tests
```bash
$ pytest tests/ -v

tests/test_agents.py::test_central_router_classification PASSED
tests/test_agents.py::test_engineering_agent_search PASSED
tests/test_agents.py::test_product_agent_search PASSED
tests/test_agents.py::test_agent_communication PASSED
tests/test_integration.py::test_end_to_end_engineering_query PASSED
tests/test_integration.py::test_end_to_end_product_query PASSED
tests/test_integration.py::test_cross_department_query PASSED

===== 7 passed in 2.34s =====
```

---

## 🔄 FLOW DIAGRAM

```
User asks in Teams:
  "How do we deploy services?"
        ↓
Teams webhook → /webhooks/teams
        ↓
CentralRouterAgent receives message
        ↓
    ├─ Classify intent: "ENGINEERING"
    ├─ Detect departments: ["engineering"]
    └─ Route to EngineeringAgent
        ↓
EngineeringAgent.process()
    ├─ Search Confluence ENG space
    ├─ Find: "Deployment Guide"
    ├─ Generate response
    └─ Add citations
        ↓
CentralRouter aggregates
    ├─ Format for Teams
    └─ Include Confluence links
        ↓
Send back to Teams user
    ✅ User sees answer + links
```

---

## 📈 NEXT STEPS (After MVP Works)

### Day 3-4: Scale to 20 Departments
- Create 18 more agents (same pattern as EngineeringAgent)
- Load all Confluence spaces
- Test routing accuracy

### Week 2: Production Hardening
- Add PostgreSQL (replace SQLite)
- Add Redis caching
- Deploy to Docker
- Setup monitoring

### Week 3-4: Deploy to Production
- Use AgentBase /agentbase-deploy
- Setup Teams bot in production
- Load real Confluence data
- Monitor and iterate

---

## ✅ VALIDATION CHECKLIST

### Code Quality
- [ ] All files have type hints
- [ ] All methods are async
- [ ] All classes have docstrings
- [ ] Logging at key points
- [ ] Error handling everywhere

### Functionality
- [ ] Confluence integration works
- [ ] Vector search finds documents
- [ ] Agents can communicate
- [ ] Central router routes correctly
- [ ] Teams webhook responds
- [ ] Citations included in responses

### Testing
- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] /chat endpoint works
- [ ] /health endpoint works
- [ ] /agents/status works

### Demo Readiness
- [ ] Can start with `python main.py`
- [ ] Can test without Teams
- [ ] Responses are accurate
- [ ] Citations link to real Confluence
- [ ] Code is clean and understandable

---

## 💡 TROUBLESHOOTING

### Issue: Imports fail
**Solution:** Check all __init__.py files exist in each folder

### Issue: Confluence API errors
**Solution:** Verify CONFLUENCE_TOKEN in .env is valid service account token

### Issue: LLM calls fail
**Solution:** Verify AGENTBASE_API_KEY and AGENTBASE_URL correct

### Issue: Tests timeout
**Solution:** Increase timeout, or mock external calls

### Issue: Vector search returns nothing
**Solution:** Check documents were loaded into vector_store on startup

---

## 📞 KEY CONTACTS

For issues with:
- **FastAPI**: https://fastapi.tiangolo.com/
- **Confluence API**: https://developer.atlassian.com/cloud/confluence/rest/v2/
- **sentence-transformers**: https://www.sbert.net/
- **asyncio**: Python docs
- **pytest**: https://docs.pytest.org/

---

## 🎉 SUCCESS METRICS

By end of Day 2:

```
✅ 15 files created, all working
✅ ~2000 lines of production-quality code
✅ Full end-to-end RAG system
✅ Agent communication working
✅ Tests passing
✅ Ready to demo
✅ Easy to extend (20 departments is just copy-paste)
✅ Cost < $2 for entire implementation

Time: 10 hours (2 × 5-hour work days)
Cost: $1 (Claude API)
Result: Production-ready MVP
```

---

## 📚 FILES TO REFERENCE

1. **ZALOPAY_ARCHITECTURE.md** - Full 4-week plan
2. **MVP_2DAY_ROADMAP.md** - Detailed 2-day roadmap
3. **CLAUDE_CODE_PROMPTS.md** - Exact prompts to use ← **START HERE**
4. **COMPLETE_STRUCTURE.md** - Full project structure
5. **IMPLEMENTATION_ROADMAP.md** - Day-by-day week 1-4

---

**Ready to build?** 🚀

1. Read this summary
2. Open **CLAUDE_CODE_PROMPTS.md**
3. Start Claude Code
4. Copy prompts and code!

Good luck! 💪
