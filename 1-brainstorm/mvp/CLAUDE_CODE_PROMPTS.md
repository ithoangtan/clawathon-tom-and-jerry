# Claude Code Prompts - MVP 2-Day Build
## Copy-paste these prompts into Claude Code (Opus 4.8)

---

## 🎯 CONTEXT (Paste First)

```
You are building Zalopay Knowledge Bot MVP

Requirements:
- FastAPI backend (async)
- Fetch from Confluence API
- Semantic search with local embeddings
- 2 Department agents (Engineering, Product)
- 1 Central router agent
- Agent-to-agent communication
- Teams webhook integration
- End-to-end RAG: Question → Search → Response → Teams
- SQLite for storage (not PostgreSQL)
- In-memory vector store (not Weaviate)

Goals:
- Complete working system
- Full end-to-end flow tested
- Production-quality code (typing, async, error handling)
- Ready to extend to 20 departments

Tech Stack:
- FastAPI, httpx, SQLite, sentence-transformers
- Async throughout
- Type hints everywhere
- Pytest for testing
- Confluence Cloud API v2
- Qwen 3.5 via AgentBase API calls

File structure will be:
agents/, integrations/, rag/, storage/, tests/, main.py, config.py

Start with scaffold, then implement each component.
```

---

## 📅 DAY 1: FOUNDATION (5 hours)

### Session 1A: Boilerplate (15 min - manual or auto)

**Prompt 1: Create project structure**
```
Create the following files for Zalopay Knowledge Bot MVP:

1. requirements.txt with:
   - fastapi, uvicorn, httpx
   - python-dotenv, pydantic
   - sentence-transformers, numpy, scikit-learn
   - pytest, pytest-asyncio

2. .env.example with:
   CONFLUENCE_URL, CONFLUENCE_TOKEN
   CONFLUENCE_ENG_SPACE=ENG
   CONFLUENCE_PRODUCT_SPACE=PRODUCT
   TEAMS_BOT_TOKEN
   AGENTBASE_API_KEY, AGENTBASE_URL
   LLM_MODEL=qwen-3.5

3. config.py using pydantic BaseSettings:
   - confluence_url, confluence_token, spaces
   - teams_bot_token, agentbase settings
   - llm_model, temperature
   - class Config: env_file = ".env"

4. Create empty __init__.py files in:
   agents/, integrations/, rag/, storage/, tests/

All files should have proper imports and structure.
```

---

### Session 1B: Base Agent (30 min)

**Prompt 2: BaseAgent abstract class**
```
Create agents/base.py with complete implementation:

1. Message dataclass:
   - content: str
   - role: str (user/assistant/system)
   - metadata: Dict[str, Any] = None
   - timestamp: datetime auto-set in __post_init__

2. BaseAgent abstract class:
   - __init__(name: str, model: str = "qwen-3.5")
   - async def process(message: Message) -> Message: (abstract)
   - async def initialize() -> None
   - async def shutdown() -> None
   - async def add_to_memory(message: Message)
   - async def get_memory(limit: int = None) -> List[Message]
   - memory: List[Message] attribute

3. All methods have:
   - Type hints (including return types)
   - Docstrings
   - Proper async/await
   - self.logger for logging

4. Include logger setup:
   - import logging
   - self.logger = logging.getLogger(f"agent.{name}")

Requirements:
- Use ABC (from abc import ABC, abstractmethod)
- All methods async
- Well-documented
- Ready for subclassing
```

---

### Session 1C: Confluence Integration (40 min)

**Prompt 3: Confluence API client**
```
Create integrations/confluence.py with ConfluenceClient class:

Features:
1. __init__(url: str, token: str)
   - Store url, token
   - Create httpx.AsyncClient with auth header

2. async def fetch_documents(
       space_key: str,
       limit: int = 50
   ) -> List[Dict]:
   - Call Confluence API: /wiki/api/v2/spaces/{space}/pages
   - Extract: id, title, body (plain text), status
   - Return list of {title, content, url, space, timestamp}
   - Handle pagination
   - Cache results in dict self._cache

3. async def fetch_page(page_id: str) -> Dict:
   - Fetch single page by ID
   - Return full content with metadata

4. Error handling:
   - Try/except for API calls
   - Log errors
   - Return empty list on failure

5. Initialization cleanup:
   - Add __aenter__, __aexit__ for context manager
   - Proper resource cleanup

Requirements:
- Use httpx.AsyncClient
- Confluence v2 API endpoints
- Bearer token auth
- Return plain text content (not HTML)
- Include source URL
- Type hints for all methods
```

---

### Session 1D: Vector Store & Embeddings (40 min)

**Prompt 4: Embeddings generator**
```
Create rag/embeddings.py with local embedding support:

1. EmbeddingGenerator class:
   - __init__():
     - Load model: sentence-transformers/all-MiniLM-L6-v2
     - Store as self.model
   
   - def embed(text: str) -> np.ndarray:
     - Generate embedding using model.encode()
     - Return 384-dimensional vector
     - Handle empty text gracefully
   
   - def embed_batch(texts: List[str]) -> List[np.ndarray]:
     - Generate embeddings for multiple texts
     - Use batch processing for speed
     - Return list of vectors

2. Cosine similarity helper:
   - def cosine_similarity(vec1, vec2) -> float:
   - Return score between -1 and 1

3. All methods have:
   - Type hints
   - Docstrings
   - Error handling

Requirements:
- Use sentence_transformers.SentenceTransformer
- Import numpy for vector operations
- All operations in-memory (no external calls)
- Fast execution
```

**Prompt 5: Vector store**
```
Create rag/vector_store.py with SimpleVectorStore class:

Structure:
1. __init__():
   - self.documents = []  # Store {content, embedding, source_url, title, space, timestamp}
   - self.embeddings = None  # numpy array
   - self.embedding_gen = EmbeddingGenerator()

2. async def add_documents(docs: List[Dict]):
   - For each doc in docs:
     - Generate embedding using embedding_gen
     - Store in self.documents
     - Update self.embeddings numpy array
   - Log progress

3. async def search(
       query: str,
       top_k: int = 5,
       threshold: float = 0.5
   ) -> List[Dict]:
   - Generate query embedding
   - Calculate cosine similarity to all documents
   - Sort by score descending
   - Return top_k results with {content, score, source_url, title, space}
   - Only return if score > threshold

4. async def clear():
   - Reset documents and embeddings

Requirements:
- All operations async
- Use numpy for efficient similarity calculation
- Type hints everywhere
- Docstrings
- Handle empty store gracefully
- Return results with scores
```

---

### Session 1E: Retriever (20 min)

**Prompt 6: Hybrid retriever**
```
Create rag/retriever.py with HybridRetriever class:

1. __init__(vector_store: SimpleVectorStore):
   - Store vector_store reference

2. async def retrieve(
       query: str,
       department: str,
       top_k: int = 5
   ) -> List[Dict]:
   - Search vector store with query
   - Filter by department (if not included, search all)
   - Return top_k results with:
     - content, source_url, title, department, score

3. Fallback search:
   - If score too low, do keyword matching
   - Return results with keyword match scores

Requirements:
- Type hints
- Async
- Docstrings
- Return standardized result format
- Include confidence scores
```

---

### Session 1F: Database Layer (20 min)

**Prompt 7: SQLite database**
```
Create storage/db.py with database setup:

1. SQLAlchemy models:
   - Document: id, title, content, source_url, department, space, embedding (blob), timestamp
   - Conversation: id, user_id, agent_name, query, response, department, timestamp
   - Feedback: id, conversation_id, rating, comment, timestamp

2. async def init_db():
   - Create tables if not exist

3. async def save_document(doc: Dict):
   - Insert/update document in DB

4. async def save_conversation(user_id, agent, query, response, dept):
   - Log conversation

5. async def get_documents_by_dept(dept: str):
   - Retrieve documents for department

Requirements:
- Use SQLAlchemy (async support)
- SQLite file: knowledge_bot.db
- Proper typing
- Context manager support
```

---

## 📅 DAY 2: AGENTS + INTEGRATION (5 hours)

### Session 2A: Central Router Agent (30 min)

**Prompt 8: CentralRouterAgent implementation**
```
Create agents/central_router.py with CentralRouterAgent class:

Inherits from BaseAgent.

Key methods:

1. __init__(dept_agents: Dict[str, BaseAgent], llm_api_key: str, llm_url: str):
   - Store agents dict
   - Setup LLM client for Qwen 3.5 via AgentBase

2. async def process(message: Message) -> Message:
   Main flow:
   a) Call classify_intent(message.content) → {type: str, confidence: float}
      Types: "engineering", "product", "both", "other"
   
   b) Call detect_departments(intent_type) → List[str]
      Returns which departments can answer
   
   c) Route to agents:
      - For each department, call agent.process(message) in parallel
      - Use asyncio.gather() with timeout=10
      - Handle exceptions gracefully
   
   d) Call aggregate_responses(responses, message.metadata.get("role")) → str
      - Merge responses intelligently
      - Include all citations
      - Format for user role (engineer vs PM)
   
   e) Return Message with:
      - content: aggregated response
      - role: "assistant"
      - metadata: {departments: list, citations: list, confidence: float}

3. async def classify_intent(query: str) -> Dict:
   - Call Qwen 3.5 LLM to classify
   - Return {type, confidence}

4. async def detect_departments(intent_type: str) -> List[str]:
   - If "engineering" → ["engineering"]
   - If "product" → ["product"]
   - If "both" → ["engineering", "product"]
   - Otherwise → ["engineering", "product"] (search both)

5. async def aggregate_responses(responses: List[Message], user_role: str) -> str:
   - If no responses: return "No information found"
   - If 1 response: return as-is
   - If multiple: merge with context, call LLM for synthesis

Requirements:
- Type hints everywhere
- Proper async/await
- Error handling for agent timeouts
- Logging at key points
- Include citations in final response
- Docstrings for all methods
```

---

### Session 2B: Department Agents (40 min)

**Prompt 9: Engineering Agent**
```
Create agents/engineering_agent.py with EngineeringAgent class:

Inherits from BaseAgent.

Features:

1. __init__(retriever: HybridRetriever, confluence: ConfluenceClient, llm_config):
   - Store retriever, confluence, llm config
   - Set self.department = "engineering"
   - Load response style for engineers

2. async def process(message: Message) -> Message:
   Flow:
   a) Search knowledge base:
      results = await retriever.retrieve(message.content, "engineering", top_k=5)
   
   b) Check results:
      if not results or score < 0.3:
         return "No engineering info found"
   
   c) Format context from results
   
   d) Generate response:
      - Include technical depth
      - Reference code/architecture
      - Use engineering language
   
   e) Return Message with:
      - content: response text
      - metadata: {department: "engineering", citations: [...], confidence: score}

3. Response style for engineers:
   - Technical, detailed, code-focused
   - Reference implementation details
   - Mention edge cases

4. Citation extraction:
   - Extract from retriever results
   - Format as {title, url, section}

Requirements:
- Type hints
- Async throughout
- Error handling
- Proper logging
- Docstrings
- Response should reference Confluence links
```

**Prompt 10: Product Agent**
```
Create agents/product_agent.py with ProductAgent class:

Inherits from BaseAgent.
Similar structure to EngineeringAgent but:

1. __init__: set self.department = "product"

2. async def process: Search "product" space in Confluence

3. Response style for PMs:
   - Focus on features, timeline, business impact
   - Use product language (features, users, metrics)
   - Reference PRD documents
   - Mention dependencies and timeline

4. Everything else same as EngineeringAgent

Requirements:
- Type hints, async, docstrings
- Proper error handling
- Log all operations
```

---

### Session 2C: Agent Communication (20 min)

**Prompt 11: Enable agent-to-agent calls**
```
Add to both EngineeringAgent and ProductAgent:

When answering a complex question that needs another department:

In their process() method, add:

async def process(message: Message) -> Message:
    # ... existing search ...
    
    # If need cross-dept info:
    if needs_other_dept:
        other_agent = self.get_other_agent()
        other_response = await other_agent.process(message)
        # Incorporate other_response into final response
    
    # ... return aggregated response ...

Also add method:
    
    def get_other_agent(self) -> BaseAgent:
        # Return reference to other department agent
        # This will be set during initialization

Requirements:
- Support calling other agents directly
- Avoid infinite loops (track depth)
- Include both responses in final answer
- Maintain citations from both
```

---

### Session 2D: Teams Integration (30 min)

**Prompt 12: Teams webhook handler**
```
Create integrations/teams.py with TeamsHandler class:

Features:

1. __init__(bot_token: str, central_agent: CentralRouterAgent):
   - Store bot token
   - Store reference to central agent

2. async def handle_webhook(payload: Dict) -> Dict:
   - Extract from Teams payload:
     - message text
     - user_id, user_name
     - conversation_id
   - Get user context (department, role) from user_id
   - Create Message object
   - Call central_agent.process(message)
   - Format response for Teams
   - Return Teams response format

3. Response formatting:
   - Convert to Teams markdown
   - Include citations as links
   - Break long responses into multiple cards

4. async def send_message(recipient_id: str, text: str):
   - Call Teams Bot API to send message back
   - Include proper auth headers

5. Helper: parse_teams_payload(payload):
   - Extract message content, user info
   - Return structured dict

Requirements:
- Handle Teams activity types (message, conversationUpdate, etc)
- Extract clean message text
- Format citations as markdown links
- Support mentions and direct messages
- Proper error handling
- Logging
- Type hints everywhere
```

---

### Session 2E: FastAPI App (30 min)

**Prompt 13: Main application**
```
Create main.py with complete FastAPI application:

1. Setup:
   - Import everything
   - Load config
   - Setup logging
   - Create FastAPI(title="Zalopay Knowledge Bot")

2. Global variables (set in startup):
   - confluence_client: ConfluenceClient
   - vector_store: SimpleVectorStore
   - retriever: HybridRetriever
   - engineering_agent: EngineeringAgent
   - product_agent: ProductAgent
   - central_agent: CentralRouterAgent
   - teams_handler: TeamsHandler

3. @app.on_event("startup"):
   - Initialize all clients and agents
   - Load Confluence documents into vector store
   - Log startup completion

4. @app.on_event("shutdown"):
   - Call shutdown on all agents
   - Close clients

5. @app.get("/health"):
   - Return {"status": "healthy", "timestamp": now()}

6. @app.get("/agents/status"):
   - Return status of all agents
   - Memory sizes
   - Document count in vector store

7. @app.post("/chat"):
   - Query params: query (str), user_role (str, default="engineer")
   - Create Message
   - Call central_agent.process()
   - Return {response: str, citations: list, department: str}
   - Error handling with 500 responses

8. @app.post("/webhooks/teams"):
   - Receive Teams webhook payload
   - Call teams_handler.handle_webhook()
   - Return Teams response format
   - Handle Teams challenge requests

9. Error handlers:
   - Global exception handler
   - Log all errors
   - Return proper status codes

Requirements:
- All async
- Proper type hints
- Comprehensive logging
- Error handling
- CORS support (for testing)
- Docstrings
- Ready to run: python main.py
```

---

### Session 2F: Tests (20 min)

**Prompt 14: Test suite**
```
Create tests/test_agents.py with pytest tests:

1. test_central_router_classification:
   - Test that router correctly classifies engineering vs product queries
   - Mock retriever responses

2. test_engineering_agent_search:
   - Test engineering agent finds docs
   - Test response formatting

3. test_product_agent_search:
   - Test product agent finds docs
   - Test response formatting

4. test_agent_communication:
   - Test agents can call each other
   - Test response aggregation

5. test_message_flow:
   - Test full flow from query to response
   - Test citations are included

Requirements:
- Use pytest and pytest-asyncio
- Mock external API calls (Confluence, LLM)
- Test happy path and error cases
- Include fixtures for test data
```

**Prompt 15: Integration test**
```
Create tests/test_integration.py:

1. test_end_to_end_engineering_query:
   - Load test documents
   - Query about engineering
   - Verify response + citations

2. test_end_to_end_product_query:
   - Load test documents
   - Query about product
   - Verify response + citations

3. test_cross_department_query:
   - Query needs both departments
   - Verify both agents called
   - Verify aggregated response

Requirements:
- Use real vector store (not mock)
- Use real agents
- Test with sample Confluence documents
- Verify citations in responses
```

---

## 🚀 EXECUTION CHECKLIST

### Pre-coding
- [ ] Create empty directory: `zalopay-bot-mvp`
- [ ] Create requirements.txt (Prompt 1)
- [ ] Create .env.example (Prompt 1)
- [ ] Create config.py (Prompt 1)
- [ ] Create folder structure (Prompt 1)

### Day 1
- [ ] Prompt 2: BaseAgent
- [ ] Prompt 3: ConfluenceClient
- [ ] Prompt 4: EmbeddingGenerator
- [ ] Prompt 5: SimpleVectorStore
- [ ] Prompt 6: HybridRetriever
- [ ] Prompt 7: Database layer
- [ ] Test locally: `pip install -r requirements.txt && python -c "from agents.base import BaseAgent"`

### Day 2
- [ ] Prompt 8: CentralRouterAgent
- [ ] Prompt 9: EngineeringAgent
- [ ] Prompt 10: ProductAgent
- [ ] Prompt 11: Agent communication
- [ ] Prompt 12: Teams handler
- [ ] Prompt 13: Main FastAPI app
- [ ] Prompt 14: Agent tests
- [ ] Prompt 15: Integration tests
- [ ] Test: `pytest tests/ -v`
- [ ] Run: `python main.py`
- [ ] Test health: `curl http://localhost:8000/health`

### Validation
- [ ] /chat endpoint works
- [ ] Agents search Confluence
- [ ] Citations included
- [ ] Teams webhook works (if Teams setup)
- [ ] Tests passing

---

## 💡 TIPS FOR CLAUDE CODE

**When using Claude Code Opus 4.8:**

1. **Be specific** - Include exact method signatures
2. **Reference previous files** - "Like in base.py, but..."
3. **Ask for complete implementations** - Not snippets
4. **Request type hints** - "All parameters and returns typed"
5. **Test after each major component** - "Write test immediately after"
6. **Use clear structure** - "Separate concerns into methods"

**Progress check after each major component:**
```bash
# After Confluence integration
python -c "from integrations.confluence import ConfluenceClient; print('✅ Confluence imports')"

# After agents
python -c "from agents.central_router import CentralRouterAgent; print('✅ Agent imports')"

# After FastAPI app
python main.py &  # Should start without errors
curl http://localhost:8000/health
```

---

## ⏱️ TIME ALLOCATION (Total: 10 hours)

**Day 1 (5 hours):**
- 15 min: Boilerplate
- 30 min: BaseAgent (Prompt 2)
- 40 min: Confluence (Prompt 3)
- 40 min: Embeddings + Vector Store (Prompts 4-5)
- 20 min: Retriever (Prompt 6)
- 20 min: Database (Prompt 7)
- 15 min: Testing components

**Day 2 (5 hours):**
- 30 min: CentralRouter (Prompt 8)
- 40 min: Department Agents (Prompts 9-10)
- 20 min: Agent communication (Prompt 11)
- 30 min: Teams integration (Prompt 12)
- 30 min: FastAPI app (Prompt 13)
- 30 min: Tests (Prompts 14-15)
- 20 min: Integration testing + fixes

---

## ✅ SUCCESS CRITERIA

End of Day 2:
- ✅ `python main.py` runs without errors
- ✅ `/health` endpoint responds
- ✅ `/chat?query=...` returns answers with citations
- ✅ 2 agents communicate with each other
- ✅ `/webhooks/teams` receives messages
- ✅ All tests passing: `pytest tests/ -v`
- ✅ Code has type hints everywhere
- ✅ Logging shows what's happening
- ✅ Can demo to team (just show chat endpoint)
- ✅ Ready to extend to 20 departments

**DEMO COMMAND:**
```bash
# Terminal 1
python main.py

# Terminal 2
curl "http://localhost:8000/chat?query=How%20do%20we%20deploy%20services&user_role=engineer"
```

Response:
```json
{
  "response": "Based on our deployment guide... [detailed answer]",
  "citations": [
    {"title": "Deployment Guide", "url": "https://confluence.../..."}
  ],
  "department": "engineering",
  "confidence": 0.92
}
```

**That's your MVP working!** 🚀
