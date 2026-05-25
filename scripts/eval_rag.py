"""RAG 效果评测脚本."""

import sys
sys.path.insert(0, ".")

import json
from pathlib import Path
from config.settings import settings
from src.data_layer.embedders.bge_embedder import BGEEmbedder
from src.data_layer.stores.vector_store import MilvusVectorStore
from src.retrieval_layer.retrievers.regulatory import RegulatoryRetriever
from src.common.logger import setup_logging

setup_logging("INFO")


def eval_recall(retriever, test_cases: list[dict], k: int = 10) -> float:
    """计算 Recall@K."""
    hits = 0
    for case in test_cases:
        results = retriever.retrieve(case["question"], top_k=k)
        result_texts = " ".join(r.content for r in results)
        if any(ans in result_texts for ans in case["expected_keywords"]):
            hits += 1
    return hits / len(test_cases) if test_cases else 0


def eval_mrr(retriever, test_cases: list[dict], k: int = 5) -> float:
    """计算 MRR@K."""
    rr_sum = 0
    for case in test_cases:
        results = retriever.retrieve(case["question"], top_k=k)
        for rank, r in enumerate(results, 1):
            if any(ans in r.content for ans in case["expected_keywords"]):
                rr_sum += 1 / rank
                break
    return rr_sum / len(test_cases) if test_cases else 0


def main():
    # 示例测试用例（可扩展）
    test_cases = [
        {
            "question": "公路工程技术标准的主要内容是什么？",
            "expected_keywords": ["JTG B01", "公路等级", "设计速度"],
        },
        {
            "question": "道路交通安全法对酒驾怎么处罚？",
            "expected_keywords": ["饮酒", "醉酒", "吊销", "拘留"],
        },
        {
            "question": "隧道通风设计的规范要求？",
            "expected_keywords": ["通风", "隧道", "射流"],
        },
    ]

    print("Loading models...")
    embedder = BGEEmbedder(model_name=settings.embedding_model, device=settings.embedding_device)
    vector_store = MilvusVectorStore()
    retriever = RegulatoryRetriever(vector_store, embedder)

    print(f"Evaluating with {len(test_cases)} test cases...\n")

    recall_10 = eval_recall(retriever, test_cases, k=10)
    mrr_5 = eval_mrr(retriever, test_cases, k=5)

    print("=== Evaluation Results ===")
    print(f"Recall@10: {recall_10:.3f} (target: ≥ 0.90)")
    print(f"MRR@5:     {mrr_5:.3f} (target: ≥ 0.80)")

    # 保存报告
    report = {"recall_at_10": recall_10, "mrr_at_5": mrr_5, "test_cases": len(test_cases)}
    report_path = Path("eval_report.json")
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"\nReport saved to: {report_path}")


if __name__ == "__main__":
    main()
