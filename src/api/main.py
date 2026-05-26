"""FastAPI 应用入口."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.settings import settings
from src.common.logger import setup_logging, get_logger

logger = get_logger(__name__)

# 全局状态（延迟初始化）
app_state: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动/关闭生命周期."""
    setup_logging(settings.app_log_level)
    logger.info("Starting Traffic RAG System...", env=settings.app_env)
    if settings.app_env == "development":
        logger.warning("Running in DEVELOPMENT mode — auth bypass is enabled, CORS is permissive. Do NOT use in production.")
    if not settings.jwt_secret_key:
        logger.warning("JWT_SECRET_KEY is not set — token creation will fail. Set it via .env")
    if not settings.mimo_base_url or not settings.mimo_api_key:
        logger.warning("MIMO_BASE_URL or MIMO_API_KEY is not set — LLM calls will fail. Set them via .env")
    if settings.is_production and settings.cors_origins == "*":
        logger.error("CORS_ORIGINS cannot be '*' in production. Exiting.")
        raise SystemExit(1)
    try:
        _init_components()
        logger.info("All components initialized")
    except Exception as e:
        logger.warning(f"Component init deferred: {e}")
    yield
    logger.info("Shutting down...")


def _init_components():
    """初始化所有组件."""
    from src.data_layer.embedders.bge_embedder import BGEEmbedder
    from src.data_layer.stores.vector_store import MilvusVectorStore
    from src.data_layer.stores.graph_store import Neo4jGraphStore
    from src.data_layer.stores.user_store import UserStore
    from src.data_layer.pipeline import IndexingPipeline
    from src.retrieval_layer.rerankers.cross_encoder import CrossEncoderReranker
    from src.retrieval_layer.retrievers.regulatory import RegulatoryRetriever
    from src.retrieval_layer.retrievers.spatiotemporal import SpatioTemporalRetriever
    from src.retrieval_layer.retrievers.graph_rag import GraphRAGRetriever
    from src.retrieval_layer.retrievers.hybrid import HybridRetriever
    from src.retrieval_layer.intent_router import IntentRouter
    from src.generation_layer.llm_gateway import LLMGateway
    from src.generation_layer.prompt_manager import PromptManager
    from src.generation_layer.citation import CitationManager
    from src.generation_layer.session.session_store import SessionStore
    from src.generation_layer.session.emergency_dialogue import EmergencyDialogueManager
    from src.guardrails.input_guard import InputGuard
    from src.guardrails.output_guard import OutputGuard

    # Data Layer
    embedder = BGEEmbedder(model_name=settings.embedding_model, device=settings.embedding_device)
    vector_store = MilvusVectorStore()
    vector_store.create_collection(dimension=embedder.dimension)
    graph_store = Neo4jGraphStore()
    user_store = UserStore()
    user_store.create_indexes()

    # Retrieval Layer
    reranker = CrossEncoderReranker(model_name=settings.reranker_model, device=settings.reranker_device)
    regulatory = RegulatoryRetriever(vector_store, embedder, reranker)
    spatiotemporal = SpatioTemporalRetriever(vector_store, embedder)
    graph_rag = GraphRAGRetriever(vector_store, graph_store, embedder, reranker)
    hybrid = HybridRetriever(regulatory, spatiotemporal, graph_rag)
    intent_router = IntentRouter()

    # Generation Layer
    llm_gateway = LLMGateway(
        mimo_base_url=settings.mimo_base_url,
        mimo_api_key=settings.mimo_api_key,
        mimo_model=settings.mimo_model,
        mimo_pro_model=settings.mimo_pro_model,
    )
    prompt_manager = PromptManager()
    citation_manager = CitationManager()
    session_store = SessionStore()

    # Guardrails
    input_guard = InputGuard(settings.sensitive_words_path)
    output_guard = OutputGuard()

    # Pipeline
    pipeline = IndexingPipeline(embedder, vector_store)

    # Emergency Dialogue
    dialogue_mgr = EmergencyDialogueManager(llm_gateway, session_store, regulatory)

    app_state.update({
        "embedder": embedder,
        "vector_store": vector_store,
        "graph_store": graph_store,
        "user_store": user_store,
        "reranker": reranker,
        "hybrid": hybrid,
        "intent_router": intent_router,
        "llm_gateway": llm_gateway,
        "prompt_manager": prompt_manager,
        "citation_manager": citation_manager,
        "session_store": session_store,
        "input_guard": input_guard,
        "output_guard": output_guard,
        "pipeline": pipeline,
        "dialogue_manager": dialogue_mgr,
        "engine": RAGEngine(
            hybrid=hybrid,
            intent_router=intent_router,
            llm_gateway=llm_gateway,
            prompt_manager=prompt_manager,
            citation_manager=citation_manager,
            session_store=session_store,
            user_store=user_store,
            input_guard=input_guard,
            output_guard=output_guard,
            dialogue_mgr=dialogue_mgr,
        ),
    })


class RAGEngine:
    """RAG 查询引擎 — 编排完整查询流程."""

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    async def query(self, question: str, session_id: str = "", intent: str = "auto",
                    filters: dict | None = None, top_k: int = 5, user_context: dict | None = None) -> dict:
        filters = filters or {}
        user_context = user_context or {}

        # 1. 输入安全检查
        guard_result = await self.input_guard.check(question, user_context)
        if guard_result.blocked:
            return {"answer": guard_result.reason, "intent": "blocked", "sources": []}

        # 2. 意图路由
        if intent == "auto":
            intent = await self.intent_router.classify(question, self.llm_gateway)

        # 3. 应急对话走独立流程
        if intent == "emergency":
            result = await self.dialogue_mgr.process(session_id, question)
            return {
                "answer": result.get("dispatch_order", "") or result.get("clarification", ""),
                "intent": "emergency",
                "sources": [],
                "phase": result.get("phase", ""),
                "clarification": result.get("clarification", ""),
            }

        # 4. 检索
        retrieval_results = self.hybrid.retrieve(question, intent=intent, top_k=top_k, filters=filters)

        # 5. 构建上下文
        context = self.citation_manager.build_context_with_citation(retrieval_results)

        # 6. 生成回答
        template = "regulatory_qa" if intent == "regulatory" else "multimodal_analysis"
        system_prompt, user_prompt = self.prompt_manager.build(template, context=context, question=question)
        answer = await self.llm_gateway.invoke(user_prompt, system_prompt=system_prompt)

        # 7. 输出脱敏
        answer = self.output_guard.sanitize(answer, user_context.get("clearance_level", 1))
        answer = self.output_guard.add_hallucination_warning(answer, has_source=len(retrieval_results) > 0)

        # 8. 记录会话
        if session_id:
            self.session_store.add_message(session_id, "user", question)
            self.session_store.add_message(session_id, "assistant", answer)
            # 持久化到 Neo4j
            self._persist_to_neo4j(session_id, question, answer, intent, user_context)

        sources = [{"content": r.content[:200], "score": r.score, "source": r.source} for r in retrieval_results]
        return {"answer": answer, "intent": intent, "sources": sources}

    def _persist_to_neo4j(self, session_id: str, question: str, answer: str, intent: str, user_context: dict) -> None:
        """将聊天记录持久化到 Neo4j."""
        try:
            email = user_context.get("user_id")
            if not email or email == "dev_user":
                return
            history = self.session_store.get_history(session_id, limit=1000)
            seq = len(history) - 1  # 当前 answer 的 seq
            if seq <= 1:
                self.user_store.create_chat_session(email, session_id, intent)
            self.user_store.add_chat_message(session_id, "user", question, seq - 1)
            self.user_store.add_chat_message(session_id, "assistant", answer, seq)
        except Exception as e:
            logger.warning(f"Failed to persist chat to Neo4j: {e}")


app = FastAPI(
    title="交通领域 RAG 系统",
    version="1.0.0",
    description="基于 RAG 的交通法规、应急调度、GraphRAG 智能问答系统",
    lifespan=lifespan,
)

origins = [o.strip() for o in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册中间件
from src.api.middleware.rate_limit import rate_limit_middleware
app.middleware("http")(rate_limit_middleware)

# 注册路由
from src.api.routes import query, ingest, session, auth
app.include_router(auth.router)
app.include_router(query.router)
app.include_router(ingest.router)
app.include_router(session.router)


@app.get("/health")
async def health():
    return {"status": "ok", "components": {k: "ready" for k in app_state if k != "engine"}}


# --- 前端静态文件服务 ---
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

_frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if _frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=_frontend_dist / "assets"), name="static-assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """SPA catch-all: 返回 index.html 让前端路由接管."""
        file_path = _frontend_dist / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(_frontend_dist / "index.html")
