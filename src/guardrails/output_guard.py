"""输出安全网关：PII 脱敏 + 事实核查."""

import re
from src.common.logger import get_logger

logger = get_logger(__name__)


class OutputGuard:
    """输出安全网关."""

    # 正则模式的 PII
    PII_PATTERNS = {
        "phone": (re.compile(r"1[3-9]\d{9}"), lambda m: m.group()[:3] + "****" + m.group()[-4:]),
        "id_card": (re.compile(r"\d{17}[\dXx]"), lambda m: m.group()[:4] + "**********" + m.group()[-4:]),
        "plate": (re.compile(r"[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤川青藏琼宁][A-Z][A-Z0-9]{5}"),
                  lambda m: m.group()[:2] + "****" + m.group()[-1:]),
        "email": (re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
                  lambda m: m.group()[:2] + "***@" + m.group().split("@")[1]),
    }

    def sanitize(self, text: str, user_clearance: int = 1) -> str:
        """对输出文本进行脱敏处理."""
        if user_clearance >= 3:
            return text

        result = text
        for pii_type, (pattern, masker) in self.PII_PATTERNS.items():
            result = pattern.sub(masker, result)

        return result

    def add_hallucination_warning(self, answer: str, has_source: bool) -> str:
        """如果回答没有引用来源，添加幻觉警告."""
        if not has_source:
            answer += "\n\n[系统提示] 以上回答可能包含未经验证的信息，请以原始法规条文为准。"
        return answer
