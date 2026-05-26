"""用户存储 — 基于 Neo4j 的用户管理."""

from datetime import datetime, timezone
from neo4j import GraphDatabase
from config.settings import settings
from src.common.logger import get_logger

logger = get_logger(__name__)


class UserStore:
    """Neo4j 用户存储."""

    def __init__(self):
        self._driver = None

    def _get_driver(self):
        if self._driver is None:
            self._driver = GraphDatabase.driver(
                settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
            )
        return self._driver

    def close(self):
        if self._driver:
            self._driver.close()
            self._driver = None

    def create_indexes(self) -> None:
        """创建用户和会话唯一性约束."""
        driver = self._get_driver()
        with driver.session() as session:
            try:
                session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (u:User) REQUIRE u.email IS UNIQUE")
                logger.info("User constraint created")
            except Exception as e:
                logger.warning(f"User constraint: {e}")
            try:
                session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (s:Session) REQUIRE s.session_id IS UNIQUE")
                logger.info("Session constraint created")
            except Exception as e:
                logger.warning(f"Session constraint: {e}")

    def create_user(self, email: str, name: str, password_hash: str, clearance_level: int = 1) -> dict:
        """创建用户，返回用户信息."""
        driver = self._get_driver()
        now = datetime.now(timezone.utc).isoformat()
        with driver.session() as session:
            result = session.run(
                """
                CREATE (u:User {
                    email: $email,
                    name: $name,
                    password_hash: $password_hash,
                    clearance_level: $clearance_level,
                    created_at: $created_at,
                    last_login: $created_at
                })
                RETURN u.email AS email, u.name AS name, u.clearance_level AS clearance_level, u.created_at AS created_at
                """,
                email=email, name=name, password_hash=password_hash,
                clearance_level=clearance_level, created_at=now,
            )
            record = result.single()
            if not record:
                raise RuntimeError("Failed to create user")
            return dict(record)

    def get_user_by_email(self, email: str) -> dict | None:
        """根据邮箱查找用户."""
        driver = self._get_driver()
        with driver.session() as session:
            result = session.run(
                "MATCH (u:User {email: $email}) RETURN u",
                email=email,
            )
            record = result.single()
            if not record:
                return None
            node = record["u"]
            return dict(node)

    def update_last_login(self, email: str) -> None:
        """更新最后登录时间."""
        driver = self._get_driver()
        now = datetime.now(timezone.utc).isoformat()
        with driver.session() as session:
            session.run(
                "MATCH (u:User {email: $email}) SET u.last_login = $now",
                email=email, now=now,
            )

    def record_query(self, email: str, question: str, intent: str) -> None:
        """记录用户查询行为."""
        driver = self._get_driver()
        now = datetime.now(timezone.utc).isoformat()
        with driver.session() as session:
            session.run(
                """
                MATCH (u:User {email: $email})
                CREATE (q:Query {question: $question, intent: $intent, created_at: $created_at})
                CREATE (u)-[:ASKED]->(q)
                """,
                email=email, question=question, intent=intent, created_at=now,
            )

    def get_user_stats(self, email: str) -> dict:
        """获取用户统计信息."""
        driver = self._get_driver()
        with driver.session() as session:
            result = session.run(
                """
                MATCH (u:User {email: $email})
                OPTIONAL MATCH (u)-[:ASKED]->(q:Query)
                RETURN count(q) AS total_queries,
                       count(DISTINCT q.intent) AS intent_diversity
                """,
                email=email,
            )
            record = result.single()
            return {
                "total_queries": record["total_queries"] if record else 0,
                "intent_diversity": record["intent_diversity"] if record else 0,
            }

    # ---- 聊天记录持久化 ----

    def create_chat_session(self, email: str, session_id: str, intent: str = "") -> None:
        """创建会话节点并关联用户."""
        driver = self._get_driver()
        now = datetime.now(timezone.utc).isoformat()
        with driver.session() as session:
            session.run(
                """
                MATCH (u:User {email: $email})
                MERGE (s:Session {session_id: $session_id})
                ON CREATE SET s.created_at = $created_at, s.intent = $intent
                MERGE (u)-[:HAS_SESSION]->(s)
                """,
                email=email, session_id=session_id, created_at=now, intent=intent,
            )

    def add_chat_message(self, session_id: str, role: str, content: str, seq: int) -> None:
        """向会话添加一条消息."""
        driver = self._get_driver()
        now = datetime.now(timezone.utc).isoformat()
        with driver.session() as session:
            session.run(
                """
                MATCH (s:Session {session_id: $session_id})
                CREATE (m:ChatMessage {
                    role: $role,
                    content: $content,
                    seq: $seq,
                    created_at: $created_at
                })
                CREATE (s)-[:HAS_MESSAGE]->(m)
                """,
                session_id=session_id, role=role, content=content, seq=seq, created_at=now,
            )

    def get_chat_history(self, session_id: str, limit: int = 50) -> list[dict]:
        """获取会话的聊天记录."""
        driver = self._get_driver()
        with driver.session() as session:
            result = session.run(
                """
                MATCH (s:Session {session_id: $session_id})-[:HAS_MESSAGE]->(m:ChatMessage)
                RETURN m.role AS role, m.content AS content, m.seq AS seq, m.created_at AS created_at
                ORDER BY m.seq ASC
                LIMIT $limit
                """,
                session_id=session_id, limit=limit,
            )
            return [dict(r) for r in result]

    def get_user_sessions(self, email: str, limit: int = 20) -> list[dict]:
        """获取用户的所有会话."""
        driver = self._get_driver()
        with driver.session() as session:
            result = session.run(
                """
                MATCH (u:User {email: $email})-[:HAS_SESSION]->(s:Session)
                OPTIONAL MATCH (s)-[:HAS_MESSAGE]->(m:ChatMessage)
                WITH s, m ORDER BY m.seq ASC
                RETURN s.session_id AS session_id,
                       s.intent AS intent,
                       s.created_at AS created_at,
                       count(m) AS message_count,
                       collect(m.content)[0] AS first_message
                ORDER BY s.created_at DESC
                LIMIT $limit
                """,
                email=email, limit=limit,
            )
            return [dict(r) for r in result]

    def delete_session(self, session_id: str) -> None:
        """删除会话及其所有消息."""
        driver = self._get_driver()
        with driver.session() as session:
            session.run(
                """
                MATCH (s:Session {session_id: $session_id})
                OPTIONAL MATCH (s)-[:HAS_MESSAGE]->(m:ChatMessage)
                DETACH DELETE m, s
                """,
                session_id=session_id,
            )
