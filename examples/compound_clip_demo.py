import os
import pyJianYingDraft as draft

from _bootstrap import ensure_skill_scripts_on_path

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT, _ = ensure_skill_scripts_on_path(CURRENT_DIR)

from jy_wrapper import JyProject


def create_compound_demo() -> None:
    assets_dir = os.path.join(SKILL_ROOT, "assets")
    video_path = os.path.join(assets_dir, "video.mp4")
    if not os.path.exists(video_path):
        print(f"Video not found: {video_path}")
        return

    print("Creating sub project...")
    sub_project = JyProject("Sub_Project_Nested")
    sub_project.add_media_safe(video_path, "0s", duration="3s", track_name="SubVideo")
    sub_project.add_text_simple("Nested content", start_time="0.5s", duration="2s", font_size=10)

    print("Creating main project...")
    main_project = JyProject("Main_Project_With_Compound")
    main_project.add_media_safe(video_path, "0s", duration="8s", track_name="Background")

    if hasattr(main_project, "add_compound_project"):
        main_project.add_compound_project(
            sub_project,
            clip_name="Nested Module",
            start_time="2s",
            track_name="Overlay",
        )
    else:
        print("[warn] add_compound_project not available, fallback to overlay clip.")
        main_project.add_media_safe(video_path, "2s", duration="3s", track_name="Overlay")
        main_project.add_text_simple(
            "Compound fallback overlay",
            "2s",
            "2s",
            clip_settings=draft.ClipSettings(transform_y=0.2),
        )

    main_project.add_text_simple(
        "Main project with compound clip",
        start_time="0s",
        duration="8s",
        clip_settings=draft.ClipSettings(transform_y=0.8),
        track_name="MainTitle",
    )
    main_project.save()
    print("Done. Open JianYing and find draft: Main_Project_With_Compound")


if __name__ == "__main__":
    create_compound_demo()
