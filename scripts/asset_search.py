import os
import csv
import argparse
import sys

# 设置基础目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

# --- 扩展: 常见同义词映射库 (Synonym Dictionary) ---
SYNONYMS = {
    # 常用英文 -> 中文
    "dissolve": ["叠化", "溶解", "混合"],
    "fade": ["渐隐", "渐显", "黑场", "白场"],
    "glitch": ["故障", "干扰", "燥波", "雪花"],
    "zoom": ["拉近", "拉远", "缩放", "变焦"],
    "shake": ["振动", "摇晃", "抖动"],
    "blur": ["模糊", "虚化"],
    "glow": ["发光", "辉光", "霓虹"],
    "retro": ["复古", "胶片", "怀旧", "DV"],
    "film": ["胶片", "电影", "颗粒"],
    "typewriter": ["打字机", "字幕"],
    "particle": ["粒子", "碎片"],
    "fire": ["火", "燃烧", "烈焰"],
    "rain": ["雨", "水滴"],
    "cyber": ["赛博", "科技", "数码"],
    "scan": ["扫描", "全息"],
    
    # 场景化描述
    "tech": ["科技", "全息", "扫描", "数据"],
    "memory": ["回忆", "黑白", "泛黄", "柔光"],
    "horror": ["恐怖", "惊悚", "暗黑", "血"],
    "happy": ["欢乐", "跳动", "弹力"],
}

def expand_query_with_synonyms(query):
    """
    将用户的英文查询词扩展为中文同义词列表。
    例如: "glitch" -> ["glitch", "故障", "干扰", "燥波", "雪花"]
    """
    terms = query.lower().split()
    expanded_terms = set(terms)
    
    for term in terms:
        # 直接匹配
        if term in SYNONYMS:
            expanded_terms.update(SYNONYMS[term])
        # 模糊匹配 (如果 term 是 synonym 的一部分)
        else:
            for key, values in SYNONYMS.items():
                if term in key:  # 比如搜 "typewrite" 匹配 "typewriter"
                    expanded_terms.update(values)
                    
    return list(expanded_terms)

def search_assets(query, category=None, limit=20):
    """
    在 CSV 数据中搜索资产。
    query: 搜索关键词
    """
    results = []
    
    # 1. 扩展查询词
    search_terms = expand_query_with_synonyms(query)
    # print(f"DEBUG: Searching for terms: {search_terms}")
    
    files_to_search = []
    if category:
        if not category.endswith('.csv'):
            category += '.csv'
        files_to_search = [category]
    else:
        if os.path.exists(DATA_DIR):
            files_to_search = [f for f in os.listdir(DATA_DIR) if f.endswith('.csv')]
        else:
            print(f"❌ Error: Data directory not found at {DATA_DIR}")
            return []

    for filename in files_to_search:
        filepath = os.path.join(DATA_DIR, filename)
        if not os.path.exists(filepath):
            continue
            
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # 匹配标识符、描述或分类
                # 构造一个宽泛的搜索文本
                target_text = (row.get('identifier', '') + " " + 
                               row.get('description', '') + " " + 
                               row.get('category', '')).lower()
                
                # 只要任何一个同义词命中即可 (OR logic for synonyms)
                # 但如果是多词查询 "tech glitch"，我们可能希望是 AND 逻辑?
                # 为了简单起见，我们假设 search_terms 里的词，只要命中一个就算相关。
                # 但为了精准，我们优先匹配原始 query。
                
                # 评分逻辑:
                # 1. 精确包含原始 query: 100分
                # 2. 包含任意同义词: 10分
                
                score = 0
                if query.lower() in target_text:
                    score += 100
                
                for term in search_terms:
                    if term in target_text:
                        score += 10
                
                if score > 0:
                    row['score'] = score
                    row['source_file'] = filename
                    results.append(row)

    # 按分数排序
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:limit]

def format_results(results):
    if not results:
        return "❌ 未找到匹配项。尝试使用更简单的中文关键词。"
    
    output = []
    # 增加 Source 列，方便知道是哪个分类里的
    output.append(f"{'Identifier':<30} | {'Category':<15} | {'Source'}")
    output.append("-" * 70)
    for r in results:
        # 截断过长的 identifier
        ident = r.get('identifier', 'N/A')
        if len(ident) > 28: ident = ident[:25] + "..."
        
        cat = r.get('category', 'N/A')[:15]
        src = r.get('source_file', '').replace('.csv', '')
        
        output.append(f"{ident:<30} | {cat:<15} | {src}")
        
    return "\n".join(output)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="剪映资产搜索工具 (智能双语版)")
    parser.add_argument("query", nargs="?", default=None, help="搜索关键词 (支持中英文、同义词)")
    parser.add_argument("-c", "--category", help="限定分类 (例如: filters, text_animations)")
    parser.add_argument("-l", "--limit", type=int, default=20, help="返回结果数量限制")
    parser.add_argument("--list", action="store_true", help="列出所有可用分类及其数量")
    
    args = parser.parse_args()
    
    if args.list:
        # 显示分类摘要
        print("=== 剪映资产数据库概览 ===")
        print(f"{'分类文件名':<30} | {'资产数量'}")
        print("-" * 50)
        total = 0
        if os.path.exists(DATA_DIR):
            for filename in sorted(os.listdir(DATA_DIR)):
                if filename.endswith('.csv'):
                    with open(os.path.join(DATA_DIR, filename), 'r', encoding='utf-8') as f:
                        count = sum(1 for line in f) - 1
                        print(f"{filename:<30} | {count}")
                        total += count
        else:
             print("Data directory missing.")
        print("-" * 50)
        print(f"{'总计':<30} | {total}")
        sys.exit(0)

    if not args.query:
        parser.print_help()
        sys.exit(0)

    print(f"🔍 Searching for '{args.query}' (Smart Synonyms Enabled)...")
    search_results = search_assets(args.query, args.category, args.limit)
    print(format_results(search_results))
