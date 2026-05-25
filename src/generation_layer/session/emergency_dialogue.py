"""场景5 — 应急调度多轮对话状态机."""

from enum import Enum
from src.common.logger import get_logger

logger = get_logger(__name__)


class EmergencyState(Enum):
    COLLECTING = "collecting"
    CLARIFYING = "clarifying"
    CLASSIFIED = "classified"
    DISPATCHED = "dispatched"


REQUIRED_SLOTS = {
    "accident": ["location", "severity", "casualties", "hazmat", "road_condition"],
    "fire": ["location", "tunnel_name", "fire_level", "evacuation_status"],
    "equipment": ["device_type", "location", "impact_scope"],
    "congestion": ["location", "cause", "scope"],
}


class EmergencyDialogueManager:
    """应急调度对话管理器."""

    def __init__(self, llm_gateway, session_store, retriever=None):
        self.llm = llm_gateway
        self.session_store = session_store
        self.plan_retriever = retriever

    async def process(self, session_id: str, user_input: str) -> dict:
        """处理用户输入，返回响应."""
        session = self.session_store.get_session(session_id)
        if not session:
            session = self.session_store.create_session(session_id)

        # 1. 意图分类
        intent = self._classify_intent(user_input)
        session["state"]["intent"] = intent

        # 2. 信息提取
        extracted = self._extract_slots(user_input, intent)
        for k, v in extracted.items():
            if v:
                session["state"].setdefault("slots", {})[k] = v

        # 3. 槽位检查
        slots = session["state"].get("slots", {})
        required = REQUIRED_SLOTS.get(intent, [])
        filled = [s for s in required if slots.get(s)]
        completeness = len(filled) / len(required) if required else 1.0

        # 4. 状态路由
        if completeness >= 0.8:
            # 信息充足 → 检索预案 + 生成指令
            plan = self._retrieve_plan(intent, slots)
            dispatch = await self._generate_dispatch(intent, slots, plan)
            session["state"]["phase"] = EmergencyState.DISPATCHED.value
            self.session_store.update_session(session_id, session)
            return {
                "phase": "dispatched",
                "dispatch_order": dispatch,
                "matched_plan": plan,
            }
        else:
            # 信息不足 → 生成反问
            missing = [s for s in required if not slots.get(s)]
            clarification = self._generate_clarification(intent, slots, missing)
            session["state"]["phase"] = EmergencyState.CLARIFYING.value
            self.session_store.update_session(session_id, session)
            return {
                "phase": "clarifying",
                "clarification": clarification,
                "missing_slots": missing,
                "collected_slots": slots,
            }

    def _classify_intent(self, text: str) -> str:
        keywords = {
            "accident": ["事故", "追尾", "碰撞", "翻车", "撞车"],
            "fire": ["火灾", "起火", "燃烧", "隧道火"],
            "equipment": ["故障", "损坏", "设备", "信号灯坏"],
            "congestion": ["拥堵", "堵车", "缓行", "排队"],
        }
        for intent, kws in keywords.items():
            if any(kw in text for kw in kws):
                return intent
        return "accident"

    def _extract_slots(self, text: str, intent: str) -> dict:
        """从文本提取信息槽位."""
        import re
        slots = {}
        # 位置
        loc_match = re.search(r"([一-龥]+(?:路段|路口|隧道|桥|收费站|服务区|高速|公路))", text)
        if loc_match:
            slots["location"] = loc_match.group(1)
        # 隧道名
        tunnel_match = re.search(r"([一-龥]+隧道)", text)
        if tunnel_match:
            slots["tunnel_name"] = tunnel_match.group(1)
        # 严重程度
        for kw, level in [("严重", "严重"), ("轻微", "轻微"), ("重大", "重大"), ("一般", "一般")]:
            if kw in text:
                slots["severity"] = level
                break
        # 伤亡
        if "伤亡" in text or "伤" in text or "亡" in text:
            slots["casualties"] = "有"
        # 危化品
        if "危化" in text or "危险品" in text or "泄漏" in text:
            slots["hazmat"] = "是"
        return slots

    def _generate_clarification(self, intent: str, slots: dict, missing: list[str]) -> str:
        """生成引导性反问."""
        slot_names = {
            "location": "具体位置",
            "severity": "严重程度",
            "casualties": "是否有伤亡",
            "hazmat": "是否涉及危化品",
            "road_condition": "路面状况",
            "tunnel_name": "隧道名称",
            "fire_level": "火势等级",
            "evacuation_status": "疏散情况",
            "device_type": "设备类型",
            "impact_scope": "影响范围",
            "cause": "拥堵原因",
            "scope": "拥堵范围",
        }
        missing_names = [slot_names.get(s, s) for s in missing[:2]]
        return f"请补充以下信息：{'、'.join(missing_names)}"

    def _retrieve_plan(self, intent: str, slots: dict) -> str:
        """检索应急预案."""
        if not self.plan_retriever:
            return "（无预案库接入，请参考标准应急流程）"
        query = f"{intent} {slots.get('location', '')} {slots.get('severity', '')}"
        try:
            results = self.plan_retriever.retrieve(query, top_k=1, filters={"category": "应急预案"})
            return results[0].content if results else "未找到匹配预案"
        except Exception:
            return "预案检索失败"

    async def _generate_dispatch(self, intent: str, slots: dict, plan: str) -> str:
        """生成处置指令."""
        system_prompt = "你是交通应急调度专家。基于现场信息和预案，生成简明处置指令。"
        user_prompt = f"""事件类型: {intent}
现场信息: {slots}
匹配预案: {plan}

请输出结构化指令：1)立即措施 2)调度资源 3)上报流程"""
        try:
            return await self.llm.invoke(user_prompt, system_prompt=system_prompt)
        except Exception as e:
            logger.error(f"Dispatch generation failed: {e}")
            return self._fallback_dispatch(intent, slots)

    @staticmethod
    def _fallback_dispatch(intent: str, slots: dict) -> str:
        """兜底处置指令."""
        location = slots.get("location", "事发地点")
        return f"""【应急处置指令】
1. 立即措施：在{location}设置警示标志，疏导交通
2. 调度资源：通知就近交警、路政、急救力量赶赴现场
3. 上报流程：向指挥中心报告事件详情，请求支援"""
