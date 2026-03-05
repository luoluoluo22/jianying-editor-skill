import argparse
import csv
import os
from typing import Dict, List

from utils.cli_protocol import emit_result, make_result
from utils.constants import SYNONYMS
from utils.errors import InfraError
from utils.logging_utils import setup_logger

logger = setup_logger("asset_search")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")


def expand_query_with_synonyms(query: str) -> List[str]:
    terms = query.lower().split()
    expanded_terms = set(terms)
    for term in terms:
        if term in SYNONYMS:
            expanded_terms.update(SYNONYMS[term])
            continue
        for key, values in SYNONYMS.items():
            if term in key:
                expanded_terms.update(values)
    return list(expanded_terms)


def get_enum_key_from_ident(ident: str) -> str:
    ident_lower = ident.lower()
    for key, synonyms in SYNONYMS.items():
        if key in ident_lower:
            return key
        for syn in synonyms:
            if syn in ident_lower:
                return key
    return ""


def _iter_rows(filepath: str):
    with open(filepath, "r", encoding="utf-8", newline="") as f:
        lines = [line for line in f if not line.startswith("#")]
    if not lines:
        return
    reader = csv.DictReader(lines)
    for row in reader:
        yield row


def search_assets(query: str, category: str = None, limit: int = 20) -> List[Dict[str, str]]:
    results: List[Dict[str, str]] = []
    search_terms = expand_query_with_synonyms(query)

    if not os.path.exists(DATA_DIR):
        raise InfraError(f"Data directory not found: {DATA_DIR}")

    files_to_search: List[str]
    if category:
        normalized = category if category.endswith(".csv") else f"{category}.csv"
        if os.path.exists(os.path.join(DATA_DIR, normalized)):
            files_to_search = [normalized]
        else:
            # 支持前缀匹配，如 -c filter => filters.csv
            all_csv = [f for f in os.listdir(DATA_DIR) if f.endswith(".csv")]
            files_to_search = [f for f in all_csv if f.startswith(category)]
    else:
        files_to_search = [f for f in os.listdir(DATA_DIR) if f.endswith(".csv")]

    for filename in files_to_search:
        filepath = os.path.join(DATA_DIR, filename)
        if not os.path.exists(filepath):
            logger.warning("Category file not found: %s", filename)
            continue

        for row in _iter_rows(filepath):
            target_text = " ".join(
                [
                    row.get("identifier", ""),
                    row.get("description", ""),
                    row.get("category", ""),
                    row.get("title", ""),
                    row.get("name", ""),
                ]
            ).lower()

            score = 0
            if query.lower() in target_text:
                score += 100
            for term in search_terms:
                if term in target_text:
                    score += 10

            if score > 0:
                row["score"] = score
                row["source_file"] = filename
                results.append(row)

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[: max(1, limit)]


def format_results(results: List[Dict[str, str]]) -> str:
    if not results:
        return "❌ 未找到匹配项。尝试更简单的关键词或切换分类。"

    header = f"{'Identifier':<25} | {'Category':<15} | {'API Key (Use This)':<20} | {'Source'}"
    output = [header, "-" * len(header)]

    for r in results:
        ident = r.get("identifier") or r.get("title") or r.get("name") or "N/A"
        display_ident = ident if len(ident) <= 23 else ident[:20] + "..."
        cat = (r.get("category") or r.get("categories") or "N/A")[:15]
        src = r.get("source_file", "").replace(".csv", "")
        enum_key = get_enum_key_from_ident(ident) or ident
        if len(enum_key) > 18:
            enum_key = enum_key[:15] + "..."
        output.append(f"{display_ident:<25} | {cat:<15} | {enum_key:<20} | {src}")

    return "\n".join(output)


def _list_categories() -> int:
    print("=== 剪映资产数据库概览 ===")
    if not os.path.exists(DATA_DIR):
        logger.error("Data directory not found: %s", DATA_DIR)
        return 1

    for filename in sorted(os.listdir(DATA_DIR)):
        if not filename.endswith(".csv"):
            continue
        filepath = os.path.join(DATA_DIR, filename)
        try:
            count = sum(1 for _ in _iter_rows(filepath))
        except Exception as e:
            logger.warning("Failed reading %s: %s", filename, e)
            count = 0
        print(f"{filename:<30} | {count}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="剪映资产搜索工具 (智能双语版)")
    parser.add_argument("query", nargs="?", default=None, help="搜索关键词")
    parser.add_argument("-c", "--category", help="限定分类（csv 文件名或前缀）")
    parser.add_argument("-l", "--limit", type=int, default=20, help="数量限制")
    parser.add_argument("--list", action="store_true", help="列出分类")
    parser.add_argument("--json", action="store_true", help="输出 JSON 结果")
    args = parser.parse_args()

    if args.list:
        return _list_categories()

    if not args.query:
        parser.print_help()
        return 0

    logger.info("Searching '%s'...", args.query)
    try:
        search_results = search_assets(args.query, args.category, args.limit)
        if args.json:
            emit_result(
                make_result(
                    True,
                    "ok",
                    "",
                    {
                        "query": args.query,
                        "category": args.category,
                        "count": len(search_results),
                        "results": search_results,
                    },
                ),
                True,
            )
        else:
            print(format_results(search_results))
        return 0
    except InfraError as e:
        logger.error(str(e))
        emit_result(make_result(False, "infra_error", str(e)), args.json)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
