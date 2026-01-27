import os
import sys
import unittest
import shutil

# Bootstrap path
current_dir = os.path.dirname(os.path.abspath(__file__))
skill_root = os.path.dirname(current_dir)
scripts_path = os.path.join(skill_root, "scripts")
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)

from jy_wrapper import JyProject, draft

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
        with open(cls.test_media, 'wb') as f:
            f.write(b'\x00' * 1024)

    def test_01_initialization(self):
        """测试项目初始化与路径探测"""
        p = JyProject("TestInit", drafts_root=self.test_output, overwrite=True)
        self.assertTrue(os.path.exists(os.path.join(self.test_output, "TestInit")))
        self.assertIsInstance(p.script, draft.ScriptFile)

    def test_02_add_text_simple(self):
        """测试文本添加与模糊匹配"""
        p = JyProject("TestText", drafts_root=self.test_output)
        # 测试模糊匹配 "Typewriter" -> "复古打字机"
        seg = p.add_text_simple("Hello", "0s", "3s", anim_in="Typewriter")
        self.assertIsNotNone(seg)
        # 验证是否真的添加到了轨道
        # 注意：这里需要根据底层库的具体结构来断言
        # 兼容 Dict/List
        tracks_iter = p.script.tracks.values() if isinstance(p.script.tracks, dict) else p.script.tracks
        
        found = False
        for track in tracks_iter:
            if hasattr(track, 'type') and track.type == draft.TrackType.text:
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
        tracks_iter = p.script.tracks.values() if isinstance(p.script.tracks, dict) else p.script.tracks
        for t in tracks_iter:
            if hasattr(t, 'name') and t.name == "MyTrack":
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

    @classmethod
    def tearDownClass(cls):
        # 清理测试产物
        if os.path.exists(cls.test_output):
            shutil.rmtree(cls.test_output, ignore_errors=True)

if __name__ == "__main__":
    unittest.main()
