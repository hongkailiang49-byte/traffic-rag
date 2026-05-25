"""输入安全网关：Prompt 注入防御 + 敏感词过滤 + RBAC."""

import re
from dataclasses import dataclass
from src.common.logger import get_logger

logger = get_logger(__name__)


@dataclass
class GuardResult:
    blocked: bool
    reason: str = ""


class AhoCorasickFilter:
    """基于 ahocorasick 的敏感词过滤器."""

    def __init__(self, wordlist_path: str = ""):
        import ahocorasick
        self.automaton = ahocorasick.Automaton()
        self._loaded = False
        if wordlist_path:
            self.load(wordlist_path)

    def load(self, path: str) -> None:
        try:
            with open(path, encoding="utf-8") as f:
                for i, line in enumerate(f):
                    word = line.strip()
                    if word:
                        self.automaton.add_word(word, (i, word))
            self.automaton.make_automaton()
            self._loaded = True
        except FileNotFoundError:
            logger.warning(f"Sensitive words file not found: {path}")

    def match(self, text: str) -> list[str]:
        if not self._loaded:
            return []
        matched = []
        for _, (_, word) in self.automaton.iter(text):
            matched.append(word)
        return list(set(matched))


class InputGuard:
    """输入安全网关."""

    # 常见 Prompt 注入模式
    INJECTION_PATTERNS = [
        r"忽略.{0,20}(之前的|上面的|所有).{0,10}(指令|规则|提示)",
        r"ignore.{0,20}(previous|above|all).{0,10}(instructions|rules)",
        r"你现在是",
        r"你是一个.{0,5}(没有|不受).{0,10}限制",
        r"system\s*prompt",
        r"<\|im_start\|>",
        r"jailbreak",
        r"DAN\s*mode",
    ]

    def __init__(self, sensitive_words_path: str = ""):
        self.ac_filter = AhoCorasickFilter(sensitive_words_path)
        self._injection_patterns = [re.compile(p, re.IGNORECASE) for p in self.INJECTION_PATTERNS]

    async def check(self, query: str, user_context: dict | None = None) -> GuardResult:
        user_context = user_context or {}

        # 1. Prompt 注入检测
        for pattern in self._injection_patterns:
            if pattern.search(query):
                logger.warning(f"Prompt injection detected: {query[:50]}")
                return GuardResult(blocked=True, reason="检测到潜在的 Prompt 注入攻击")

        # 2. 敏感词匹配
        matched = self.ac_filter.match(query)
        if matched:
            return GuardResult(blocked=True, reason="查询包含受限信息关键词，请联系管理员获取权限")

        # 3. RBAC 权限校验
        clearance = user_context.get("clearance_level", 0)
        required = self._infer_clearance(query)
        if required > clearance:
            return GuardResult(blocked=True, reason=f"您无权调阅该级别数据（需要 L{required} 权限）")

        return GuardResult(blocked=False)

    @staticmethod
    def _infer_clearance(query: str) -> int:
        """根据查询内容推断所需权限等级."""
        high_keywords = ["高精地图", "精确坐标", "控制中心", "调度系统", "涉密"]
        mid_keywords = ["内部", "非公开", "限流", "管制"]
        if any(kw in query for kw in high_keywords):
            return 3
        if any(kw in query for kw in mid_keywords):
            return 2
        return 1
