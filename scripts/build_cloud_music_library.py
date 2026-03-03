import os
import json
import csv

# 路径定义
LOCAL_APP_DATA = os.getenv('LOCALAPPDATA')
PROJECTS_ROOT = os.path.join(LOCAL_APP_DATA, r"JianyingPro\User Data\Projects\com.lveditor.draft")

# Skill 根目录
SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_FILE = os.path.join(SKILL_ROOT, "data", "cloud_music_library.csv")
JSON_FILE = os.path.join(SKILL_ROOT, "data", "cloud_music_library.json")

def build_pure_library():
    print(f"🔍 Scanning Jianying projects for music metadata...")
    
    # 1. 尝试增量读取现有的库
    music_library = {} # music_id -> {title, duration_s, categories (set)}
    
    # 兼容 JSON 迁移到 CSV
    if os.path.exists(JSON_FILE):
        try:
            print("📦 Found old JSON library, migrating to CSV...")
            with open(JSON_FILE, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                for m_id, info in existing_data.items():
                    info["categories"] = set(info.get("categories", []))
                    music_library[m_id] = info
        except Exception as e:
            print(f"⚠️ Migrating JSON failed: {e}")

    # 读取现有的 CSV
    if os.path.exists(CSV_FILE):
        try:
            with open(CSV_FILE, 'r', encoding='utf-8', newline='') as f:
                # 过滤注释行
                lines = [l for l in f.readlines() if not l.startswith("#")]
                if lines:
                    reader = csv.DictReader(lines)
                    for row in reader:
                        m_id = row['music_id']
                        cats = set(row['categories'].split('|')) if row['categories'] else set()
                        if m_id not in music_library:
                            music_library[m_id] = {
                                "music_id": m_id,
                                "title": row['title'],
                                "duration_s": float(row['duration_s']) if row['duration_s'] else 0.0,
                                "categories": cats
                            }
                        else:
                            music_library[m_id]["categories"].update(cats)
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
                    
                    # 3. 提取素材库中的音频
                    audios = data.get('materials', {}).get('audios', [])
                    for audio in audios:
                        m_id = audio.get('music_id') or audio.get('id')
                        if not m_id: continue
                        
                        # 只有类型为 music 的才记录
                        if audio.get('type') != 'music': continue

                        title = audio.get('name', 'Unknown')
                        duration_ms = audio.get('duration', 0)
                        category = audio.get('category_name')
                        
                        if m_id not in music_library:
                            music_library[m_id] = {
                                "music_id": m_id,
                                "title": title,
                                "duration_s": round(duration_ms / 1000000, 2),
                                "categories": set()
                            }
                        
                        if category:
                            music_library[m_id]["categories"].add(category)
            except Exception as e:
                print(f"⚠ Skipping project '{project_name}': {e}")
    else:
        print("❌ Projects root not found, only merging existing data.")

    # 4. 排序并写入 CSV
    os.makedirs(os.path.dirname(CSV_FILE), exist_ok=True)
    sorted_ids = sorted(music_library.keys(), key=lambda x: music_library[x]['title'])
    
    with open(CSV_FILE, 'w', encoding='utf-8', newline='') as f:
        # 添加引导与说明 (Guidance)
        f.write("# JianYing Cloud Music Library (Music IDs Scanned from Projects)\n")
        f.write("# AI Guidance: Use 'music_id' to reference. If found here but not in 'jy_cached_audio.csv', ask user to 'Sync Music'.\n")
        f.write("# If not found here, ask user to add music to a track first, then run 'Scan Music' (build_cloud_music_library.py).\n")
        f.write("# Schema: music_id,title,duration_s,categories\n")
        
        writer = csv.DictWriter(f, fieldnames=["music_id", "title", "duration_s", "categories"])
        writer.writeheader()
        for m_id in sorted_ids:
            info = music_library[m_id]
            writer.writerow({
                "music_id": m_id,
                "title": info["title"],
                "duration_s": info["duration_s"],
                "categories": "|".join(sorted(list(info["categories"])))
            })
    
    # 5. 清理旧 JSON 文件
    if os.path.exists(JSON_FILE):
        try:
            os.remove(JSON_FILE)
            print(f"🗑️ Old JSON library removed.")
        except: pass

    print(f"✅ Success! Library updated with {len(music_library)} entries.")
    print(f"📂 Saved to: {CSV_FILE}")

if __name__ == "__main__":
    build_pure_library()
