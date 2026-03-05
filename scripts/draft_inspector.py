import argparse
import json
import os
from typing import Any, Dict, List, Optional

from utils.formatters import get_all_drafts, get_default_drafts_root


def _ok(data: Dict[str, Any]) -> Dict[str, Any]:
    return {"ok": True, "code": "ok", "reason": "", "data": data}


def _err(code: str, reason: str) -> Dict[str, Any]:
    return {"ok": False, "code": code, "reason": reason, "data": {}}


def _find_draft(root: str, name: str) -> Optional[Dict[str, Any]]:
    for d in get_all_drafts(root):
        if d["name"] == name:
            return d
    return None


def _read_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def cmd_list(root: str, limit: int) -> Dict[str, Any]:
    drafts = get_all_drafts(root)
    if limit > 0:
        drafts = drafts[:limit]
    return _ok({"root": root, "count": len(drafts), "drafts": drafts})


def cmd_show(root: str, name: Optional[str], path: Optional[str], kind: str) -> Dict[str, Any]:
    if not name and not path:
        return _err("invalid_input", "Either --name or --path is required.")

    draft_path: Optional[str] = None
    draft_name = ""

    if path:
        draft_path = os.path.abspath(path)
        draft_name = os.path.basename(draft_path.rstrip("\\/"))
    else:
        found = _find_draft(root, name or "")
        if not found:
            return _err("not_found", f"Draft not found: {name}")
        draft_path = found["path"]
        draft_name = found["name"]

    content_path = os.path.join(draft_path, "draft_content.json")
    meta_path = os.path.join(draft_path, "draft_meta_info.json")

    data: Dict[str, Any] = {"name": draft_name, "path": draft_path}

    try:
        if kind in {"content", "both"}:
            if not os.path.exists(content_path):
                return _err("not_found", f"Missing draft_content.json: {content_path}")
            data["content"] = _read_json(content_path)

        if kind in {"meta", "both"}:
            if not os.path.exists(meta_path):
                return _err("not_found", f"Missing draft_meta_info.json: {meta_path}")
            data["meta"] = _read_json(meta_path)

        return _ok(data)
    except json.JSONDecodeError as e:
        return _err("invalid_json", f"JSON decode failed: {e}")
    except OSError as e:
        return _err("io_error", str(e))


def cmd_summary(root: str, name: Optional[str], path: Optional[str]) -> Dict[str, Any]:
    show = cmd_show(root=root, name=name, path=path, kind="content")
    if not show["ok"]:
        return show

    payload = show["data"]
    content = payload["content"]
    tracks: List[Dict[str, Any]] = content.get("tracks", [])
    materials = content.get("materials", {}) or {}

    track_summaries: List[Dict[str, Any]] = []
    total_segments = 0
    for t in tracks:
        segs = t.get("segments", []) or []
        total_segments += len(segs)
        track_summaries.append(
            {
                "name": t.get("name", ""),
                "type": t.get("type", ""),
                "segment_count": len(segs),
            }
        )

    mat_counts = {}
    for k, v in materials.items():
        if isinstance(v, list):
            mat_counts[k] = len(v)

    return _ok(
        {
            "name": payload["name"],
            "path": payload["path"],
            "track_count": len(tracks),
            "segment_count": total_segments,
            "tracks": track_summaries,
            "material_counts": mat_counts,
        }
    )


def _print_human_list(res: Dict[str, Any]) -> None:
    data = res["data"]
    print(f"Root: {data['root']}")
    print(f"Drafts: {data['count']}")
    for i, d in enumerate(data["drafts"], 1):
        print(f"{i}. {d['name']} | {d['path']}")


def _print_human_summary(res: Dict[str, Any]) -> None:
    d = res["data"]
    print(f"Name: {d['name']}")
    print(f"Path: {d['path']}")
    print(f"Tracks: {d['track_count']} | Segments: {d['segment_count']}")
    print("Track details:")
    for t in d["tracks"]:
        print(f"- {t['name']} ({t['type']}): {t['segment_count']}")
    if d["material_counts"]:
        print("Materials:")
        for k, v in sorted(d["material_counts"].items()):
            print(f"- {k}: {v}")


def _print_human_show(res: Dict[str, Any]) -> None:
    print(json.dumps(res["data"], ensure_ascii=False, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect JianYing draft list and JSON files.")
    parser.add_argument("--root", default=get_default_drafts_root(), help="Draft root directory")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON response")

    sub = parser.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list", help="List drafts")
    p_list.add_argument("--limit", type=int, default=0, help="Max drafts to show (0 = all)")
    p_list.add_argument("--json", action="store_true", help="Print machine-readable JSON response")

    p_show = sub.add_parser("show", help="Show draft JSON")
    p_show.add_argument("--name", help="Draft name")
    p_show.add_argument("--path", help="Draft absolute path")
    p_show.add_argument(
        "--kind",
        choices=["content", "meta", "both"],
        default="content",
        help="Which JSON payload to print",
    )
    p_show.add_argument("--json", action="store_true", help="Print machine-readable JSON response")

    p_summary = sub.add_parser("summary", help="Show compact draft summary")
    p_summary.add_argument("--name", help="Draft name")
    p_summary.add_argument("--path", help="Draft absolute path")
    p_summary.add_argument("--json", action="store_true", help="Print machine-readable JSON response")

    args = parser.parse_args()
    root = os.path.abspath(args.root)

    if args.cmd == "list":
        res = cmd_list(root=root, limit=args.limit)
    elif args.cmd == "show":
        res = cmd_show(root=root, name=args.name, path=args.path, kind=args.kind)
    else:
        res = cmd_summary(root=root, name=args.name, path=args.path)

    want_json = bool(args.json)
    if hasattr(args, "json") and getattr(args, "json"):
        want_json = True

    if want_json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        if not res["ok"]:
            print(f"Error [{res['code']}]: {res['reason']}")
        else:
            if args.cmd == "list":
                _print_human_list(res)
            elif args.cmd == "show":
                _print_human_show(res)
            else:
                _print_human_summary(res)

    return 0 if res["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
