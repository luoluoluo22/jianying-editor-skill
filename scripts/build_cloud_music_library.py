import argparse
import csv
import json
import os
from typing import Dict

from utils.logging_utils import setup_logger


logger = setup_logger("build_cloud_music_library")

LOCAL_APP_DATA = os.getenv("LOCALAPPDATA")
PROJECTS_ROOT = (
    os.path.join(LOCAL_APP_DATA, r"JianyingPro\User Data\Projects\com.lveditor.draft")
    if LOCAL_APP_DATA
    else ""
)

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MUSIC_CSV = os.path.join(SKILL_ROOT, "data", "cloud_music_library.csv")
SFX_CSV = os.path.join(SKILL_ROOT, "data", "cloud_sound_effects.csv")


def load_existing_csv(path: str, id_key: str) -> Dict[str, dict]:
    library: Dict[str, dict] = {}
    if not os.path.exists(path):
        return library
    try:
        with open(path, "r", encoding="utf-8", newline="") as f:
            lines = [l for l in f if not l.startswith("#")]
        if not lines:
            return library
        reader = csv.DictReader(lines)
        for row in reader:
            m_id = row.get(id_key, "")
            if not m_id:
                continue
            cats = set((row.get("categories") or "").split("|")) if row.get("categories") else set()
            library[m_id] = {
                id_key: m_id,
                "title": row.get("title", "Unknown"),
                "duration_s": float(row.get("duration_s") or 0.0),
                "categories": {c for c in cats if c},
            }
    except Exception as e:
        logger.warning("Reading existing CSV failed (%s): %s", path, e)
    return library


def save_to_csv(path: str, library: Dict[str, dict], id_key: str, title_prefix: str) -> None:
    sorted_ids = sorted(library.keys(), key=lambda x: library[x]["title"])
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(f"# JianYing Cloud {title_prefix} Library\n")
        f.write(f"# AI Guidance: Use '{id_key}' to reference. Sync if not available.\n")
        f.write("# Schema: identifier,title,duration_s,categories\n")

        writer = csv.DictWriter(f, fieldnames=[id_key, "title", "duration_s", "categories"])
        writer.writeheader()
        for m_id in sorted_ids:
            info = library[m_id]
            writer.writerow(
                {
                    id_key: m_id,
                    "title": info["title"],
                    "duration_s": info["duration_s"],
                    "categories": "|".join(sorted(list(info["categories"]))),
                }
            )


def build_libraries(
    projects_root: str = PROJECTS_ROOT,
    music_csv: str = MUSIC_CSV,
    sfx_csv: str = SFX_CSV,
    dry_run: bool = False,
) -> tuple[int, dict]:
    logger.info("Scanning Jianying projects for cloud assets...")

    if not projects_root or not os.path.exists(projects_root):
        logger.error("Projects root not found: %s", projects_root or "<LOCALAPPDATA missing>")
        return 1, {"ok": False, "reason": "projects_root_missing", "projects_root": projects_root}

    music_lib = load_existing_csv(music_csv, "music_id")
    sfx_lib = load_existing_csv(sfx_csv, "effect_id")
    skipped_projects = 0

    for project_name in os.listdir(projects_root):
        project_path = os.path.join(projects_root, project_name)
        if not os.path.isdir(project_path):
            continue
        content_path = os.path.join(project_path, "draft_content.json")
        if not os.path.exists(content_path):
            continue

        try:
            with open(content_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            audios = data.get("materials", {}).get("audios", [])
            for audio in audios:
                m_type = audio.get("type")
                title = audio.get("name", "Unknown")
                duration_us = int(audio.get("duration", 0) or 0)
                category = audio.get("category_name")

                if m_type == "music":
                    m_id = str(audio.get("music_id") or audio.get("id") or "")
                    if not m_id:
                        continue
                    if m_id not in music_lib:
                        music_lib[m_id] = {
                            "music_id": m_id,
                            "title": title,
                            "duration_s": round(duration_us / 1_000_000, 2),
                            "categories": set(),
                        }
                    if category:
                        music_lib[m_id]["categories"].add(category)
                elif m_type == "sound":
                    e_id = str(audio.get("effect_id") or "")
                    if not e_id:
                        continue
                    if e_id not in sfx_lib:
                        sfx_lib[e_id] = {
                            "effect_id": e_id,
                            "title": title,
                            "duration_s": round(duration_us / 1_000_000, 2),
                            "categories": set(),
                        }
                    if category:
                        sfx_lib[e_id]["categories"].add(category)
        except Exception as e:
            logger.warning("Skipping project '%s': %s", project_name, e)
            skipped_projects += 1

    if not dry_run:
        save_to_csv(music_csv, music_lib, "music_id", "Music")
        save_to_csv(sfx_csv, sfx_lib, "effect_id", "Sound Effects")
    logger.info("Success. Music=%d, SFX=%d", len(music_lib), len(sfx_lib))
    return 0, {
        "ok": True,
        "projects_root": projects_root,
        "music_count": len(music_lib),
        "sfx_count": len(sfx_lib),
        "skipped_projects": skipped_projects,
        "dry_run": dry_run,
        "music_csv": music_csv,
        "sfx_csv": sfx_csv,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build cloud music/sfx library from local drafts")
    parser.add_argument("--projects-root", default=PROJECTS_ROOT, help="JianYing draft projects root")
    parser.add_argument("--music-csv", default=MUSIC_CSV, help="Output music csv path")
    parser.add_argument("--sfx-csv", default=SFX_CSV, help="Output sound effects csv path")
    parser.add_argument("--dry-run", action="store_true", help="Scan only, do not write csv")
    parser.add_argument("--json", action="store_true", help="Output JSON summary")
    args = parser.parse_args()

    exit_code, summary = build_libraries(
        projects_root=args.projects_root,
        music_csv=args.music_csv,
        sfx_csv=args.sfx_csv,
        dry_run=args.dry_run,
    )
    if args.json:
        print(json.dumps(summary, ensure_ascii=False))
    raise SystemExit(exit_code)
