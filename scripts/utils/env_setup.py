import os
import sys

def setup_env():
    """
    统一初始化 JianYing Editor Skill 运行环境。
    将 scripts、references 及跨 Skill 的依赖路径注入到 sys.path 中。
    """
    try:
        current_frame = sys._getframe(1)
        caller_file = current_frame.f_globals.get('__file__')
        if caller_file:
            start_dir = os.path.dirname(os.path.abspath(caller_file))
        else:
            start_dir = os.getcwd()
    except Exception:
        start_dir = os.getcwd()

    skill_root = None
    
    possible_roots = [
        start_dir,
        os.path.join(start_dir, ".."),
        os.path.join(start_dir, "..", ".."),
        os.path.join(start_dir, ".agent", "skills", "jianying-editor"),
        os.path.join(os.getcwd(), ".agent", "skills", "jianying-editor"),
        os.path.join(os.getcwd(), "skills", "jianying-editor"),
    ]

    for p in possible_roots:
        p = os.path.abspath(p)
        if os.path.exists(os.path.join(p, "scripts", "jy_wrapper.py")):
            skill_root = p
            break
            
    if not skill_root:
        fallback_root = os.path.join(os.getcwd(), ".agent", "skills", "jianying-editor")
        if os.path.exists(fallback_root):
            skill_root = fallback_root
            
    if skill_root:
        scripts_dir = os.path.join(skill_root, "scripts")
        references_dir = os.path.join(skill_root, "references")
        
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)
            
        if references_dir not in sys.path:
            sys.path.insert(0, references_dir)
            
        possible_api_roots = [
            os.path.join(skill_root, "..", "antigravity-api-skill", "libs"),
            os.path.abspath(os.path.join(skill_root, "../../antigravity-api-skill/libs"))
        ]
        for api_path in possible_api_roots:
            if os.path.exists(api_path) and api_path not in sys.path:
                sys.path.append(api_path)
                break
