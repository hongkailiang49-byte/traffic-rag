"""意图路由器 — LLM Few-Shot 分类."""

INTENT_PROMPT = """你是交通系统的意图分类器。根据用户输入，判断其意图类别。

类别说明：
- regulatory: 法规标准查询（如"公路设计规范"、"JTG标准"、"交通法规"）
- spatiotemporal: 时空数据查询（如"某路段流量"、"拥堵情况"、"实时数据"）
- graph_rag: 关联推理查询（如"事故影响"、"连锁反应"、"拓扑关系"）
- emergency: 应急调度对话（如"事故报警"、"隧道火灾"、"危险品泄漏"）
- general: 通用交通知识问答

只输出类别名称，不要其他内容。

用户输入：{query}
类别："""


class IntentRouter:
    """意图路由器 — 将查询分发到对应检索器."""

    INTENT_MAP = {
        "regulatory": "regulatory",
        "spatiotemporal": "spatiotemporal",
        "graph_rag": "graph_rag",
        "emergency": "emergency",
        "general": "regulatory",
    }

    # 关键词快速分类（优先于 LLM）
    KEYWORD_RULES = [
        (["规范", "标准", "法规", "条文", "JTG", "GB", "JT/", "法律", "条例"], "regulatory"),
        (["流量", "拥堵", "实时", "监控", "车速", "路段数据", "GPS", "定位"], "spatiotemporal"),
        (["事故影响", "连锁", "波及", "上下游", "关联", "拓扑", "因果"], "graph_rag"),
        (["报警", "应急", "火灾", "泄漏", "追尾", "处置", "救援", "调度"], "emergency"),
    ]

    async def classify(self, query: str, llm_client=None) -> str:
        """分类用户查询意图."""
        # 1. 关键词规则优先
        for keywords, intent in self.KEYWORD_RULES:
            if any(kw in query for kw in keywords):
                return intent

        # 2. LLM 分类兜底
        if llm_client:
            try:
                prompt = INTENT_PROMPT.format(query=query)
                result = await llm_client.invoke(prompt)
                intent = result.strip().lower()
                if intent in self.INTENT_MAP:
                    return intent
            except Exception:
                pass

        return "regulatory"  # 默认走法规检索
