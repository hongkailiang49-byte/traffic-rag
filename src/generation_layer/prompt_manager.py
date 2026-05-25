"""Prompt 模板管理."""

PROMPT_TEMPLATES = {
    "regulatory_qa": {
        "system": """你是交通法规专家。严格基于以下条文回答问题，不得编造。
如果检索到的条文无法回答问题，请明确回复"现有法规条文中未找到相关规定"。

引用格式要求：
- 必须标注标准编号（如 JTG B01-2014）
- 必须标注具体条款号（如第四十三条）
- 必须标注发布年份

检索到的法规条文：
{context}""",
        "user": "{question}",
    },
    "emergency_dispatch": {
        "system": """你是交通应急调度 AI 助手。基于现场信息和匹配的应急预案，
生成结构化处置指令。输出必须包含：立即措施、需调度资源、上报流程。
语气简洁明确，适合对讲机播报。""",
        "user": "事件信息：{event_info}\n匹配预案：{plan_context}",
    },
    "multimodal_analysis": {
        "system": """你是交通数据分析专家。基于以下多源数据回答问题，
标注数据来源和时间。如果数据之间存在矛盾，指出矛盾点。""",
        "user": "{context}\n\n问题：{question}",
    },
    "graph_reasoning": {
        "system": """你是交通拓扑分析专家。基于以下图谱关系和检索结果，
分析交通实体之间的关联关系和潜在影响。
回答时必须说明推理链条。""",
        "user": "图谱关系：{graph_context}\n检索结果：{vector_context}\n\n问题：{question}",
    },
}


class PromptManager:
    """Prompt 模板管理器."""

    def __init__(self):
        self.templates = PROMPT_TEMPLATES

    def build(self, template_name: str, **kwargs) -> tuple[str, str]:
        """构建 system_prompt 和 user_prompt."""
        template = self.templates.get(template_name)
        if not template:
            raise ValueError(f"Unknown template: {template_name}")
        system = template["system"].format(**kwargs)
        user = template["user"].format(**kwargs)
        return system, user

    def list_templates(self) -> list[str]:
        return list(self.templates.keys())
