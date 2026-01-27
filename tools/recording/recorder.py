
import tkinter as tk
from tkinter import messagebox, simpledialog
import threading
import subprocess
import time
import os
import json
import sys
from pynput import mouse, keyboard

class ProGuiRecorder:
    def __init__(self, output_dir=None, audio_device=None):
        # 默认保存到当前目录下的 recordings 文件夹，或者用户指定的目录
        default_dir = os.path.join(os.getcwd(), "recordings")
        self.output_dir = os.path.abspath(output_dir or default_dir)
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "recorder_config.json")
        self.audio_device = audio_device
        self.is_recording = False
        self.start_time = 0
        self.events = []
        self.process = None
        
        # UI Setup
        self.root = tk.Tk()
        self.root.title("剪映 Skill 录屏助手 V3")
        self.root.attributes("-topmost", True)
        self.root.configure(bg="#2c3e50")
        
        # 加载记忆位置
        self.load_config()
        
        # --- 初始完整界面 ---
        self.main_frame = tk.Frame(self.root, bg="#2c3e50")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.status_label = tk.Label(self.main_frame, text="准备就绪", fg="#ecf0f1", bg="#2c3e50", font=("Microsoft YaHei", 12, "bold"))
        self.status_label.pack(pady=15)
        
        audio_status = "已开启" if audio_device else "已禁用"
        self.info_label = tk.Label(self.main_frame, text=f"系统音频录制: {audio_status}\n保存至: recordings/", 
                                  fg="#bdc3c7", bg="#2c3e50", font=("Microsoft YaHei", 8))
        self.info_label.pack(pady=2)
        
        self.start_btn = tk.Button(self.main_frame, text="🎬 开始录制", command=self.start_countdown, 
                                  bg="#2ecc71", fg="white", font=("Microsoft YaHei", 10, "bold"), width=25, height=2)
        self.start_btn.pack(pady=10)

        # --- 录制中简洁界面 (小圆点) ---
        self.mini_frame = tk.Frame(self.root, bg="#e74c3c", cursor="hand2")
        self.record_indicator = tk.Label(self.mini_frame, text="●", fg="white", bg="#e74c3c", font=("Arial", 16))
        self.record_indicator.pack(expand=True)
        
        # 绑定悬停和点击停止
        self.mini_frame.bind("<Button-1>", lambda e: self.stop_recording())
        self.record_indicator.bind("<Button-1>", lambda e: self.stop_recording())
        
        # 允许拖拽小圆点
        self.mini_frame.bind("<B1-Motion>", self.drag_window)
        self.record_indicator.bind("<B1-Motion>", self.drag_window)

        # 初始隐藏 mini
        self.mini_frame.pack_forget()
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        self.m_listener = None
        self.k_listener = None
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()

    def drag_window(self, event):
        x = self.root.winfo_x() + event.x - 25 # 偏移修正
        y = self.root.winfo_y() + event.y - 25
        self.root.geometry(f"+{x}+{y}")

    def load_config(self):
        default_geo = "300x240"  # 略微增加高度适配路径显示
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    config = json.load(f)
                    pos = config.get("window_pos", "")
                    if pos:
                        self.root.geometry(pos)
                        return
            except:
                pass
        self.root.geometry(default_geo)

    def on_close(self):
        try:
            geo = self.root.geometry()
            with open(self.config_path, "w") as f:
                json.dump({"window_pos": geo}, f)
        except:
            pass
        self.root.destroy()

    def generate_filename(self):
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        self.output_path = os.path.join(self.output_dir, f"recording_{timestamp}.mp4")
        self.events_path = self.output_path.replace(".mp4", "_events.json")

    def on_click(self, x, y, button, pressed):
        if self.is_recording and pressed:
            rel_time = time.time() - self.start_time
            self.events.append({
                "type": "click",
                "time": round(rel_time, 3),
                "x": round(x / self.screen_width, 3),
                "y": round(y / self.screen_height, 3)
            })

    def on_press(self, key):
        if self.is_recording:
            rel_time = time.time() - self.start_time
            self.events.append({
                "type": "keypress", "time": round(rel_time, 3)
            })

    def start_countdown(self):
        self.start_btn.config(state=tk.DISABLED)
        for i in range(3, 0, -1):
            self.status_label.config(text=f"即将开始 ({i})...", fg="#f1c40f")
            self.root.update()
            time.sleep(1)
        self.start_actual_recording()

    def start_actual_recording(self):
        self.generate_filename()
        self.is_recording = True
        self.start_time = time.time()
        self.events = []
        
        # 切换到迷你圆形界面 (50x50)
        self.main_frame.pack_forget()
        self.mini_frame.pack(fill=tk.BOTH, expand=True)
        self.root.overrideredirect(True) # 去掉边框
        old_geo = self.root.geometry() # 获取当前位置逻辑
        # 尝试保持中心位置或左上角
        parts = old_geo.split('+')
        if len(parts) >= 3:
            self.root.geometry(f"50x50+{parts[1]}+{parts[2]}")
        else:
            self.root.geometry("50x50")
        
        self.m_listener = mouse.Listener(on_click=self.on_click, on_move=self.on_move)
        self.k_listener = keyboard.Listener(on_press=self.on_press)
        self.m_listener.start()
        self.k_listener.start()
        
        threading.Thread(target=self.run_ffmpeg, daemon=True).start()

    def on_move(self, x, y):
        # 即使只记录坐标，数据量也可能很大。增加限制: 
        # 1. 仅在录制期间
        # 2. 距离上次记录时间 > 0.1s (10FPS采样)
        # 3. 距离上次坐标变化 > 阈值 (例如 5 像素)
        if not self.is_recording:
            return
            
        now = time.time()
        if not hasattr(self, '_last_move_time'):
            self._last_move_time = 0
            self._last_move_pos = (x, y)
        
        if (now - self._last_move_time) > 0.1: # 100ms
            # 计算距离平方
            last_x, last_y = self._last_move_pos
            if (x - last_x)**2 + (y - last_y)**2 > 25: # >5px move
                rel_time = now - self.start_time
                self.events.append({
                    "type": "move",
                    "time": round(rel_time, 3),
                    "x": round(x / self.screen_width, 4),
                    "y": round(y / self.screen_height, 4)
                })
                self._last_move_time = now
                self._last_move_pos = (x, y)

    def run_ffmpeg(self):
        cmd = [
            'ffmpeg', '-y',
            '-f', 'gdigrab', '-framerate', '30', '-i', 'desktop'
        ]
        if self.audio_device:
            cmd.extend(['-f', 'dshow', '-i', f'audio={self.audio_device}'])
            cmd.extend(['-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-crf', '20'])
        else:
            cmd.extend(['-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '20'])
        cmd.append(self.output_path)
        
        # 必须设置 PYTHONIOENCODING，否则子进程在 Windows Pipe 中打印 Emoji 会报 GBK 编码错误
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        
        self.process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
        self.process.wait()

    def stop_recording(self):
        if not self.is_recording: return
        self.is_recording = False
        
        # 恢复界面
        self.root.overrideredirect(False)
        self.mini_frame.pack_forget()
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        self.load_config() # 恢复之前的尺寸
        self.status_label.config(text="已保存", fg="#2ecc71")
        
        # 重新启用开始按钮
        self.start_btn.config(state=tk.NORMAL)
        
        if self.m_listener: self.m_listener.stop()
        if self.k_listener: self.k_listener.stop()
        
        if self.process:
            try:
                self.process.communicate(input=b'q\n', timeout=10)
            except:
                self.process.kill()
        
        try:
            with open(self.events_path, "w", encoding="utf-8") as f:
                json.dump(self.events, f, indent=4)
        except: pass
        
        print(f"✅ 录制成功: {self.output_path}")
        print(f"✅ 录制成功: {self.output_path}")
        
        # 弹出后续操作对话框
        self.show_post_action_dialog()

    def show_post_action_dialog(self):
        """显示录制后操作选单"""
        dialog = tk.Toplevel(self.root)
        dialog.title("录制完成")
        dialog.geometry("400x250")
        dialog.configure(bg="#2c3e50")
        dialog.attributes("-topmost", True)
        
        # 居中显示
        x = self.root.winfo_x()
        y = self.root.winfo_y()
        dialog.geometry(f"+{x}+{y}")

        lbl = tk.Label(dialog, text="✅ 视频已保存！\n下一步做什么？", 
                      fg="#ecf0f1", bg="#2c3e50", font=("Microsoft YaHei", 12, "bold"))
        lbl.pack(pady=20)
        
        btn_frame = tk.Frame(dialog, bg="#2c3e50")
        btn_frame.pack(fill=tk.BOTH, expand=True)

        def do_create_draft():
            # 默认项目名
            import datetime
            timestamp = datetime.datetime.now().strftime("%H%M%S")
            default_name = f"演示_{timestamp}"
            
            # 简单的输入弹窗 (可以用 simpledialog，为了样式统一这里简单搞定)
            name = tk.simpledialog.askstring("创建草稿", "请输入剪映项目名称:", initialvalue=default_name, parent=dialog)
            if not name: return
            
            dialog.destroy()
            self.create_smart_draft(name)

        def open_folder():
            folder = self.output_dir
            os.startfile(folder)
            dialog.destroy()

        tk.Button(btn_frame, text="✨ 自动生成智能草稿", command=do_create_draft,
                 bg="#3498db", fg="white", font=("Microsoft YaHei", 10), width=20).pack(pady=5)
                 
        tk.Button(btn_frame, text="📂 打开文件位置", command=open_folder,
                 bg="#95a5a6", fg="white", font=("Microsoft YaHei", 10), width=20).pack(pady=5)
                 
        tk.Button(btn_frame, text="❌ 关闭", command=dialog.destroy,
                 bg="#e74c3c", fg="white", font=("Microsoft YaHei", 10), width=20).pack(pady=5)

    def create_smart_draft(self, project_name):
        """调用 wrapper 创建草稿"""
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            # 假设结构: tools/recording/xxx.py -> scripts/jy_wrapper.py
            # recording -> tools -> jianying-editor -> scripts
            wrapper_path = os.path.abspath(os.path.join(script_dir, "..", "..", "scripts", "jy_wrapper.py"))
            
            if not os.path.exists(wrapper_path):
                messagebox.showerror("错误", f"找不到 jy_wrapper.py:\n{wrapper_path}")
                return

            cmd = [
                sys.executable, wrapper_path, 
                "apply-zoom",
                "--name", project_name,
                "--video", self.output_path,
                "--json", self.events_path,
                "--scale", "150" # 默认缩放
            ]
            
            # 显示运行中
            self.status_label.config(text="正在生成草稿...", fg="#3498db")
            self.root.update()
            
            # 运行命令
            # 必须设置 PYTHONIOENCODING，否则子进程在 Windows Pipe 中打印 Emoji 会报 GBK 编码错误
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', env=env)
            
            if result.returncode == 0:
                self.status_label.config(text="草稿创建成功！", fg="#2ecc71")
                messagebox.showinfo("成功", f"剪映草稿 '{project_name}' 已创建！\n\n请打开剪映查看。")
            else:
                self.status_label.config(text="创建失败", fg="#e74c3c")
                messagebox.showerror("失败", f"创建出错:\n{result.stderr}")
                
        except Exception as e:
            messagebox.showerror("异常", str(e))

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    AUDIO_ID = "@device_cm_{33D9A762-90C8-11D0-BD43-00A0C911CE86}\\wave_{ABC9BEC4-A0C4-4D18-AB98-09084B41A52D}"
    # 可以接受路径作为保存目录
    out_dir = sys.argv[1] if len(sys.argv) > 1 else None
    recorder = ProGuiRecorder(out_dir, audio_device=AUDIO_ID)
    recorder.run()


