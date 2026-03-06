# ruff: noqa: E402

import os
import shutil
import sys
import unittest
from unittest.mock import patch

# Bootstrap path
current_dir = os.path.dirname(os.path.abspath(__file__))
skill_root = os.path.dirname(current_dir)
scripts_path = os.path.join(skill_root, "scripts")
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)

from cloud_manager import CloudManager
from core.mocking_ops import MockAudioMaterial
from jy_wrapper import JyProject, draft
from utils.formatters import safe_tim


class TestJyWrapper(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # 使用临时目录作为测试环境
        cls.test_output = os.path.join(current_dir, "output")
        if os.path.exists(cls.test_output):
            shutil.rmtree(cls.test_output)
        os.makedirs(cls.test_output)

        # 准备一个假的素材文件用于测试 (空文件即可，只要路径存在)
        cls.test_media = os.path.join(cls.test_output, "test_video.mp4")
        with open(cls.test_media, "wb") as f:
            f.write(b"\x00" * 1024)

    def test_01_initialization(self):
        """测试项目初始化与路径探测"""
        p = JyProject("TestInit", drafts_root=self.test_output, overwrite=True)
        self.assertTrue(os.path.exists(os.path.join(self.test_output, "TestInit")))
        self.assertIsInstance(p.script, draft.ScriptFile)

    def test_02_add_text_simple(self):
        """测试文本添加与模糊匹配"""
        p = JyProject("TestText", drafts_root=self.test_output, overwrite=True)
        # 测试模糊匹配 "Typewriter" -> "复古打字机"
        seg = p.add_text_simple("Hello", "0s", "3s", anim_in="Typewriter")
        self.assertIsNotNone(seg)
        # 验证是否真的添加到了轨道
        # 注意：这里需要根据底层库的具体结构来断言
        # 兼容 Dict/List
        tracks_iter = (
            p.script.tracks.values() if isinstance(p.script.tracks, dict) else p.script.tracks
        )

        found = False
        for track in tracks_iter:
            t_type = getattr(track, "track_type", None) or getattr(track, "type", None)
            if t_type == draft.TrackType.text:
                if len(track.segments) > 0:
                    found = True
                    break
        self.assertTrue(found, "Text segment should be added to a text track")

    def test_03_ensure_track_logic(self):
        """测试轨道去重逻辑"""
        p = JyProject("TestTrack", drafts_root=self.test_output)
        p._ensure_track(draft.TrackType.text, "MyTrack")
        p._ensure_track(draft.TrackType.text, "MyTrack")

        count = 0
        tracks_iter = (
            p.script.tracks.values() if isinstance(p.script.tracks, dict) else p.script.tracks
        )
        for t in tracks_iter:
            if hasattr(t, "name") and t.name == "MyTrack":
                count += 1
        self.assertEqual(count, 1, "Track should not be duplicated")

    def test_04_add_transition_simple(self):
        """测试转场添加 (API 稳定性测试)"""
        p = JyProject("TestTrans", drafts_root=self.test_output)
        # 需要两个片段
        p.add_media_safe(self.test_media, "0s", "3s", track_name="V1")
        p.add_media_safe(self.test_media, "3s", "3s", track_name="V1")

        # 尝试添加转场
        # 注意：由于我们用的是假素材，add_media_safe 可能会因为读取时长失败。
        # 此时 add_media_safe 应该返回 None 且打印错误，但不 Crash。
        # 我们这里主要测试 Wrapper 的健壮性。
        p.add_transition_simple("BlackFade", duration="0.5s", track_name="V1")
        # 只要不报错 Crash 就算通过

    def test_05_project_name_sanitization(self):
        """测试 project_name 会被安全化且不越界到 root 外"""
        p = JyProject("..\\..\\Bad:Name*", drafts_root=self.test_output, overwrite=True)
        self.assertNotIn("..", p.name)
        self.assertNotIn(":", p.name)
        self.assertTrue(os.path.abspath(p.draft_dir).startswith(os.path.abspath(self.test_output)))

    def test_06_cloud_url_guard(self):
        """测试云下载 URL 安全校验：阻断 localhost/私网地址"""
        cm = CloudManager()
        self.assertTrue(cm._is_safe_download_url("https://example.com/a.mp4"))
        self.assertFalse(cm._is_safe_download_url("http://127.0.0.1/test.mp4"))
        self.assertFalse(cm._is_safe_download_url("http://localhost/test.mp4"))

    def test_07_cloud_header_guard(self):
        """测试下载响应头校验：拦截 html 和超大文件"""
        cm = CloudManager()

        class Resp:
            def __init__(self, headers):
                self.headers = headers

        self.assertFalse(cm._validate_response_headers(Resp({"Content-Type": "text/html"})))
        self.assertFalse(cm._validate_response_headers(Resp({"Content-Type": "application/json"})))
        self.assertFalse(
            cm._validate_response_headers(
                Resp({"Content-Type": "video/mp4", "Content-Length": str(1024 * 1024 * 1024)})
            )
        )
        self.assertTrue(
            cm._validate_response_headers(
                Resp({"Content-Type": "video/mp4", "Content-Length": "1024"})
            )
        )

    def test_08_safe_join_root_guard(self):
        """测试安全路径拼接：阻断越界路径"""
        p = JyProject("SafeJoin", drafts_root=self.test_output, overwrite=True)
        with self.assertRaises(ValueError):
            p._safe_join_root("..", "..", "Windows")

    def test_09_safe_tim_int_us_not_scaled(self):
        """测试 safe_tim 对 int 输入按微秒处理，避免 55h 级别放大"""
        self.assertEqual(safe_tim(200000), 200000)  # 0.2s
        self.assertEqual(safe_tim(1.5), 1500000)  # float 仍按秒解析

    def test_10_safe_tim_explicit_units(self):
        """测试 safe_tim 支持 ms/us 和复合单位字符串"""
        self.assertEqual(safe_tim("500ms"), 500000)
        self.assertEqual(safe_tim("200000us"), 200000)
        self.assertEqual(safe_tim("1m2.5s"), 62500000)
        self.assertEqual(safe_tim("1h2m3s500ms"), 3723500000)

    def test_11_audio_auto_layering(self):
        """测试音频轨道重叠时自动创建后缀轨道"""
        p = JyProject("TestAudioLayer", drafts_root=self.test_output, overwrite=True)

        def fake_audio_material(path):
            return MockAudioMaterial(f"mat_{os.path.basename(path)}", 3000000, "TestAudio", path)

        with patch("core.media_ops.draft.AudioMaterial", side_effect=fake_audio_material):
            first = p.add_audio_safe(
                "voice_a.mp3", start_time="0s", duration="2s", track_name="AudioTrack"
            )
            second = p.add_audio_safe(
                "voice_b.mp3", start_time="1s", duration="2s", track_name="AudioTrack"
            )

        self.assertIsNotNone(first)
        self.assertIsNotNone(second)
        self.assertIn("AudioTrack", p.script.tracks)
        self.assertIn("AudioTrack_1", p.script.tracks)
        self.assertEqual(len(p.script.tracks["AudioTrack"].segments), 1)
        self.assertEqual(len(p.script.tracks["AudioTrack_1"].segments), 1)

    @classmethod
    def tearDownClass(cls):
        # 清理测试产物
        if os.path.exists(cls.test_output):
            shutil.rmtree(cls.test_output, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
