# Zalopay Knowledge Bot - 2-Day MVP Roadmap
## Fast End-to-End Demo (Claude Code Opus 4.8)

---

## 📊 MVP SCOPE

### What's Included ✅
```
Core Flows:
├─ User asks question in Teams
├─ Central router agent (1) classifies + routes
├─ 2 Department agents (Engineering + Product) search Confluence
├─ Agent-to-agent communication (if cross-dept)
├─ Response aggregation + formatting
├─ Send back to Teams with citations
└─ Full end-to-end working

Technology:
├─ Confluence integration (API client)
├─ Semantic search (local embeddings)
├─ Simple vector store (in-memory + JSON fallback)
├─ LLM calls via AgentBase API (Qwen 3.5)
├─ Teams webhook receiver
├─ FastAPI app (single process, no K8s)
└─ SQLite (local DB, no Postgres needed)

Key Features:
✅ Accurate responses (with citations)
✅ Multi-agent communication
✅ Response personalization (Engineer vs PM)
✅ Confluence real-time fetch
✅ Teams integration
✅ Demo-ready + extensible
```

### What's Skipped ❌
```
✗ Kubernetes / complex infrastructure
✗ Production database (PostgreSQL) - use SQLite
✗ Distributed caching (Redis) - use in-memory cache
✗ Weaviate cluster - use simple vector DB (Chroma or FAISS)
✗ 20 departments - use 2 for demo
✗ Complex auth/RBAC - simple header-based
✗ Advanced monitoring - basic logging only
✗ Disaster recovery - single instance
✗ Sophisticated feedback loops - simple rating only
```

---

## 💰 ESTIMATE - CLAUDE CODE OPUS 4.8

### Token Breakdown
```
Claude Opus 4.8 Input: $3/1M tokens
Claude Opus 4.8 Output: $15/1M tokens

Day 1 Estimates:
├─ Setup + base classes: 15k input, 8k output
├─ Confluence integration: 20k input, 12k output
├─ Vector search setup: 25k input, 15k output
├─ Agent framework: 30k input, 20k output
└─ Day 1 Total: ~90k input + 55k output = $0.45

Day 2 Estimates:
├─ Central router agent: 20k input, 12k output
├─ 2 Department agents: 25k input, 15k output
├─ Agent communication: 20k input, 12k output
├─ Teams integration: 20k input, 12k output
├─ Web API + testing: 25k input, 15k output
└─ Day 2 Total: ~110k input + 66k output = $0.55

MVP Total: ~200k tokens ≈ **$1.00 USD**

Time Estimate (Claude Code):
- Day 1: 4-5 hours coding
- Day 2: 4-5 hours coding
- Total: 8-10 hours
- With Claude Code: very fast (can be done in 2x4h working sessions)
```

---

## 🎯 DAY 1: FOUNDATION (4-5 hours)

### Morning Session (2-2.5 hours)

#### Task 1.1: Project Scaffolding
```
Files to create:
├─ project/
│  ├─ .env (local config)
│  ├─ requirements.txt (minimal deps)
│  ├─ main.py (FastAPI app)
│  ├─ config.py (settings)
│  │
│  ├─ agents/
│  │  ├─ __init__.py
│  │  ├─ base.py (BaseAgent)
│  │  ├─ central_router.py (1 agent)
│  │  ├─ engineering_agent.py (dept 1)
│  │  └─ product_agent.py (dept 2)
│  │
│  ├─ integrations/
│  │  ├─ __init__.py
│  │  ├─ confluence.py (API client)
│  │  └─ teams.py (webhook handler)
│  │
│  ├─ rag/
│  │  ├─ __init__.py
│  │  ├─ embeddings.py (local model)
│  │  ├─ vector_store.py (in-memory)
│  │  └─ retriever.py (search)
│  │
│  └─ storage/
│     ├─ __init__.py
│     └─ db.py (SQLite)

Prompt to Claude Code:
"Create MVP project structure for Zalopay knowledge bot.
- Use FastAPI for API server
- Create base agent class (async)
- Setup SQLite database
- Include .env template for Confluence + Teams tokens
- All files should have type hints
- Ready to fill in implementation"
```

**Expected Output:**
- Project structure created ✅
- All imports working ✅
- Can run `python main.py` without errors ✅

---

#### Task 1.2: Core Agent Base Classes
```python
# agents/base.py - what Claude Code should generate

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import asyncio

@dataclass
class Message:
    content: str
    role: str = "user"  # user, assistant, system
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        self.timestamp = datetime.now()

class BaseAgent(ABC):
    """Base class for all agents"""
    
    def __init__(self, name: str, model: str = "qwen-3.5"):
        self.name = name
        self.model = model
        self.memory: List[Message] = []
    
    @abstractmethod
    async def process(self, message: Message) -> Message:
        """Process incoming message, return response"""
        pass
    
    async def initialize(self):
        """Init agent resources"""
        pass
    
    async def shutdown(self):
        """Cleanup"""
        pass
    
    async def add_memory(self, message: Message):
        """Store in memory"""
        self.memory.append(message)

Prompt to Claude Code:
"Implement BaseAgent class with:
- Message dataclass (content, role, metadata, timestamp)
- Abstract process() method for subclasses
- Memory management (add_memory, get_memory)
- LLM integration skeleton (ready for Qwen API calls)
- Type hints everywhere
- All methods should be async"
```

**Expected Output:**
- BaseAgent class implemented ✅
- Message class with typing ✅
- Ready for subclasses ✅

---

### Afternoon Session (2-2.5 hours)

#### Task 1.3: Confluence Integration
```python
# integrations/confluence.py

class ConfluenceClient:
    """Fetch documents from Confluence"""
    
    def __init__(self, url: str, token: str):
        self.url = url
        self.token = token
    
    async def fetch_documents(self, space_key: str, limit: int = 50) -> List[Dict]:
        """
        Fetch pages from Confluence space
        Return: [{"title": "...", "content": "...", "url": "...", "space": "..."}]
        """
        pass
    
    async def fetch_page_by_id(self, page_id: str) -> Dict:
        """Fetch single page content"""
        pass

Prompt to Claude Code:
"Implement ConfluenceClient class:
- Use httpx for async HTTP calls
- Confluence Cloud API v2
- Methods: fetch_documents(space), fetch_page_by_id(page_id)
- Return structured dict with title, content, url, timestamp
- Error handling + logging
- Auth: Bearer token header
- Assume CONFLUENCE_URL, CONFLUENCE_TOKEN in .env
- Cache results in memory (optional but good)
- Handle pagination"
```

**Expected Output:**
- ConfluenceClient fully working ✅
- Can fetch from Confluence spaces ✅
- Structured document format ✅

---

#### Task 1.4: Vector Search (Simple)
```python
# rag/vector_store.py

class SimpleVectorStore:
    """
    In-memory vector store for MVP
    - Use Sentence Transformers for embeddings (local)
    - Store as list of dicts
    - Fallback: keyword search if no vectors
    """
    
    def __init__(self):
        self.documents = []  # [{content, embedding, source_url, ...}]
    
    async def add_documents(self, docs: List[Dict]):
        """Embed + store documents"""
        pass
    
    async def search(self, query: str, top_k: int = 3) -> List[Dict]:
        """Semantic search by query"""
        pass

Prompt to Claude Code:
"Implement SimpleVectorStore:
- Use sentence-transformers/all-MiniLM-L6-v2 (local, free)
- Store documents as list with embeddings
- search() uses cosine similarity
- Fallback to keyword matching if needed
- Return top_k results with relevance scores
- Include source_url and original content in results
- Fast implementation (no external DB needed)
- Async methods"
```

**Expected Output:**
- Vector store working locally ✅
- Semantic search functional ✅
- No external dependencies ✅

---

## 🚀 DAY 2: AGENTS + INTEGRATION (4-5 hours)

### Morning Session (2-2.5 hours)

#### Task 2.1: Central Router Agent
```python
# agents/central_router.py

class CentralRouterAgent(BaseAgent):
    """
    Routes queries to appropriate department agents.
    Detects which departments needed.
    Aggregates responses.
    """
    
    def __init__(self, engineering_agent, product_agent):
        super().__init__("CentralRouter")
        self.engineering_agent = engineering_agent
        self.product_agent = product_agent
        self.dept_agents = {
            "engineering": engineering_agent,
            "product": product_agent
        }
    
    async def process(self, message: Message) -> Message:
        """
        1. Classify query intent
        2. Detect departments
        3. Route to agents
        4. Aggregate responses
        5. Format with citations
        """
        pass

Prompt to Claude Code:
"Implement CentralRouterAgent:
- Inherit from BaseAgent
- Has LLM classify query (engineering/product/both)
- Route to 1-2 department agents based on classification
- Use asyncio.gather() for parallel requests
- Aggregate multiple responses
- Add user role from metadata (engineer vs PM)
- Include citations from department responses
- Return formatted Message with aggregated content
- Handle timeouts (max 10s per dept agent)"
```

**Expected Output:**
- Router agent implemented ✅
- Classifies queries correctly ✅
- Routes to correct departments ✅

---

#### Task 2.2: Department Agents (2)
```python
# agents/engineering_agent.py
# agents/product_agent.py

class EngineeringAgent(BaseAgent):
    """Handles engineering/technical questions"""
    
    def __init__(self, retriever, confluence_client):
        super().__init__("EngineeringAgent")
        self.retriever = retriever
        self.confluence = confluence_client
    
    async def process(self, message: Message) -> Message:
        """
        1. Search Confluence ENG space
        2. Retrieve relevant docs
        3. Generate response with citations
        4. Format for user role (engineer vs PM)
        """
        pass

class ProductAgent(BaseAgent):
    """Handles product/feature questions"""
    
    # Similar structure

Prompt to Claude Code:
"Implement 2 department agents (Engineering, Product):
- Each inherits from BaseAgent
- Fetch from specific Confluence spaces (ENG, PRODUCT)
- Search retriever for relevant docs
- Generate responses personalized by user role
  - Engineer: technical, code-focused
  - PM: feature/timeline focused
- Always include citations (url + title)
- Handle 'no results found' gracefully
- Async await for all operations"
```

**Expected Output:**
- 2 department agents working ✅
- Search Confluence correctly ✅
- Format responses per role ✅

---

### Afternoon Session (2-2.5 hours)

#### Task 2.3: Teams Integration
```python
# integrations/teams.py

class TeamsHandler:
    """
    Handle Teams webhook messages.
    Send responses back to Teams.
    """
    
    def __init__(self, bot_token: str, central_agent):
        self.bot_token = bot_token
        self.central_agent = central_agent
    
    async def handle_message(self, payload: Dict) -> Dict:
        """
        Receive Teams message
        Send to central agent
        Format response
        Send back to Teams
        """
        pass

# In main.py
@app.post("/webhooks/teams")
async def teams_webhook(payload: Dict):
    """Webhook endpoint for Teams"""
    response = await teams_handler.handle_message(payload)
    return response

Prompt to Claude Code:
"Implement TeamsHandler:
- Handle Teams webhook payload
- Extract message text + user info
- Pass to central agent
- Format agent response for Teams (markdown)
- Send back via Teams Bot API
- Include citations as markdown links
- Error handling for Teams API calls
- Log all interactions
- Support both @mention and direct messages"
```

**Expected Output:**
- Teams webhook working ✅
- Messages routed correctly ✅
- Responses formatted for Teams ✅

---

#### Task 2.4: FastAPI Integration + Testing
```python
# main.py

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import asyncio

app = FastAPI()

@app.on_event("startup")
async def startup():
    """Initialize agents + integrations"""
    global central_agent, teams_handler
    
    # Load config
    # Create agents
    # Create handlers
    pass

@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy"}

@app.post("/chat")
async def chat_api(query: str, user_role: str = "engineer"):
    """
    Test endpoint: send query directly
    Bypass Teams, get response as JSON
    """
    pass

@app.post("/webhooks/teams")
async def teams_webhook(payload: Dict):
    """Teams webhook"""
    pass

@app.get("/agents/status")
async def agent_status():
    """Check agents online"""
    pass

Prompt to Claude Code:
"Implement main FastAPI app:
- Setup event handlers (startup, shutdown)
- Create all agents in startup
- Initialize Confluence client
- Implement /health endpoint
- Implement /chat endpoint (test without Teams)
- Implement /webhooks/teams endpoint
- Implement /agents/status endpoint
- Add error handling + logging
- Include CORS if needed
- Ready to run: python main.py"
```

**Expected Output:**
- FastAPI app fully functional ✅
- All endpoints working ✅
- Agents initialized on startup ✅

---

#### Task 2.5: End-to-End Testing
```
Manual test flow:

1. Start server:
   python main.py

2. Test health:
   curl http://localhost:8000/health

3. Test chat endpoint (no Teams):
   curl -X POST "http://localhost:8000/chat?query=How%20do%20we%20deploy&user_role=engineer"

4. Check agent status:
   curl http://localhost:8000/agents/status

5. Test with Teams webhook:
   curl -X POST http://localhost:8000/webhooks/teams \
     -H "Content-Type: application/json" \
     -d '{"text": "What are the product features?", "from": "user123"}'

Prompt to Claude Code:
"Create comprehensive test suite:
- Unit tests for each agent
- Integration test for full flow
- Mock Confluence responses
- Test with pytest
- Include test fixtures
- Test error cases
- Test agent communication"
```

**Expected Output:**
- All tests passing ✅
- End-to-end flow working ✅
- Demo-ready ✅

---

## 📋 DETAILED FILE-BY-FILE CODING

### Day 1: Morning

**File 1: `requirements.txt` (2 min)**
```
fastapi==0.104.1
uvicorn==0.24.0
httpx==0.25.1
python-dotenv==1.0.0
pydantic==2.5.0
sentence-transformers==2.2.2
numpy==1.24.3
scikit-learn==1.3.2
pytest==7.4.3
pytest-asyncio==0.21.1
```

**File 2: `.env.example` (2 min)**
```
CONFLUENCE_URL=https://zalopay.atlassian.net/wiki
CONFLUENCE_TOKEN=<your-api-token>
CONFLUENCE_ENG_SPACE=ENG
CONFLUENCE_PRODUCT_SPACE=PRODUCT

TEAMS_BOT_TOKEN=<your-bot-token>
AGENTBASE_API_KEY=<your-key>
AGENTBASE_URL=https://api.agentbase.zalopay.com

LLM_MODEL=qwen-3.5
LLM_TEMPERATURE=0.7
```

**File 3: `config.py` (3 min)**
```python
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    confluence_url: str
    confluence_token: str
    confluence_eng_space: str
    confluence_product_space: str
    
    teams_bot_token: Optional[str] = None
    agentbase_api_key: str
    agentbase_url: str
    
    llm_model: str = "qwen-3.5"
    llm_temperature: float = 0.7
    
    class Config:
        env_file = ".env"

settings = Settings()
```

**Total Day 1 Morning: ~7 minutes boilerplate + 1.5 hours Claude Code**

### Day 1: Afternoon

**Confluence Integration (20 min of Claude Code)**
```python
# integrations/confluence.py
```

**Vector Store (20 min of Claude Code)**
```python
# rag/vector_store.py
```

**Retriever (10 min of Claude Code)**
```python
# rag/retriever.py
```

---

### Day 2: Morning

**Central Router Agent (20 min)**
```python
# agents/central_router.py
```

**Department Agents (20 min)**
```python
# agents/engineering_agent.py
# agents/product_agent.py
```

---

### Day 2: Afternoon

**Teams Integration (15 min)**
```python
# integrations/teams.py
```

**FastAPI Main (15 min)**
```python
# main.py
```

**Tests (15 min)**
```python
# tests/test_agents.py
# tests/test_integration.py
```

---

## 🎯 END RESULT - MVP FEATURES

### What Works End-to-End
```
Flow 1: Single Department Query
├─ User asks engineering question in Teams
├─ Webhook reaches /webhooks/teams
├─ CentralRouter classifies as "engineering"
├─ Routes to EngineeringAgent
├─ EngineeringAgent searches Confluence ENG space
├─ Retriever finds relevant documents
├─ LLM generates response with citations
├─ Response formatted as Teams markdown
├─ Sent back to Teams user
└─ ✅ User sees answer + links to Confluence

Flow 2: Cross-Department Query
├─ User asks about "payment feature architecture"
├─ CentralRouter detects needs Product + Engineering
├─ Both agents run in parallel
├─ Each searches their Confluence space
├─ Responses aggregated
├─ Citations from both departments included
├─ Sent to Teams as unified answer
└─ ✅ User gets complete picture

Flow 3: Agent Communication
├─ Product agent needs engineering context
├─ Calls engineering_agent.process() directly
├─ Engineering agent responds with info
├─ Product agent incorporates in final response
└─ ✅ Agents collaborate seamlessly

All Flows Include:
✅ Confluence citations (links + titles)
✅ Role-based formatting (engineer vs PM)
✅ Error handling + fallbacks
✅ Response timing <5-10 seconds typically
```

---

## 📊 MVP DELIVERABLES

### Code Files Created (15 total)
```
agents/
├─ __init__.py
├─ base.py (150 lines)
├─ central_router.py (200 lines)
├─ engineering_agent.py (150 lines)
└─ product_agent.py (150 lines)

integrations/
├─ __init__.py
├─ confluence.py (150 lines)
└─ teams.py (150 lines)

rag/
├─ __init__.py
├─ embeddings.py (50 lines)
├─ vector_store.py (200 lines)
└─ retriever.py (100 lines)

storage/
├─ __init__.py
└─ db.py (100 lines)

tests/
├─ __init__.py
├─ test_agents.py (200 lines)
└─ test_integration.py (150 lines)

Root:
├─ main.py (300 lines) FastAPI app
├─ config.py (50 lines)
├─ requirements.txt (15 lines)
├─ .env.example (15 lines)
└─ README.md (50 lines)
```

**Total: ~2000 lines of working code**

---

## ✅ VALIDATION CHECKLIST

By end of Day 2:

```
Functionality:
✅ Can query via /chat endpoint
✅ Gets back answer + citations
✅ Teams webhook receives messages
✅ Teams bot responds correctly
✅ 2 agents communicate with each other
✅ Central router routes correctly
✅ Roles affect response format (Engineer vs PM)
✅ Confidence scores included
✅ Handles "no results" gracefully

Code Quality:
✅ Type hints everywhere
✅ Proper async/await
✅ Error handling
✅ Logging throughout
✅ Tests passing
✅ No external services (except Confluence + Teams APIs)

Performance:
✅ Response time <10 seconds typical
✅ Handles concurrent requests
✅ Memory efficient (in-process vector store)
✅ No database needed

Demo-Ready:
✅ One command to start: python main.py
✅ Can test without Teams (use /chat endpoint)
✅ Can test with Teams (use webhook)
✅ Logs show what's happening
✅ Easy to understand code
```

---

## 🚀 HOW TO USE CLAUDE CODE

### Setup
```bash
# Install Claude Code
npm install -g @anthropic-ai/claude-code

# Start in project directory
claude code init

# Set context
claude code set-context "Build Zalopay knowledge bot MVP.
Use FastAPI, Confluence API, sentence-transformers, async.
Create agents that communicate with each other.
Teams integration via webhooks.
End-to-end flow from RAG to response."
```

### Day 1 Session (5 hours)
```bash
# Each task as separate prompt:

# Task 1.1
claude code create "Create project structure with FastAPI,
Confluence integration, vector store, SQLite.
Use requirements.txt, .env, config.py"

# Task 1.2
claude code create "Implement BaseAgent abstract class.
Message dataclass with content/role/metadata.
Async methods for initialize, shutdown, process."

# ... repeat for 1.3, 1.4, etc
```

### Day 2 Session (5 hours)
```bash
# Similar prompts for agents, integration, FastAPI app
```

### Testing
```bash
pytest tests/ -v
python main.py  # Run server
curl http://localhost:8000/health  # Test
```

---

## 📈 PROGRESSION PATH TO PROD

Once MVP is working (end of Day 2):

```
Day 3-4: Deploy MVP
├─ Docker image
├─ Deploy to AgentBase
├─ Real Teams bot
└─ Real Confluence

Week 2: Add 18 more departments
├─ Create agent for each
├─ Load knowledge from Confluence
├─ Test scaling

Week 3: Production hardening
├─ Database (PostgreSQL instead of SQLite)
├─ Caching (Redis)
├─ Monitoring
├─ Security (RBAC, PII masking)

Week 4: Launch
```

---

## 💡 MVP VS PROD COMPARISON

```
         MVP          PROD 
────────────────────────────────────────────────
Agents      2 departments        20 departments
Vector DB   In-memory            Weaviate cluster
Cache       None                 Redis
Database    SQLite               PostgreSQL
Sync        Manual               Daily batch
Monitoring  Logging only         Prometheus+ELK
Scaling     Single instance      Auto-scaling
Auth        None                 RBAC + audit
Cost        ~$0 (free tiers)     ~$1400/month

Both have:
✅ Confluence integration
✅ Semantic search
✅ Multi-agent communication
✅ Teams integration
✅ Accurate responses with citations
✅ End-to-end RAG pipeline
```

---

## 🎯 SUCCESS = WORKING DEMO

**End of Day 2, you have:**

1. **Working chatbot** that understands questions
2. **Searches Confluence** for real answers
3. **Agent communication** (2 agents talking to each other)
4. **Teams integration** (messages come in/out)
5. **Accurate citations** (links to Confluence)
6. **Role-based responses** (engineer vs PM)
7. **Clean codebase** (ready to extend)
8. **Testable code** (pytest suite included)

**What's missing (added later):**
- 18 more departments
- Production database + caching
- Distributed deployment
- Advanced monitoring
- Full RBAC

**But core system is COMPLETE and WORKING!** ✅

