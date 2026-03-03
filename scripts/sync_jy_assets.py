import sqlite3
import os
import json
import csv
import shutil
import subprocess

# 1. 路径定义
LOCAL_APP_DATA = os.getenv('LOCALAPPDATA')
JY_USER_DATA = os.path.join(LOCAL_APP_DATA, r"JianyingPro\User Data")
JY_CACHE_MUSIC = os.path.join(JY_USER_DATA, r"Cache\music")

# Skill 根目录 (scripts 的上一级)
SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEST_DIR = os.path.join(SKILL_ROOT, "assets", "jy_sync")
DATA_DIR = os.path.join(SKILL_ROOT, "data")

def get_duration_ffprobe(file_path):
    """尝试用 ffprobe 获取音频时长(秒)，失败返回 0"""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", file_path],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5
        )
        return round(float(result.stdout.strip()), 2)
    except Exception:
        return 0

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
        print("No cached music found in config.")
        return

    # 2. 尝试连接数据库获取元数据 (Best Effort)
    db_map = {} # mid -> {name, author}
    db_root = os.path.join(JY_USER_DATA, r"Cache\ressdk_db")
    if os.path.exists(db_root):
        for root, dirs, files in os.walk(db_root):
            if "rp.db" in files:
                try:
                    conn = sqlite3.connect(os.path.join(root, "rp.db"))
                    cursor = conn.cursor()
                    try:
                        cursor.execute("SELECT id, title, author FROM music")
                        for r in cursor.fetchall():
                            db_map[r[0]] = {"name": r[1], "author": r[2]}
                    except Exception:
                        pass
                    conn.close()
                except Exception:
                    pass
    
    # 3. 读取现有 CSV 索引以实现增量同步
    csv_path = os.path.join(DATA_DIR, "jy_cached_audio.csv")
    existing_ids = set()
    existing_items = []
    if os.path.exists(csv_path):
        try:
            with open(csv_path, 'r', encoding='utf-8', newline='') as f:
                lines = [l for l in f.readlines() if not l.startswith("#")]
                if lines:
                    reader = csv.DictReader(lines)
                    for row in reader:
                        existing_items.append(row)
                        existing_ids.add(row.get('identifier', ''))
        except Exception as e:
            print(f"⚠ Reading existing CSV failed: {e}")

    # 4. 处理文件与同步 (增量)
    os.makedirs(DEST_DIR, exist_ok=True)
    new_count = 0

    print(f"📂 Found {len(file_list)} files in cache config. Existing: {len(existing_ids)} synced.")

    for item in file_list:
        mid_hex = item.get('hex')
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
            display_name = f"JY_Cached_{mid_hex[:6]}"
            author = "Unknown"
            cat = "jy_cached_unknown"

        # 跳过已存在的 (增量)
        if display_name in existing_ids:
            continue

        # 复制到 Skill 目录
        safe_name = "".join([c for c in display_name if c.isalnum() or c in (' ', '_', '-')]).strip()
        if not safe_name: safe_name = f"Music_{mid_hex[:6]}"
        
        dest_filename = f"{safe_name}.mp3"
        dest_path = os.path.join(DEST_DIR, dest_filename)
        
        try:
            shutil.copy2(src_path, dest_path)
            
            # 尝试获取真实时长
            duration = get_duration_ffprobe(dest_path)
            
            existing_items.append({
                "identifier": display_name,
                "author": author,
                "duration": str(duration),
                "path": dest_path,
                "category": cat
            })
            existing_ids.add(display_name)
            new_count += 1
            print(f"   + Synced: {display_name} ({duration}s)")
        except Exception as e:
            print(f"   ⚠ Copy failed for {file_name}: {e}")

    # 5. 保存 CSV 索引 (带引导注释)
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        f.write("# JianYing Cached Audio Assets (Physical files synced via sync_jy_assets.py)\n")
        f.write("# AI Guidance: These files exist locally. Use 'path' column directly with add_audio_safe().\n")
        f.write("# To refresh: run 'python scripts/sync_jy_assets.py'\n")
        writer = csv.DictWriter(f, fieldnames=["identifier", "author", "duration", "path", "category"])
        writer.writeheader()
        writer.writerows(existing_items)
    
    print(f"\n🎉 Sync Complete! +{new_count} new, {len(existing_items)} total assets.")
    print(f"📂 Assets dir: {DEST_DIR}")
    print(f"📋 Index: {csv_path}")

if __name__ == "__main__":
    sync_music_cache_robust()
