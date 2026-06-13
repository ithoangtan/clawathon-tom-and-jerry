# Zalopay Knowledge Agent - Implementation Roadmap

## 📅 Timeline Overview

```
Week 1 (Foundation)    │ Week 2 (Knowledge Sys) │ Week 3 (Multi-Agent)  │ Week 4 (Deploy + Ops)
Days 1-5               │ Days 6-10              │ Days 11-17            │ Days 18-20
Foundation + Testing   │ RAG + Indexing        │ Router + Sub-agents   │ Integration + PROD
```

---

## WEEK 1: FOUNDATION & INFRASTRUCTURE

### Day 1: Project Setup & Architecture

**Goals:**
- ✅ Create project structure
- ✅ Setup local development environment
- ✅ Initialize git repo + CI/CD pipelines
- ✅ Prepare Docker image templates

**Deliverables:**
```
1. Project initialized
   └─ repo structure (per COMPLETE_STRUCTURE.md)
   └─ all __init__.py files created
   └─ .gitignore, .env.example configured

2. Docker setup
   └─ Dockerfile.dev (local development)
   └─ Dockerfile (production)
   └─ docker-compose.yml (full stack: app + postgres + redis + weaviate)
   └─ .dockerignore optimized

3. CI/CD Pipeline
   └─ .gitlab-ci.yml (if using GitLab)
   └─ Stages: lint → test → build → push → deploy-staging

4. Base dependencies
   └─ requirements.txt (updated with all libs)
   └─ pyproject.toml configured
   └─ pip install successful locally

5. Documentation
   └─ README.md (how to run locally)
   └─ SETUP.md (step-by-step setup)
   └─ ARCHITECTURE.md (technical overview)
```

**Commands to Run:**
```bash
# Clone repo + setup
git clone <your-repo>
cd agent-base-repo
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start local environment
docker-compose up -d

# Verify
curl http://localhost:8000/health
```

---

### Day 2-3: Core Agent Classes & Framework

**Goals:**
- ✅ Implement BaseAgent class (abstract + concrete)
- ✅ Implement BaseIntegration class
- ✅ Create Message protocol
- ✅ Build AgentOrchestrator

**Deliverables:**

```python
# src/agents/base.py
class BaseAgent(ABC):
    async def process(message: Message) -> Message: pass
    async def initialize() -> None: pass
    async def shutdown() -> None: pass
    
class AgentOrchestrator:
    async def process(message: Message) -> Message: pass
    # Routes to primary/secondary agents

# src/integrations/base.py
class BaseIntegration(ABC):
    async def connect() -> bool: pass
    async def send_message() -> bool: pass
    async def handle_webhook() -> bool: pass

class IntegrationManager:
    async def route_message() -> bool: pass
```

**Test Coverage:**
```
tests/test_agents/test_base_agent.py
├─ test_message_creation()
├─ test_agent_initialization()
├─ test_agent_processing()
├─ test_error_handling()
└─ test_memory_management()

tests/test_integrations/test_base_integration.py
├─ test_integration_connect()
├─ test_message_routing()
├─ test_webhook_handling()
└─ test_manager_registration()
```

---

### Day 4: Configuration & Settings

**Goals:**
- ✅ Pydantic settings with nested configs
- ✅ YAML config loaders
- ✅ Environment variable management
- ✅ Secrets management

**Deliverables:**

```python
# config/settings.py - Complete implementation
from pydantic_settings import BaseSettings

class RAGSettings(BaseSettings):
    vector_db_type: str = "weaviate"
    weaviate_url: str
    embedding_model: str = "all-MiniLM-L6-v2"
    chunk_size: int = 300
    # ...

class LLMSettings(BaseSettings):
    default_model: str = "qwen-3.5"
    agentbase_api_key: str  # from env
    qwen_endpoint: str = "https://agentbase.zalopay.com/models/qwen"
    # ...

class Settings(BaseSettings):
    database: DatabaseSettings
    redis: RedisSettings
    rag: RAGSettings
    llm: LLMSettings
    integrations: IntegrationSettings
    # ...

# config/agents_config.yaml - 20 departments
agents:
  primary:
    name: "Zalopay Knowledge Router"
    model: "qwen-3.5"
  secondary:
    engineering: {...}
    product: {...}
    ops: {...}
    # ... 17 more departments
```

**Files to Create:**
```
config/
├─ settings.py                    # Pydantic models ✅
├─ agents_config.yaml            # Department configs
├─ models_config.yaml            # Model endpoints
├─ integrations_config.yaml       # Platform credentials
├─ rag_config.yaml               # Vector DB + embedding
├─ .env.example                  # Template
└─ __init__.py
```

---

### Day 5: Logging, Monitoring & Local Testing

**Goals:**
- ✅ Structured logging setup
- ✅ Basic health checks
- ✅ Local dev environment validation
- ✅ Docker Compose fully working

**Deliverables:**

```python
# src/utils/logger.py
def setup_logging(level: str = "INFO"):
    # Structured JSON logging
    # File + console outputs
    # Separate log levels per module

# src/main.py - FastAPI app with:
@app.get("/health")
async def health(): return {"status": "healthy"}

@app.get("/status")
async def status(): return {"agents": "ready", ...}

# src/api/routes.py - Basic endpoints:
@router.post("/chat")
async def chat(message: str): pass

@router.get("/agents/status")
async def agent_status(): pass
```

**Testing:**
```bash
# Run local
make dev

# In another terminal
curl http://localhost:8000/health
curl http://localhost:8000/status

# Run unit tests
pytest tests/ -v

# Check Docker Compose
docker-compose logs -f app
docker-compose ps  # All services up
```

**By End of Day 5:**
- ✅ Project runs locally without errors
- ✅ Docker Compose starts all services
- ✅ Logging works + captures all events
- ✅ Health checks passing
- ✅ Ready for Week 2

---

## WEEK 2: KNOWLEDGE SYSTEM & RAG PIPELINE

### Day 6-7: Confluence Integration

**Goals:**
- ✅ Implement Confluence API client
- ✅ Batch sync logic
- ✅ Incremental updates
- ✅ Error handling + retry

**Deliverables:**

```python
# src/integrations/confluence/handler.py
class ConfluenceHandler(BaseIntegration):
    async def fetch_all_pages(space: str) -> List[Page]:
        # Get all pages + metadata from Confluence
        # Filter by modified_after timestamp (incremental)
        # Handle pagination (50 pages/request)
        # Retry with exponential backoff
    
    async def parse_page(page_id: str) -> Document:
        # Extract text content
        # Preserve formatting
        # Store metadata (author, modified_date, section structure)
        # Get URL for citation links

    async def fetch_changes(last_sync_time: datetime) -> List[Document]:
        # Incremental: only changed pages
        # More efficient than full refresh

# src/rag/document_loader.py
class ConfluenceLoader:
    async def load(space_key: str) -> List[Document]:
        # Use ConfluenceHandler to get pages
        # Standardize document format
        # Add metadata

class DocumentProcessor:
    def classify(doc: Document) -> DocType:
        # Detect: Org / PRD / TechDoc / RCA / Ops
        # Use pattern matching + ML if needed
```

**Configuration:**
```yaml
# config/integrations_config.yaml
confluence:
  enabled: true
  api_url: "https://zalopay.atlassian.net/wiki"
  auth_token: "${CONFLUENCE_API_TOKEN}"  # Service account
  spaces: ["ENG", "PRODUCT", "OPS", ...]  # All 20 dept spaces
  fetch_interval: "daily"
  retry_count: 5
  timeout: 60  # seconds
```

**Testing:**
```python
# tests/test_integrations/test_confluence.py
async def test_fetch_pages():
    handler = ConfluenceHandler(config)
    pages = await handler.fetch_all_pages("ENG")
    assert len(pages) > 0
    assert pages[0].content is not None

async def test_incremental_sync():
    # Only new/modified pages fetched
    changes = await handler.fetch_changes(last_sync_time)
    assert all(p.modified_at >= last_sync_time for p in changes)
```

---

### Day 8: Weaviate Setup & Vector Indexing

**Goals:**
- ✅ Weaviate cluster running (3 nodes)
- ✅ Schema creation (per department)
- ✅ Vector indexing pipeline
- ✅ Semantic search working

**Deliverables:**

```python
# src/rag/vector_store.py
class WeaviateVectorStore:
    def __init__(self, url: str = "http://localhost:8080"):
        self.client = weaviate.Client(url)
    
    async def create_schema(department: str):
        # Create collection per department
        schema = {
            "class": f"Document_{department}",
            "properties": [
                {"name": "content", "dataType": ["text"]},
                {"name": "source_url", "dataType": ["text"]},
                {"name": "doc_type", "dataType": ["text"]},
                {"name": "section", "dataType": ["text"]},
                {"name": "modified_at", "dataType": ["date"]},
                {"name": "department", "dataType": ["text"]},
            ],
            "vectorizer": "text2vec-transformers",
            "moduleConfig": {
                "text2vec-transformers": {
                    "poolingStrategy": "masked_mean",
                }
            }
        }
        self.client.schema.create_class(schema)
    
    async def add_document(doc: Document) -> str:
        # Generate embedding (local model)
        # Store in Weaviate
        return doc_uuid
    
    async def search(query: str, department: str, top_k: int = 5):
        # Hybrid search (vector + BM25)
        # Return top_k results with scores

# src/rag/embeddings.py
class EmbeddingGenerator:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
    
    def embed(self, text: str) -> List[float]:
        # Generate embedding locally
        # Fast + free
        return self.model.encode(text).tolist()
```

**Docker Compose Update:**
```yaml
weaviate:
  image: semitechnologies/weaviate:latest
  environment:
    QUERY_DEFAULTS_LIMIT: 25
    AUTHENTICATION_APIKEY_ENABLED: 'false'
  volumes:
    - weaviate_data:/var/lib/weaviate
  ports:
    - "8080:8080"
```

**Testing:**
```python
# tests/test_rag/test_vector_store.py
async def test_add_and_search():
    store = WeaviateVectorStore()
    await store.create_schema("ENG")
    
    doc = Document(content="Python code best practices", ...)
    doc_id = await store.add_document(doc)
    
    results = await store.search("Python tips", "ENG", top_k=5)
    assert len(results) > 0
    assert results[0]['score'] > 0.7
```

---

### Day 9: Document Chunking & Batch Indexing

**Goals:**
- ✅ Smart text chunking (300 tokens)
- ✅ Metadata preservation
- ✅ Batch indexing pipeline
- ✅ Duplicate detection

**Deliverables:**

```python
# src/rag/chunker.py
class SemanticChunker:
    def chunk(self, text: str, chunk_size: int = 300, overlap: int = 50):
        # Split by sentences/paragraphs (semantic aware)
        # Maintain context with overlap
        # Preserve metadata (section, paragraph num)
        chunks = []
        for i, chunk in enumerate(semantic_split(text, chunk_size, overlap)):
            chunks.append({
                "content": chunk,
                "chunk_index": i,
                "token_count": count_tokens(chunk)
            })
        return chunks

# src/rag/pipeline.py
class RAGPipeline:
    async def ingest_documents(docs: List[Document], department: str):
        for doc in docs:
            # 1. Chunk document
            chunks = self.chunker.chunk(doc.content)
            
            # 2. Generate embeddings (batch)
            embeddings = await self.embedding_gen.embed_batch(
                [c["content"] for c in chunks]
            )
            
            # 3. Check for duplicates
            for chunk, embedding in zip(chunks, embeddings):
                if not await self.duplicate_check(embedding, department):
                    # 4. Store in Weaviate
                    await self.vector_store.add_document({
                        "content": chunk["content"],
                        "source_url": doc.url,
                        "doc_type": doc.doc_type,
                        "section": chunk.get("section"),
                        "modified_at": doc.modified_at,
                        "department": department,
                        "embedding": embedding,
                    })
            
            # 5. Log to audit trail
            logger.info(f"Indexed {len(chunks)} chunks from {doc.title}")

    async def batch_sync(self, force: bool = False):
        # Daily batch processing (end-of-day)
        for dept in self.get_all_departments():
            # Fetch changes from Confluence
            new_docs = await self.confluence.fetch_changes(
                last_sync_time=self.get_last_sync(dept)
            )
            
            # Ingest
            await self.ingest_documents(new_docs, dept)
            
            # Update last_sync_time
            self.set_last_sync(dept, datetime.now())
```

**Scheduler:**
```python
# src/main.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

@app.on_event("startup")
async def startup():
    # Schedule daily sync at 22:00 UTC
    scheduler.add_job(
        pipeline.batch_sync,
        trigger="cron",
        hour=22,
        minute=0,
        id="daily-batch-sync"
    )
    scheduler.start()
```

---

### Day 10: Search & Retrieval Optimization

**Goals:**
- ✅ Hybrid search (vector + keyword)
- ✅ Reranking for relevance
- ✅ Citation extraction
- ✅ Performance benchmarking

**Deliverables:**

```python
# src/rag/retriever.py
class HybridRetriever:
    async def retrieve(self, query: str, department: str, top_k: int = 5):
        # 1. Vector search
        vector_results = await self.vector_store.search(
            query=query,
            department=department,
            top_k=top_k*2  # Get more to rerank
        )
        
        # 2. Keyword search (BM25)
        keyword_results = await self.vector_store.bm25_search(
            query=query,
            department=department,
            top_k=top_k*2
        )
        
        # 3. Merge + deduplicate
        merged = self.merge_results(vector_results, keyword_results)
        
        # 4. Rerank by relevance
        reranked = self.rerank(query, merged, top_k)
        
        # 5. Extract citations
        for result in reranked:
            result["citation"] = self.extract_citation(result)
        
        return reranked
    
    def extract_citation(self, doc: Document) -> Citation:
        return Citation(
            title=doc.title,
            url=doc.url,
            section=doc.section,
            modified_at=doc.modified_at
        )

# src/rag/reranker.py
class Reranker:
    def rerank(self, query: str, candidates: List[Document], top_k: int):
        # Use cross-encoder for fine-grained ranking
        scores = self.model.predict([[query, doc.content] for doc in candidates])
        ranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
        return [doc for doc, score in ranked[:top_k]]
```

**Caching for Performance:**
```python
# src/storage/cache.py
class QueryCache:
    async def get(self, query: str, department: str):
        key = f"search:{department}:{hash(query)}"
        return await self.redis.get(key)
    
    async def set(self, query: str, department: str, results: List, ttl: int = 3600):
        key = f"search:{department}:{hash(query)}"
        await self.redis.setex(key, ttl, json.dumps(results))

# Usage in retriever
async def retrieve(self, query: str, department: str, top_k: int = 5):
    # Check cache first
    cached = await self.cache.get(query, department)
    if cached:
        return json.loads(cached)
    
    # If not cached, do full retrieval
    results = await self._do_retrieve(query, department, top_k)
    
    # Cache for next time
    await self.cache.set(query, department, results)
    
    return results
```

**By End of Day 10:**
- ✅ All documents indexed in Weaviate
- ✅ Search working (semantic + keyword)
- ✅ Citations linking to Confluence
- ✅ Caching reducing latency
- ✅ Batch sync scheduled daily
- ✅ Ready for multi-agent system

---

## WEEK 3: MULTI-AGENT SYSTEM

### Day 11: Central Router Agent

**Goals:**
- ✅ Implement central router (1 agent)
- ✅ Query classification
- ✅ Department detection
- ✅ Intent understanding

**Deliverables:**

```python
# src/agents/primary/agent.py
class CentralRouterAgent(BaseAgent):
    """
    Routes queries to appropriate department agents.
    Handles multi-department queries.
    Aggregates responses.
    """
    
    def __init__(self, config: AgentConfig, retriever: HybridRetriever):
        super().__init__(config)
        self.retriever = retriever
        self.llm = LLMManager(model="qwen-3.5")
    
    async def process(self, message: Message) -> Message:
        """
        1. Classify query type
        2. Detect departments needed
        3. Route to sub-agents
        4. Aggregate responses
        """
        user_id = message.metadata.get("user_id")
        user_department = message.metadata.get("department")
        user_role = message.metadata.get("role")
        
        # Step 1: Classify query
        classification = await self.classify_query(message.content)
        # Returns: {"type": "technical|business|operational|...", "confidence": 0.95}
        
        # Step 2: Detect required departments
        required_depts = await self.detect_departments(
            message.content,
            classification
        )
        # Returns: ["ENG", "OPS"] or ["PRODUCT"]
        
        # Step 3: Check access control
        if not self.can_access(user_department, required_depts):
            return Message(
                content="You don't have permission to query these departments",
                role="assistant"
            )
        
        # Step 4: Route to sub-agents
        sub_responses = await self.route_to_agents(
            message=message,
            departments=required_depts,
            timeout=30  # seconds
        )
        
        # Step 5: Aggregate + format response
        final_response = await self.aggregate_responses(
            sub_responses=sub_responses,
            user_role=user_role,
            query=message.content
        )
        
        # Step 6: Add to memory
        await self.add_to_memory(message)
        await self.add_to_memory(final_response)
        
        return final_response
    
    async def classify_query(self, query: str) -> Dict:
        """Use LLM to classify query type"""
        prompt = f"""
        Classify this query into one category:
        - technical (code, architecture, implementation)
        - product (features, roadmap, requirements)
        - operational (procedures, runbooks, troubleshooting)
        - business (metrics, KPIs, strategy)
        - compliance (risk, security, regulations)
        - organizational (structure, teams, contacts)
        - other
        
        Query: {query}
        
        Respond JSON: {{"type": "...", "confidence": 0.X}}
        """
        
        response = await self.llm.generate(prompt)
        return json.loads(response)
    
    async def detect_departments(self, query: str, classification: Dict) -> List[str]:
        """Detect which departments can answer this"""
        # Search metadata across all departments
        # Return departments with relevant documents
        
        docs_by_dept = {}
        for dept in self.get_all_departments():
            relevant = await self.retriever.retrieve(
                query=query,
                department=dept,
                top_k=3
            )
            if relevant and relevant[0]['score'] > 0.5:
                docs_by_dept[dept] = relevant
        
        return list(docs_by_dept.keys())
    
    async def route_to_agents(self, message: Message, departments: List[str], timeout: int):
        """Route to department agents in parallel"""
        tasks = [
            self.get_department_agent(dept).process(message)
            for dept in departments
        ]
        
        responses = await asyncio.wait_for(
            asyncio.gather(*tasks, return_exceptions=True),
            timeout=timeout
        )
        
        return responses
    
    async def aggregate_responses(self, sub_responses: List[Message], user_role: str, query: str):
        """Merge responses from multiple departments"""
        if len(sub_responses) == 0:
            return Message(
                content="No information found",
                role="assistant"
            )
        
        if len(sub_responses) == 1:
            return sub_responses[0]
        
        # Multiple responses - merge with context
        prompt = f"""
        Merge these responses into a cohesive answer for a {user_role}:
        
        Query: {query}
        
        Responses:
        {chr(10).join([f"- {r.content}" for r in sub_responses])}
        
        Create a unified response that:
        1. Answers the query directly
        2. Includes all relevant information
        3. Preserves citations
        4. Is concise and organized
        """
        
        merged = await self.llm.generate(prompt)
        return Message(
            content=merged,
            role="assistant",
            metadata={"merged_from_depts": len(sub_responses)}
        )
```

**Configuration:**
```yaml
# config/agents_config.yaml
primary_agent:
  name: "Zalopay Knowledge Router"
  type: "primary"
  description: "Central router for all queries"
  model: "qwen-3.5"
  enable_rag: true
  enable_memory: true
  timeout: 30
  max_concurrent: 100
```

---

### Day 12-14: 20 Department Sub-Agents

**Goals:**
- ✅ Create DepartmentAgent base class
- ✅ Implement 20 sub-agents (one per department)
- ✅ Response personalization per department
- ✅ Cross-department communication

**Deliverables:**

```python
# src/agents/secondary/department_agent.py
class DepartmentAgent(BaseAgent):
    """
    Handles queries for a specific department.
    Knows department-specific knowledge, tools, and response styles.
    Can communicate with other departments if needed.
    """
    
    def __init__(self, config: AgentConfig, department: str):
        super().__init__(config)
        self.department = department
        self.retriever = HybridRetriever()
        self.llm = LLMManager(model=config.model)
        self.response_style = self.load_response_style(department)
    
    async def process(self, message: Message) -> Message:
        """
        Answer a question specific to this department
        """
        user_role = message.metadata.get("role")  # Engineer, PM, etc
        
        # Step 1: Search own knowledge base
        search_results = await self.retriever.retrieve(
            query=message.content,
            department=self.department,
            top_k=5
        )
        
        if not search_results or search_results[0]['score'] < 0.5:
            return Message(
                content=f"No information found in {self.department} knowledge base",
                role="assistant",
                metadata={"department": self.department, "found": False}
            )
        
        # Step 2: Format context for LLM
        context = self.format_context(search_results)
        
        # Step 3: Generate response with department knowledge
        response_text = await self.generate_response(
            query=message.content,
            context=context,
            user_role=user_role
        )
        
        # Step 4: Add citations
        citations = self.extract_citations(search_results)
        
        # Step 5: Return with metadata
        return Message(
            content=response_text,
            role="assistant",
            metadata={
                "department": self.department,
                "citations": citations,
                "confidence": search_results[0]['score'],
                "sources": len(search_results)
            }
        )
    
    async def generate_response(self, query: str, context: str, user_role: str) -> str:
        """Generate response personalized for user role"""
        
        style_prompt = self.response_style.get(user_role, self.response_style["default"])
        
        prompt = f"""
        You are a {self.department} department expert at Zalopay.
        
        Response guidelines for {user_role}:
        {style_prompt}
        
        Context from knowledge base:
        {context}
        
        User question: {query}
        
        Provide a helpful, accurate answer based on the context.
        If you don't know, say "I don't have enough information".
        """
        
        return await self.llm.generate(prompt)
    
    def load_response_style(self, department: str) -> Dict[str, str]:
        """Load response styles for different roles"""
        return {
            "engineer": """
                - Be technical, include code examples
                - Discuss implementation details
                - Reference GitLab repos
                - Mention edge cases and performance considerations
            """,
            "product_manager": """
                - Focus on features and timeline
                - Discuss business impact
                - Reference PRD documents
                - Be strategic and high-level
            """,
            "operator": """
                - Provide step-by-step procedures
                - Include runbook links
                - Mention troubleshooting tips
                - Be practical and actionable
            """,
            "compliance": """
                - Highlight risks and requirements
                - Reference compliance docs
                - Mention regulatory implications
                - Be cautious about edge cases
            """,
            "default": """
                - Be clear and concise
                - Provide relevant context
                - Include links to more information
                - Ask for clarification if needed
            """
        }
```

**Department Agents to Create (20 total):**
```
Engineering/Platform    └─ EngineeringAgent
Product & Design       └─ ProductAgent
Operations & SRE       └─ OpsAgent
Finance & Accounting   └─ FinanceAgent
Risk & Compliance      └─ ComplianceAgent
HR & People           └─ HRAgent
Marketing & Growth    └─ MarketingAgent
Sales & Partnerships  └─ SalesAgent
Customer Support      └─ SupportAgent
Legal                 └─ LegalAgent
Business Development  └─ BizDevAgent
DevOps & Infrastructure └─ DevOpsAgent
Data & Analytics      └─ DataAgent
Security             └─ SecurityAgent
QA & Testing         └─ QAAgent
Design Systems       └─ DesignAgent
... (4 more departments)
```

**Each implemented as:**
```python
# src/agents/secondary/engineering/agent.py
class EngineeringAgent(DepartmentAgent):
    def __init__(self, config: AgentConfig):
        super().__init__(config, department="ENG")
        self.tools = ["code_search", "architecture_diagram", "deployment_guide"]

# src/agents/secondary/product/agent.py
class ProductAgent(DepartmentAgent):
    def __init__(self, config: AgentConfig):
        super().__init__(config, department="PRODUCT")
        self.tools = ["feature_tracking", "roadmap_view", "user_feedback"]

# ... repeat for all 20
```

**Testing:**
```python
# tests/test_agents/test_department_agents.py
@pytest.mark.asyncio
async def test_engineering_agent():
    agent = EngineeringAgent(config)
    await agent.initialize()
    
    message = Message(
        content="How do we deploy the payment service?",
        metadata={"user_id": "eng1", "role": "engineer"}
    )
    
    response = await agent.process(message)
    assert response.role == "assistant"
    assert len(response.metadata["citations"]) > 0
    assert response.metadata["confidence"] > 0.5

@pytest.mark.asyncio
async def test_cross_department_query():
    # Product + Engineering
    router = CentralRouterAgent(config)
    message = Message(
        content="What's the payment feature status and tech implementation?",
        metadata={"role": "product_manager"}
    )
    response = await router.process(message)
    assert "PRODUCT" in response.metadata
    assert "ENG" in response.metadata
```

---

### Day 15: Response Learning & Feedback Loop

**Goals:**
- ✅ Capture user feedback on responses
- ✅ Store patterns in PostgreSQL
- ✅ Dynamically update response styles
- ✅ Improve over time (in-context learning)

**Deliverables:**

```python
# src/storage/schemas.py
from sqlalchemy import Column, String, Float, DateTime, JSON, Integer
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class QueryFeedback(Base):
    __tablename__ = "query_feedback"
    
    id = Column(Integer, primary_key=True)
    query_id = Column(String, unique=True)
    user_id = Column(String)
    query_text = Column(String)
    response_text = Column(String)
    department = Column(String)
    user_role = Column(String)
    
    rating = Column(Integer)  # 1-5
    feedback_type = Column(String)  # helpful, not_helpful, partial
    user_comment = Column(String, nullable=True)
    edited_response = Column(String, nullable=True)  # User's correction
    
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

class ResponsePattern(Base):
    __tablename__ = "response_patterns"
    
    id = Column(Integer, primary_key=True)
    department = Column(String)
    user_role = Column(String)
    pattern_type = Column(String)  # style_preference, missing_info, etc
    pattern_data = Column(JSON)  # {example_query, example_response, improvement}
    frequency = Column(Integer)  # How often observed
    success_rate = Column(Float)  # % of positive feedback
    
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

# src/storage/repositories.py
class FeedbackRepository:
    async def save_feedback(self, feedback: QueryFeedback):
        session.add(feedback)
        await session.commit()
    
    async def get_patterns_for_role(self, department: str, role: str):
        # Get successful patterns for this role + dept combination
        patterns = await session.query(ResponsePattern).filter(
            ResponsePattern.department == department,
            ResponsePattern.user_role == role,
            ResponsePattern.success_rate >= 0.8  # High success
        ).all()
        return patterns

# src/agents/secondary/department_agent.py
class DepartmentAgent(BaseAgent):
    async def process(self, message: Message) -> Message:
        # ... existing code ...
        response = await self.generate_response(...)
        
        # Attach feedback mechanism
        response.metadata["feedback_id"] = str(uuid.uuid4())
        
        return response

# src/api/routes.py
@router.post("/feedback/{feedback_id}")
async def submit_feedback(feedback_id: str, rating: int, comment: str = None):
    """
    User submits feedback on agent response.
    System learns from patterns.
    """
    feedback = QueryFeedback(
        query_id=feedback_id,
        user_id=get_current_user().id,
        rating=rating,
        user_comment=comment
    )
    
    await feedback_repo.save_feedback(feedback)
    
    # Extract patterns if high volume of same feedback
    await learning_system.update_patterns(feedback)
    
    return {"status": "feedback_received"}
```

**Continuous Learning:**
```python
# src/agents/learning_system.py
class ContinuousLearner:
    async def update_patterns(self, feedback: QueryFeedback):
        """
        If 10+ similar queries get same positive feedback,
        Update the response style for that role + department combination.
        """
        
        similar_feedbacks = await self.find_similar_feedbacks(feedback)
        
        if len(similar_feedbacks) >= 10:
            # Calculate common successful pattern
            pattern = await self.extract_common_pattern(similar_feedbacks)
            
            # Update response style in memory
            await self.update_agent_style(
                department=feedback.department,
                role=feedback.user_role,
                pattern=pattern
            )
            
            logger.info(f"Learned new pattern for {feedback.department}/{feedback.user_role}")
```

---

### Day 16-17: Integrations & User Interfaces

**Goals:**
- ✅ Teams Bot connector
- ✅ Web Dashboard API
- ✅ Message routing
- ✅ Session management

**Deliverables:**

**Teams Bot:**
```python
# src/integrations/teams/handler.py
class TeamsHandler(BaseIntegration):
    async def handle_webhook(self, payload: Dict):
        """
        Handle incoming Teams message.
        Route to appropriate agent.
        Send response back to Teams.
        """
        
        activity = Activity.deserialize(payload)
        
        if activity.type == "message":
            # Extract message
            query = activity.text
            user_id = activity.from_property.id
            user_name = activity.from_property.name
            
            # Get user context (department, role)
            user_context = await self.get_user_context(user_id)
            
            # Create message for agent
            message = Message(
                content=query,
                metadata={
                    "user_id": user_id,
                    "user_name": user_name,
                    "department": user_context["department"],
                    "role": user_context["role"],
                    "source": "teams",
                    "activity_id": activity.id
                }
            )
            
            # Route to central agent
            response = await self.central_agent.process(message)
            
            # Send back to Teams (with citations)
            await self.send_message(
                recipient_id=user_id,
                message=self.format_response(response)
            )
    
    def format_response(self, response: Message) -> str:
        """Format for Teams (markdown + cards)"""
        text = response.content + "\n\n"
        
        if response.metadata.get("citations"):
            text += "**Sources:**\n"
            for citation in response.metadata["citations"]:
                text += f"- [{citation['title']}]({citation['url']})\n"
        
        return text
    
    async def send_message(self, recipient_id: str, message: str):
        """Send Teams message"""
        activity = Activity(
            type="message",
            from_property=ChannelAccount(id="bot", name="Knowledge Bot"),
            recipient=ChannelAccount(id=recipient_id),
            conversation=ConversationAccount(id=recipient_id),
            text=message
        )
        
        await self.connector.send_message(activity)
```

**Web Dashboard API:**
```python
# src/api/routes.py
@router.get("/chat")
async def web_chat(query: str, department: str = None, role: str = None):
    """Web interface to query bot"""
    
    user = get_current_user()
    
    message = Message(
        content=query,
        metadata={
            "user_id": user.id,
            "department": department or user.department,
            "role": role or user.role,
            "source": "web"
        }
    )
    
    response = await central_agent.process(message)
    
    return {
        "response": response.content,
        "citations": response.metadata.get("citations"),
        "department": response.metadata.get("department"),
        "confidence": response.metadata.get("confidence")
    }

@router.get("/departments")
async def list_departments():
    """List all available departments"""
    return [
        {"code": "ENG", "name": "Engineering"},
        {"code": "PRODUCT", "name": "Product"},
        # ... all 20
    ]

@router.get("/agents/status")
async def agent_status():
    """Get status of all agents"""
    return {
        "central_router": await central_agent.get_status(),
        "departments": {
            dept: await agent.get_status()
            for dept, agent in dept_agents.items()
        }
    }
```

---

### Day 18: Security & Compliance

**Goals:**
- ✅ RBAC implementation
- ✅ Audit logging
- ✅ PII detection & masking
- ✅ Rate limiting

**Deliverables:**

```python
# src/api/middleware.py
from fastapi import Request, HTTPException
from functools import wraps

class SecurityMiddleware:
    async def __call__(self, request: Request, call_next):
        # 1. Authenticate user
        token = request.headers.get("Authorization")
        user = await self.verify_token(token)
        
        if not user:
            raise HTTPException(status_code=401)
        
        request.state.user = user
        
        # 2. Check rate limits
        if await self.is_rate_limited(user.id):
            raise HTTPException(status_code=429, detail="Too many requests")
        
        # 3. Log request
        await self.audit_log(user, request)
        
        response = await call_next(request)
        return response

# src/utils/pii_detector.py
class PIIDetector:
    def __init__(self):
        self.patterns = {
            "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
            "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
            "credit_card": r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"
        }
    
    def detect(self, text: str) -> List[Dict]:
        """Detect PII in text"""
        findings = []
        for pii_type, pattern in self.patterns.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                findings.append({
                    "type": pii_type,
                    "value": match.group(),
                    "position": match.start()
                })
        return findings
    
    def mask(self, text: str) -> str:
        """Mask detected PII"""
        findings = self.detect(text)
        for finding in sorted(findings, key=lambda x: x["position"], reverse=True):
            pii_type = finding["type"]
            # Replace with mask
            if pii_type == "email":
                mask = "***@***.***"
            elif pii_type == "phone":
                mask = "***-****"
            else:
                mask = "*" * len(finding["value"])
            
            text = text[:finding["position"]] + mask + text[finding["position"] + len(finding["value"]):]
        
        return text

# src/storage/audit.py
class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String)
    action = Column(String)  # query, feedback, admin_action
    resource = Column(String)  # department, agent
    query_text = Column(String)
    response_text = Column(String)
    department = Column(String)
    status = Column(String)  # success, denied, error
    timestamp = Column(DateTime, default=datetime.now)

class AuditService:
    async def log_action(self, user_id: str, action: str, details: Dict):
        log = AuditLog(
            user_id=user_id,
            action=action,
            **details
        )
        session.add(log)
        await session.commit()
```

---

## WEEK 4: DEPLOYMENT & OPERATIONS

### Day 19: Production Deployment Setup

**Goals:**
- ✅ Docker image build optimized
- ✅ AgentBase deployment configured
- ✅ Staging validation
- ✅ Monitoring setup

**Deliverables:**

```bash
# Build Docker image
docker build -f docker/Dockerfile -t myregistry/zalopay-kb:v1.0 .

# Push to registry
docker push myregistry/zalopay-kb:v1.0

# Deploy via AgentBase CLI
/agentbase-deploy build \
  --dockerfile docker/Dockerfile \
  --image myregistry/zalopay-kb:v1.0

/agentbase-deploy deploy \
  --runtime-name zalopay-kb-prod \
  --image myregistry/zalopay-kb:v1.0 \
  --scale 5 \
  --flavor standard
```

**Monitoring Stack:**
```yaml
# docker-compose.prod.yml includes
prometheus:
  image: prom/prometheus
  volumes:
    - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
  ports:
    - "9090:9090"

grafana:
  image: grafana/grafana
  ports:
    - "3000:3000"
  environment:
    - GF_SECURITY_ADMIN_PASSWORD=admin

elasticsearch:
  image: elasticsearch:8.0
  environment:
    - discovery.type=single-node
  ports:
    - "9200:9200"

kibana:
  image: kibana:8.0
  ports:
    - "5601:5601"
```

### Day 20: Launch & Handover

**Goals:**
- ✅ Final testing in production
- ✅ Team training
- ✅ Documentation complete
- ✅ On-call support setup

**Deliverables:**
```
Final Checklist:
✅ All 20 department agents active
✅ Confluence fully synced
✅ Teams bots deployed
✅ Web dashboard live
✅ Monitoring dashboards showing
✅ Logging centralized
✅ Disaster recovery tested
✅ Team trained on operation
✅ Documentation published
✅ Support SOP in place
```

---

## 📊 DELIVERABLES BY PHASE

### Phase 1 Deliverables (Week 1)
```
✅ Project structure created
✅ Docker Compose fully working (app + DB + cache + vector DB)
✅ Base agent + integration classes
✅ Settings + configuration management
✅ Logging + health checks
✅ Basic API endpoints
✅ Unit tests running
```

### Phase 2 Deliverables (Week 2)
```
✅ Confluence integration (fetch + sync)
✅ Weaviate vector DB setup (3 nodes, HA)
✅ Document chunking + embedding pipeline
✅ Batch sync scheduler (daily end-of-day)
✅ Hybrid search (vector + keyword)
✅ Citation extraction
✅ Query caching (Redis)
✅ Integration tests passing
✅ 500K-2M documents indexed
```

### Phase 3 Deliverables (Week 3)
```
✅ Central router agent (1)
✅ Department sub-agents (20)
✅ Agent communication protocol
✅ Response aggregation
✅ Response personalization (5 roles)
✅ Feedback collection + learning loop
✅ Teams bot integration
✅ Web dashboard API
✅ End-to-end testing
```

### Phase 4 Deliverables (Week 4)
```
✅ Security hardening (RBAC, PII masking, audit logs)
✅ Production Docker image
✅ AgentBase deployment
✅ Monitoring (Prometheus + Grafana + ELK)
✅ Alerting configured
✅ Load testing passed (10 req/s)
✅ Documentation complete
✅ Team trained
✅ PROD launch
```

---

## 🎯 SUCCESS CRITERIA

By end of Week 4:

```
Functional Requirements:
✅ Can answer questions from any of 20 departments
✅ Always cites Confluence sources
✅ Handles multi-department queries
✅ Learns from user feedback
✅ Supports 5+ user roles with personalized responses
✅ Concurrent users supported
✅ Response time < 30 seconds typical

Non-Functional:
✅ Uptime 99.9% or higher
✅ Supports 10 req/s (scalable beyond)
✅ Cost ~$1400/month (infrastructure)
✅ No vendor lock-in (self-hosted)
✅ Enterprise security (PCI-DSS ready)
✅ Audit trail for all actions
✅ Disaster recovery ready

Business:
✅ Reduces support queries by ~60%
✅ Team adoption > 80% in first month
✅ User satisfaction > 4/5 stars
✅ Can onboard new departments in <1 day
```

---

## 📝 NOTES

- Each phase builds on previous, no backtracking needed
- All files organized per COMPLETE_STRUCTURE.md
- Docker Compose handles all infrastructure locally
- Tests run at each phase (fast feedback)
- Ready for production deployment end of Week 4
- Continuous improvement after launch (feedback loop)
