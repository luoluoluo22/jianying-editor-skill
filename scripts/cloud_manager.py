import os
import csv
import json
import requests
import re
import argparse
import ipaddress
from urllib.parse import urlparse
from typing import Optional, Dict

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(SKILL_ROOT)))
CACHE_DIR = os.path.join(WORKSPACE_ROOT, "cloud_cache")
MAX_DOWNLOAD_BYTES = int(float(os.getenv("JY_CLOUD_MAX_MB", "512")) * 1024 * 1024)
ALLOWED_SCHEMES = {"http", "https"}

class CloudManager:
    def __init__(self):
        self.assets = self._load_database()
        if not os.path.exists(CACHE_DIR):
            os.makedirs(CACHE_DIR)

    def _load_database(self) -> Dict[str, dict]:
        """从多个资源库加载索引"""
        assets = {}
        db_files = [
            "cloud_music_library.csv",
            "cloud_video_assets.csv",
            "cloud_sound_effects.csv"
        ]
        
        for db_name in db_files:
            path = os.path.join(SKILL_ROOT, "data", db_name)
            if not os.path.exists(path): continue
            
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    # 过滤备注行并解析
                    lines = [l for l in f.readlines() if not l.startswith('#')]
                    reader = csv.DictReader(lines)
                    for row in reader:
                        # 兼容不同列名: music_id -> id, title -> name
                        eid = row.get('id') or row.get('music_id') or row.get('effect_id')
                        name = row.get('name') or row.get('title') or row.get('name_hint')
                        dur = row.get('duration_s') or row.get('duration')
                        
                        if eid:
                            assets[str(eid)] = {
                                "id": str(eid),
                                "name": str(name),
                                "url": row.get('url', ''),
                                "duration_s": float(dur) if dur and str(dur).replace('.','',1).isdigit() else None,
                                "type": row.get('type') or row.get('categories', 'unknown'),
                                "source_db": db_name
                            }
            except Exception as e:
                print(f"Error loading {db_name}: {e}")
        
        if assets:
            print(f"✅ Cloud Manager: {len(assets)} items indexed.")
        return assets

    def find_asset(self, query: str) -> Optional[dict]:
        """根据 ID 或名称模糊查找素材"""
        # 1. 尝试 ID 精确匹配
        if query in self.assets:
            return self.assets[query]
        
        # 2. 尝试名称模糊匹配
        for asset in self.assets.values():
            if query.lower() in asset['name'].lower():
                return asset
        return None

    def get_asset_duration(self, query: str) -> Optional[float]:
        """快速获取素材时长"""
        asset = self.find_asset(query)
        if asset:
            return asset.get('duration_s')
        return None

    def get_url_from_logs(self, effect_id: str) -> Optional[str]:
        """从本地监听日志中实时提取最新的授权 URL"""
        workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(SKILL_ROOT)))
        
        log_files = [
            os.path.join(workspace_root, "mitmdump_assets_capture.log"),
            os.path.join(workspace_root, "mitmdump_media_full.log"),
            r"d:\jianying\网页剪辑\mitmdump_assets_capture.log"
        ]
        
        # 更加精确的匹配逻辑：寻找包含 ID 的 JSON 片段
        # 这里的思路是找到 ID 后，在接下来的 5000 字符内寻找第一个 URL (通常 URL 紧随其后)
        for log_path in log_files:
            if not os.path.exists(log_path): continue
            
            with open(log_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 使用更精细的正则：匹配 ID 后跟着的一段区域
            # 我们找 "effect_id":"ID" 之后到下一个 "effect_id" 之前的内容
            id_pattern = f'"(?:effect_id|id)":"{effect_id}"'
            matches = list(re.finditer(id_pattern, content))
            
            if not matches: continue
            
            # 从最后的匹配项开始（通常是最新的授权）
            for m in reversed(matches):
                start_pos = m.end()
                # 往后看 10000 字符，通常包含该物料的所有字段（包括视频地址）
                search_region = content[start_pos : start_pos + 10000]
                
                # 在这个范围内寻找第一个 URL
                url_match = re.search(r'https?://[^\s"\'\]]+(?:\.mp4|\.webm|\.zip|\.7z|a=4066)[^\s"\'\]]*', search_region, re.IGNORECASE)
                if url_match:
                    url = url_match.group(0).replace('\\u0026', '&').replace('\\/', '/')
                    return url
        return None

    def _is_safe_download_url(self, url: str) -> bool:
        try:
            parsed = urlparse(url)
            if parsed.scheme.lower() not in ALLOWED_SCHEMES:
                return False
            host = (parsed.hostname or "").strip().lower()
            if not host:
                return False
            if host in {"localhost", "127.0.0.1", "::1"}:
                return False
            try:
                ip = ipaddress.ip_address(host)
                if ip.is_private or ip.is_loopback or ip.is_link_local:
                    return False
            except ValueError:
                # 不是纯 IP，当作域名处理
                pass
            return True
        except Exception:
            return False

    def _validate_response_headers(self, res: requests.Response) -> bool:
        content_type = (res.headers.get("Content-Type") or "").lower()
        if content_type.startswith("text/html") or content_type.startswith("application/json"):
            return False
        if content_type and not (
            "video/" in content_type
            or "audio/" in content_type
            or "application/octet-stream" in content_type
            or "application/zip" in content_type
            or "binary/octet-stream" in content_type
        ):
            # 对未知类型保守拒绝，降低下载错误页面或脚本内容的风险
            return False
        content_length = res.headers.get("Content-Length")
        if content_length and content_length.isdigit() and int(content_length) > MAX_DOWNLOAD_BYTES:
            return False
        return True

    def download_asset(self, query: str, force: bool = False) -> Optional[str]:
        """
        下载云端素材并返回本地路径。
        如果已在缓存中则直接返回。
        """
        asset = self.find_asset(query)
        if not asset:
            print(f"[-] Cloud Asset '{query}' not found in database.")
            return None
        
        eid = asset['id']
        safe_name = "".join([c for c in asset['name'] if c.isalnum() or c in (' ', '_')]).strip()
        local_filename = f"{eid}_{safe_name}.mp4"
        local_path = os.path.join(CACHE_DIR, local_filename)

        if os.path.exists(local_path) and not force:
            return local_path

        # 需要下载
        # 1. 优先尝试从数据库中获取已有的 URL
        url = asset.get('url')
        
        # 2. 如果数据库中没有，或者用户要求强刷，则从日志中寻找
        if not url or force:
            url = self.get_url_from_logs(eid)
            
        if not url:
            print(f"[-] No valid download URL found for ID {eid}. Please browse this asset in JianYing while sniffer is running.")
            return None
        if not self._is_safe_download_url(url):
            print(f"[-] Unsafe download URL blocked for ID {eid}: {url}")
            return None

        print(f"[*] Downloading Cloud Asset: {asset['name']}...")
        try:
            res = requests.get(url, stream=True, timeout=60)
            res.raise_for_status()
            if not self._validate_response_headers(res):
                print(f"[-] Download blocked by header validation for ID {eid}.")
                return None

            tmp_path = local_path + ".part"
            total = 0
            with open(tmp_path, 'wb') as f:
                for chunk in res.iter_content(chunk_size=32768):
                    if not chunk:
                        continue
                    total += len(chunk)
                    if total > MAX_DOWNLOAD_BYTES:
                        raise ValueError(f"Download exceeds size limit: {MAX_DOWNLOAD_BYTES} bytes")
                    f.write(chunk)
            os.replace(tmp_path, local_path)
            print(f"[+] Download Finished: {local_path}")
            return local_path
        except Exception as e:
            part = local_path + ".part"
            if os.path.exists(part):
                try:
                    os.remove(part)
                except Exception:
                    pass
            print(f"[-] Download Error: {e}")
            return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="JianYing Cloud Asset Manager")
    parser.add_argument("query", help="ID or Name of the asset")
    parser.add_argument("--force", action="store_true", help="Force redownload")
    args = parser.parse_args()

    manager = CloudManager()
    path = manager.download_asset(args.query, args.force)
    if path:
        print(f"RESULT_PATH|{path}")
