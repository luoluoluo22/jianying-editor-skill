import os
import sys

from utils.skill_path import resolve_skill_root


def _guard_stdio_encoding():
    """
    让 stdout/stderr 在 GBK 等窄编码代码页下不因 emoji 崩溃。

    Windows 默认代码页（cp936/GBK）无法编码 ✅❌⚠️ℹ️🎉 等 emoji，
    裸 print 会抛 UnicodeEncodeError。把 errors 策略降级为 replace，
    但从不改 encoding —— 保留终端原有编码与输出行为，
    仅让不可编码字符变成 '?' 而不是中断进程。
    """
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        # StringIO / 已重定向的流可能没有 reconfigure，跳过即可
        if stream is None or not hasattr(stream, "reconfigure"):
            continue
        try:
            if getattr(stream, "errors", None) != "replace":
                stream.reconfigure(errors="replace")
        except (ValueError, OSError):
            # 流已被关闭或不可重配置时保持静默，不影响主流程
            pass


def setup_env():
    """
    统一初始化 JianYing Editor Skill 运行环境。
    将 scripts、vendor 及跨 Skill 的依赖路径注入到 sys.path 中。
    """
    _guard_stdio_encoding()

    try:
        current_frame = sys._getframe(1)
        caller_file = current_frame.f_globals.get('__file__')
        if caller_file:
            start_dir = os.path.dirname(os.path.abspath(caller_file))
        else:
            start_dir = os.getcwd()
    except Exception:
        start_dir = os.getcwd()

    skill_root, _ = resolve_skill_root(start_dir)
            
    if skill_root:
        scripts_dir = os.path.join(skill_root, "scripts")
        vendor_dir = os.path.join(scripts_dir, "vendor")
        
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)
            
        if vendor_dir not in sys.path:
            sys.path.insert(0, vendor_dir)
            
        possible_api_roots = [
            os.path.join(skill_root, "..", "antigravity-api-skill", "libs"),
            os.path.abspath(os.path.join(skill_root, "../../antigravity-api-skill/libs"))
        ]
        for api_path in possible_api_roots:
            if os.path.exists(api_path) and api_path not in sys.path:
                sys.path.append(api_path)
                break
