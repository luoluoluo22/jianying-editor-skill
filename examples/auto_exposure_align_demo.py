import os

import cv2
import numpy as np

from _bootstrap import ensure_skill_scripts_on_path

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT, _ = ensure_skill_scripts_on_path(CURRENT_DIR)

from jy_wrapper import JyProject
from pyJianYingDraft import KeyframeProperty as KP


def calculate_video_brightness(video_path: str) -> float:
    cap = cv2.VideoCapture(video_path)
    ret, frame = cap.read()
    if not ret:
        cap.release()
        return 128.0
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    avg_v = float(np.mean(hsv[:, :, 2]))
    cap.release()
    return avg_v


def run_exposure_alignment_example() -> None:
    print("Starting Auto Exposure Alignment Example...")
    project_name = "Auto_Exposure_Alignment_Demo"
    project = JyProject(project_name, overwrite=True)

    video_path = os.path.join(SKILL_ROOT, "assets", "video.mp4")
    if not os.path.exists(video_path):
        print(f"Warning: example video not found at {video_path}")
        return

    target_brightness = 140.0
    current_b = calculate_video_brightness(video_path)
    offset = (target_brightness - current_b) / 128.0
    offset = max(-0.8, min(0.8, offset))

    seg = project.add_media_safe(video_path, start_time=0)
    if seg:
        seg.add_keyframe(KP.brightness, 0, offset)
        print(f"Injected brightness keyframe offset={offset:.2f}")

    project.save()
    print(f"Done. Open '{project_name}' in JianYing.")


if __name__ == "__main__":
    run_exposure_alignment_example()
