import os
import sys


def _locate_skill_root() -> str:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.dirname(current_dir),
        os.path.abspath(".agent/skills/jianying-editor"),
        os.path.join(current_dir, ".agent", "skills", "jianying-editor"),
    ]
    for p in candidates:
        if os.path.exists(os.path.join(p, "scripts", "jy_wrapper.py")):
            return p
    raise RuntimeError("Could not locate jianying-editor skill root")


def _bootstrap():
    skill_root = _locate_skill_root()
    scripts_dir = os.path.join(skill_root, "scripts")
    refs_dir = os.path.join(skill_root, "references")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    if refs_dir not in sys.path:
        sys.path.insert(0, refs_dir)
    return skill_root


def main() -> None:
    _bootstrap()
    from jy_wrapper import JyProject

    p = JyProject("Cloud_Video_Music_TTS_Demo", overwrite=True)

    # 1) 云端视频（优先 ID，失败则名称兜底）
    cloud_video_candidates = [
        "6969200777839594759",  # 科技风片头loading界面加载中
        "6969200708755279140",  # 潮酷片头 loading界面加载中
        "科技风片头",
    ]
    cloud_video_seg = None
    for q in cloud_video_candidates:
        cloud_video_seg = p.add_cloud_media(q, start_time="0s", duration="4s", track_name="CloudVideo")
        if cloud_video_seg is not None:
            print(f"[ok] cloud video loaded: {q}")
            break
    if cloud_video_seg is None:
        print("[warn] cloud video failed for all candidates")

    # 2) 不同音色 TTS 字幕（串行，避免重叠）
    cursor = 500000  # 0.5s
    tts_plan = [
        ("zh_female_xiaopengyou", "第一段，小孩音色测试，云端素材接入成功。"),
        ("BV701_streaming", "第二段，沉稳解说音色测试，字幕与配音对齐。"),
        ("zh_male_iclvop_xiaolinkepu", "第三段，清亮男声测试，准备衔接背景音乐。"),
    ]
    for idx, (speaker, text) in enumerate(tts_plan, start=1):
        cursor = p.add_narrated_subtitles(
            text=text,
            speaker=speaker,
            start_time=cursor,
            track_name=f"TTS_Sub_{idx}",
        )
        cursor += 300000  # 0.3s 间隔
        print(f"[ok] tts speaker={speaker}, cursor={cursor}")

    # 3) 云端音乐放在 TTS 后，避免与 AudioTrack 冲突
    cloud_music_candidates = [
        "7377952090247219263",  # 舒缓背景音乐
        "7377847594314287123",  # 企业形象进取创新
        "科技",
    ]
    cloud_music_seg = None
    for q in cloud_music_candidates:
        cloud_music_seg = p.add_cloud_music(q, start_time=cursor, duration="8s")
        if cloud_music_seg is not None:
            print(f"[ok] cloud music loaded: {q}")
            break
    if cloud_music_seg is None:
        print("[warn] cloud music failed for all candidates")

    p.add_text_simple(
        "Cloud Video + Cloud Music + Multi-Voice TTS",
        start_time="0.2s",
        duration="3s",
        track_name="TitleTrack",
        anim_in="复古打字机",
    )
    p.add_text_simple(
        "请检查三段不同音色配音与字幕",
        start_time="3.3s",
        duration="3s",
        track_name="HintTrack",
    )

    result = p.save()
    print(f"Draft generated: {result.get('draft_path')}")


if __name__ == "__main__":
    main()

