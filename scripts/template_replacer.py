import os
import sys

# 修复导入路径 (向上跳 5 级)
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.append(root_dir)
import pyJianYingDraft as draft

def replace_draft_text(draft_name, text_replacements, drafts_root=None):
    if not drafts_root:
        drafts_root = r"C:\Users\Administrator\AppData\Local\JianyingPro\User Data\Projects\com.lveditor.draft"
    
    df = draft.DraftFolder(drafts_root)
    new_name = f"{draft_name}_replaced"
    script = df.duplicate_as_template(draft_name, new_name, allow_replace=True)
    
    try:
        text_track = script.get_imported_track(draft.TrackType.text, index=0)
        for i in range(len(text_track.segments)):
            if i == 0 and "TITLE" in text_replacements:
                 script.replace_text(text_track, i, text_replacements["TITLE"])
        
        script.save()
        print(f"✅ 成功生成替换后的草稿: {new_name}")
    except Exception as e:
        print(f"❌ 替换失败: {str(e)}")

if __name__ == "__main__":
    print("Template Replacer 准备就绪。")
