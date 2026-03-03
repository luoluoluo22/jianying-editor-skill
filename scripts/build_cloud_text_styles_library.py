import os
import json
import csv

# 路径定义
LOCAL_APP_DATA = os.getenv('LOCALAPPDATA')
PROJECTS_ROOT = os.path.join(LOCAL_APP_DATA, r"JianyingPro\User Data\Projects\com.lveditor.draft")

# Skill 根目录
SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_FILE = os.path.join(SKILL_ROOT, "data", "cloud_text_styles.csv")

def build_text_styles_library():
    print(f"🔍 Scanning Jianying projects for styled text (Flower Text)...")
    
    # 1. 尝试增量读取现有的库
    style_library = {} # style_id -> {style_id, name_hint, categories (set)}
    
    if os.path.exists(CSV_FILE):
        try:
            with open(CSV_FILE, 'r', encoding='utf-8', newline='') as f:
                lines = [l for l in f.readlines() if not l.startswith("#")]
                if lines:
                    reader = csv.DictReader(lines)
                    for row in reader:
                        s_id = row['style_id']
                        cats = set(row['categories'].split('|')) if row['categories'] else set()
                        style_library[s_id] = {
                            "style_id": s_id,
                            "name_hint": row['name_hint'],
                            "categories": cats
                        }
        except Exception as e:
            print(f"⚠️ Reading existing CSV failed: {e}")

    if os.path.exists(PROJECTS_ROOT):
        # 2. 遍历所有工程文件夹
        for project_name in os.listdir(PROJECTS_ROOT):
            project_path = os.path.join(PROJECTS_ROOT, project_name)
            if not os.path.isdir(project_path):
                continue
                
            content_path = os.path.join(project_path, "draft_content.json")
            if not os.path.exists(content_path):
                continue
                
            try:
                with open(content_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    texts = data.get('materials', {}).get('texts', [])
                    for t in texts:
                        content = t.get('content')
                        if not content: continue
                        
                        try:
                            content_json = json.loads(content)
                            styles = content_json.get('styles', [])
                            for sty in styles:
                                eff = sty.get('effectStyle', {})
                                s_id = eff.get('id')
                                if not s_id: continue
                                
                                # 使用文本内容作为提示，除非是“默认文本”
                                raw_text = content_json.get('text', '')
                                hint = raw_text if raw_text != "默认文本" else "Flower Style"
                                
                                if s_id not in style_library:
                                    style_library[s_id] = {
                                        "style_id": s_id,
                                        "name_hint": hint,
                                        "categories": {project_name} # 使用工程名作为初期分类
                                    }
                                else:
                                    if hint != "Flower Style" and style_library[s_id]["name_hint"] == "Flower Style":
                                        style_library[s_id]["name_hint"] = hint
                                    style_library[s_id]["categories"].add(project_name)
                        except:
                            pass
            except Exception as e:
                print(f"⚠ Skipping project '{project_name}': {e}")
    else:
        print("❌ Projects root not found.")

    # 4. 写入 CSV
    os.makedirs(os.path.dirname(CSV_FILE), exist_ok=True)
    sorted_ids = sorted(style_library.keys())
    
    with open(CSV_FILE, 'w', encoding='utf-8', newline='') as f:
        f.write("# JianYing Cloud Text Styles Library (Flower Text IDs Scanned from Projects)\n")
        f.write("# AI Guidance: Use 'style_id' in add_styled_text(). If matching name found, use ID.\n")
        f.write("# Schema: style_id,name_hint,categories\n")
        
        writer = csv.DictWriter(f, fieldnames=["style_id", "name_hint", "categories"])
        writer.writeheader()
        for s_id in sorted_ids:
            info = style_library[s_id]
            writer.writerow({
                "style_id": s_id,
                "name_hint": info["name_hint"],
                "categories": "|".join(sorted(list(info["categories"])))
            })

    print(f"✅ Success! Text Styles Library updated with {len(style_library)} entries.")
    print(f"📂 Saved to: {CSV_FILE}")

if __name__ == "__main__":
    build_text_styles_library()
