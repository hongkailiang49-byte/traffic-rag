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
        """创建用户唯一性约束."""
        driver = self._get_driver()
        with driver.session() as session:
            try:
                session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (u:User) REQUIRE u.email IS UNIQUE")
                logger.info("User constraint created")
            except Exception as e:
                logger.warning(f"User constraint: {e}")

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
