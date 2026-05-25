"""Neo4j 图数据库实现."""

from neo4j import GraphDatabase
from config.settings import settings
from src.common.logger import get_logger

logger = get_logger(__name__)

# 交通实体-关系本体
ENTITY_TYPES = [
    "RoadSegment", "Intersection", "TollStation", "Camera",
    "SignalLight", "Tunnel", "Bridge", "Accident",
    "WeatherEvent", "EmergencyPlan",
]

RELATION_TYPES = [
    ("RoadSegment", "CONNECTS_TO", "RoadSegment"),
    ("RoadSegment", "HAS_DEVICE", "Camera"),
    ("RoadSegment", "HAS_DEVICE", "SignalLight"),
    ("Accident", "OCCURRED_ON", "RoadSegment"),
    ("Accident", "TRIGGERED", "EmergencyPlan"),
    ("WeatherEvent", "AFFECTS", "RoadSegment"),
    ("Intersection", "CONTROLS", "SignalLight"),
]


class Neo4jGraphStore:
    """Neo4j 图存储 — 交通实体与关系管理."""

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

    def create_constraints(self) -> None:
        """创建唯一性约束和索引."""
        driver = self._get_driver()
        with driver.session() as session:
            for entity_type in ENTITY_TYPES:
                try:
                    session.run(
                        f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{entity_type}) REQUIRE n.name IS UNIQUE"
                    )
                except Exception as e:
                    logger.warning(f"Constraint for {entity_type}: {e}")
        logger.info("Graph constraints created")

    def upsert_entity(self, entity_type: str, name: str, properties: dict | None = None) -> None:
        """插入或更新实体."""
        if entity_type not in ENTITY_TYPES:
            raise ValueError(f"Unknown entity type: {entity_type}. Allowed: {ENTITY_TYPES}")
        props = properties or {}
        props["name"] = name
        driver = self._get_driver()
        with driver.session() as session:
            prop_set = ", ".join(f"n.{k} = ${k}" for k in props)
            query = f"MERGE (n:{entity_type} {{name: $name}}) SET {prop_set}"
            session.run(query, **props)

    def upsert_relation(
        self, from_type: str, from_name: str, rel_type: str, to_type: str, to_name: str, properties: dict | None = None
    ) -> None:
        """插入或更新关系."""
        for t in (from_type, to_type):
            if t not in ENTITY_TYPES:
                raise ValueError(f"Unknown entity type: {t}. Allowed: {ENTITY_TYPES}")
        props = properties or {}
        driver = self._get_driver()
        with driver.session() as session:
            prop_set = ", ".join(f"r.{k} = ${k}" for k in props) if props else ""
            set_clause = f" SET {prop_set}" if prop_set else ""
            query = (
                f"MATCH (a:{from_type} {{name: $from_name}}), (b:{to_type} {{name: $to_name}}) "
                f"MERGE (a)-[r:{rel_type}]->(b){set_clause}"
            )
            session.run(query, from_name=from_name, to_name=to_name, **props)

    def resolve_entity(self, name: str) -> str | None:
        """根据名称查找实体节点 ID."""
        driver = self._get_driver()
        with driver.session() as session:
            result = session.run(
                "MATCH (n) WHERE n.name = $name RETURN elementId(n) AS id LIMIT 1", name=name
            )
            record = result.single()
            return record["id"] if record else None

    def traverse(self, start_node_id: str, max_hops: int = 2, relation_types: list[str] | None = None) -> list[dict]:
        """从指定节点出发，沿关系遍历."""
        max_hops = min(max(1, max_hops), 5)  # clamp to [1, 5]
        driver = self._get_driver()
        rel_filter = ""
        if relation_types:
            safe_types = [t for t in relation_types if t.isalpha() or "_" in t]
            rel_types = "|".join(safe_types)
            rel_filter = f":{rel_types}"

        query = f"""
        MATCH path = (start)-[r{rel_filter}*1..{max_hops}]-(end)
        WHERE elementId(start) = $node_id
        RETURN nodes(path) AS nodes, relationships(path) AS rels
        LIMIT 50
        """
        results = []
        with driver.session() as session:
            for record in session.run(query, node_id=start_node_id):
                nodes = [{"name": n.get("name", ""), "labels": list(n.labels)} for n in record["nodes"]]
                rels = [{"type": r.type, "props": dict(r)} for r in record["rels"]]
                results.append({"nodes": nodes, "relationships": rels})
        return results

    def extract_triples_from_text(self, text: str, llm_client=None) -> list[tuple]:
        """从文本中提取三元组（实体-关系-实体）."""
        # 简化实现：基于模式匹配提取
        triples = []
        import re
        # 匹配"XX位于XX"、"XX连接XX"等模式
        patterns = [
            (r"([一-龥]+(?:高速|公路|路段|大道))连接([一-龥]+(?:高速|公路|路段|大道))", "CONNECTS_TO"),
            (r"([一-龥]+(?:隧道|桥))位于([一-龥]+(?:高速|公路|路段))", "LOCATED_ON"),
            (r"([一-龥]+事故)发生在([一-龥]+(?:路段|路口))", "OCCURRED_ON"),
        ]
        for pattern, rel_type in patterns:
            for match in re.finditer(pattern, text):
                triples.append((match.group(1), rel_type, match.group(2)))
        return triples
