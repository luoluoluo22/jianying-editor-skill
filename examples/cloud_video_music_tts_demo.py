import os

from _bootstrap import ensure_skill_scripts_on_path

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_, _ = ensure_skill_scripts_on_path(CURRENT_DIR)

from jy_wrapper import JyProject


def main() -> None:
    project = JyProject("Cloud_Video_Music_TTS_Demo", overwrite=True)

    video_candidates = [
        "6969200777839594759",
        "6969200708755279140",
        "科技风片头",
    ]
    video_seg = None
    for query in video_candidates:
        video_seg = project.add_cloud_media(query, start_time="0s", duration="4s", track_name="CloudVideo")
        if video_seg is not None:
            print(f"[ok] cloud video loaded: {query}")
            break
    if video_seg is None:
        print("[warn] cloud video failed for all candidates")

    cursor = 500000
    tts_plan = [
        ("zh_female_xiaopengyou", "第一段，小孩音色测试。"),
        ("BV701_streaming", "第二段，解说音色测试。"),
        ("zh_male_iclvop_xiaolinkepu", "第三段，男声音色测试。"),
    ]
    for idx, (speaker, text) in enumerate(tts_plan, start=1):
        cursor = project.add_narrated_subtitles(
            text=text,
            speaker=speaker,
            start_time=cursor,
            track_name=f"TTS_Sub_{idx}",
        )
        cursor += 300000

    music_candidates = [
        "7377952090247219263",
        "7377847594314287123",
        "科技",
    ]
    music_seg = None
    for query in music_candidates:
        music_seg = project.add_cloud_music(query, start_time=cursor, duration="8s")
        if music_seg is not None:
            print(f"[ok] cloud music loaded: {query}")
            break
    if music_seg is None:
        print("[warn] cloud music failed for all candidates")

    project.add_text_simple(
        "Cloud Video + Cloud Music + Multi-Voice TTS",
        start_time="0.2s",
        duration="3s",
        track_name="TitleTrack",
        anim_in="复古打字机",
    )

    result = project.save()
    print(f"Draft generated: {result.get('draft_path')}")


if __name__ == "__main__":
    main()
