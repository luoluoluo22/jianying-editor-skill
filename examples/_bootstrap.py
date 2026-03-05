import os
import sys
from typing import List, Optional, Tuple


def _build_candidates(start_dir: str) -> List[str]:
    cwd = os.getcwd()
    return [
        os.path.abspath(start_dir),
        os.path.abspath(os.path.join(start_dir, "..")),
        os.path.abspath(os.path.join(start_dir, "..", "..")),
        os.path.abspath(os.path.join(start_dir, ".agent", "skills", "jianying-editor")),
        os.path.abspath(os.path.join(start_dir, ".trae", "skills", "jianying-editor")),
        os.path.abspath(os.path.join(start_dir, ".claude", "skills", "jianying-editor")),
        os.path.abspath(os.path.join(start_dir, "skills", "jianying-editor")),
        os.path.abspath(os.path.join(cwd, ".agent", "skills", "jianying-editor")),
        os.path.abspath(os.path.join(cwd, ".trae", "skills", "jianying-editor")),
        os.path.abspath(os.path.join(cwd, ".claude", "skills", "jianying-editor")),
        os.path.abspath(os.path.join(cwd, "skills", "jianying-editor")),
    ]


def resolve_skill_root(start_dir: str) -> Optional[str]:
    env_root = os.getenv("JY_SKILL_ROOT", "").strip()
    if env_root:
        env_root = os.path.abspath(env_root)
        if os.path.exists(os.path.join(env_root, "scripts", "jy_wrapper.py")):
            return env_root

    for candidate in _build_candidates(start_dir):
        if os.path.exists(os.path.join(candidate, "scripts", "jy_wrapper.py")):
            return candidate
    return None


def resolve_skill_root_or_raise(start_dir: str) -> str:
    root = resolve_skill_root(start_dir)
    if root:
        return root
    raise ImportError("Could not locate jianying-editor skill root. Set JY_SKILL_ROOT.")


def ensure_skill_scripts_on_path(start_dir: str) -> Tuple[str, str]:
    skill_root = resolve_skill_root_or_raise(start_dir)
    scripts_dir = os.path.join(skill_root, "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    return skill_root, scripts_dir
