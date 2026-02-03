import sqlite3
import os
import json
import csv
import shutil

# 1. 路径定义
LOCAL_APP_DATA = os.getenv('LOCALAPPDATA')
JY_USER_DATA = os.path.join(LOCAL_APP_DATA, r"JianyingPro\User Data")
JY_CACHE_MUSIC = os.path.join(JY_USER_DATA, r"Cache\music")

# Skill 根目录 (scripts 的上一级)
SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Sync to Project Root's assets folder, not inside .agent/skills
PROJECT_ROOT = os.path.dirname(SKILL_ROOT) # Assuming SKILL_ROOT is .agent/skills/jianying-editor, go up 3 levels?
# Better: Just assume we run from project root or find it relative to script
# If script is in .agent/skills/jianying-editor/scripts/sync_jy_assets.py
# SKILL_ROOT is .agent/skills/jianying-editor
# We want f:\Desktop\kaifa\jianying-editor-skill\assets\jy_sync
PROJECT_ROOT = os.path.abspath(os.path.join(SKILL_ROOT, "..", "..", "..")) 
DEST_DIR = os.path.join(PROJECT_ROOT, "assets", "jy_sync")
DATA_DIR = os.path.join(SKILL_ROOT, "data")

def sync_music_cache_robust():
    print(f"🔄 Starting Robust Sync from: {JY_CACHE_MUSIC}")
    
    # 1. 读取 downLoadcfg 获取物理文件映射
    cfg_path = os.path.join(JY_CACHE_MUSIC, "downLoadcfg")
    if not os.path.exists(cfg_path):
        print("❌ 'downLoadcfg' not found. Have you played any music in JianYing?")
        return

    try:
        with open(cfg_path, 'r', encoding='utf-8') as f:
            cfg_data = json.load(f)
            file_list = cfg_data.get('list', [])
    except Exception as e:
        print(f"❌ Error reading downLoadcfg: {e}")
        return

    if not file_list:
        print("ℹ️ No cached music found in config.")
        return

    # 2. 尝试连接数据库获取元数据 (Best Effort)
    # 收集所有 rp.db
    db_map = {} # mid -> {name, author}
    db_root = os.path.join(JY_USER_DATA, r"Cache\ressdk_db")
    if os.path.exists(db_root):
        for root, dirs, files in os.walk(db_root):
            if "rp.db" in files:
                try:
                    conn = sqlite3.connect(os.path.join(root, "rp.db"))
                    cursor = conn.cursor()
                    # 尝试从 music 表读取
                    try:
                        cursor.execute("SELECT id, title, author FROM music")
                        for r in cursor.fetchall():
                            db_map[r[0]] = {"name": r[1], "author": r[2]}
                    except: pass
                    conn.close()
                except: pass
    
    # 3. 处理文件与同步
    if os.path.exists(DEST_DIR):
        shutil.rmtree(DEST_DIR)
    os.makedirs(DEST_DIR)

    synced_items = []
    
    print(f"📂 Found {len(file_list)} files in cache config.")

    for item in file_list:
        mid_hex = item.get('hex') # This might be the ID
        file_name = item.get('path')
        src_path = os.path.join(JY_CACHE_MUSIC, file_name)
        
        if not os.path.exists(src_path):
            continue
            
        # 尝试匹配元数据
        meta = db_map.get(mid_hex)
        
        # 命名策略
        if meta:
            display_name = meta['name']
            author = meta['author']
            cat = "jy_internal"
        else:
            # Fallback: 使用 Hex 前6位
            display_name = f"JY_Cached_{mid_hex[:6]}"
            author = "Unknown"
            cat = "jy_cached_unknown"

        # 复制到 Skill 目录 (重命名为易读格式)
        # 清理文件名中的非法字符
        safe_name = "".join([c for c in display_name if c.isalnum() or c in (' ', '_', '-')]).strip()
        if not safe_name: safe_name = f"Music_{mid_hex[:6]}"
        
        dest_filename = f"{safe_name}.mp3"
        dest_path = os.path.join(DEST_DIR, dest_filename)
        
        try:
            shutil.copy2(src_path, dest_path)
            
            synced_items.append({
                "identifier": display_name,         # 供搜索用
                "author": author,
                "duration": "0", # TODO: Get exact duration if needed
                "path": dest_path,                  # 这里直接指向我们同步过来的文件
                "category": cat
            })
            print(f"   ✅ Synced: {display_name} -> {dest_filename}")
        except Exception as e:
            print(f"   ⚠️ Copy failed for {file_name}: {e}")

    # 4. 保存 CSV 索引
    if synced_items:
        csv_path = os.path.join(DATA_DIR, "jy_cached_audio.csv")
        with open(csv_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["identifier", "author", "duration", "path", "category"])
            writer.writeheader()
            writer.writerows(synced_items)
        print(f"\n🎉 Sync Complete! {len(synced_items)} assets imported to {DEST_DIR}")
        print(f"📋 Index saved to {csv_path}")
    else:
        print("❌ No valid assets synced.")

if __name__ == "__main__":
    sync_music_cache_robust()
