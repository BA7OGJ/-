import cv2
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from threading import Thread
import time
import os

class TimelapseConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("监控视频延时摄影处理器-BA7OGJ")
        self.root.geometry("680x500")
        
        # 初始化变量
        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.interval = tk.DoubleVar(value=1.0)
        self.fps = tk.IntVar(value=30)
        self.running = False
        
        # 创建界面
        self.create_widgets()
        
        # 绑定窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_widgets(self):
        # 文件选择部分
        file_frame = ttk.LabelFrame(self.root, text="文件操作")
        file_frame.pack(pady=10, padx=10, fill="x")
        
        ttk.Label(file_frame, text="输入视频:").grid(row=0, column=0, padx=5)
        ttk.Entry(file_frame, textvariable=self.input_path, width=45).grid(row=0, column=1)
        ttk.Button(file_frame, text="浏览", command=self.select_input, width=8).grid(row=0, column=2, padx=5)
        
        ttk.Label(file_frame, text="输出路径:").grid(row=1, column=0, padx=5, pady=5)
        ttk.Entry(file_frame, textvariable=self.output_path, width=45).grid(row=1, column=1)
        ttk.Button(file_frame, text="浏览", command=self.select_output, width=8).grid(row=1, column=2, padx=5)

        # 参数设置部分
        param_frame = ttk.LabelFrame(self.root, text="转换参数")
        param_frame.pack(pady=10, padx=10, fill="x")
        
        ttk.Label(param_frame, text="采样间隔 (秒):").grid(row=0, column=0, padx=5)
        ttk.Spinbox(
            param_frame, from_=0.1, to=3600, increment=0.5,
            textvariable=self.interval, width=8
        ).grid(row=0, column=1)
        
        ttk.Label(param_frame, text="输出帧率 (FPS):").grid(row=0, column=2, padx=10)
        ttk.Spinbox(
            param_frame, from_=1, to=60, increment=1,
            textvariable=self.fps, width=8
        ).grid(row=0, column=3)

        # 进度条
        self.progress = ttk.Progressbar(
            self.root, orient="horizontal",
            length=600, mode="determinate"
        )
        self.progress.pack(pady=15)
        
        # 日志窗口
        self.log = tk.Text(self.root, height=10, state="disabled")
        self.log.pack(padx=10, pady=5, fill="both", expand=True)
        
        # 操作按钮
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(pady=10)
        
        self.start_btn = ttk.Button(
            btn_frame, text="开始转换",
            command=self.start_conversion
        )
        self.start_btn.pack(side="left", padx=5)
        
        ttk.Button(
            btn_frame, text="退出程序",
            command=self.on_close
        ).pack(side="right", padx=5)

    def select_input(self):
        filetypes = [
            ("视频文件", "*.mp4 *.avi *.mov"),
            ("所有文件", "*.*")
        ]
        path = filedialog.askopenfilename(filetypes=filetypes)
        if path:
            self.input_path.set(path)
            self.auto_generate_output_path(path)

    def select_output(self):
        initial_file = "timelapse_output.mp4"
        filetypes = [
            ("MP4 文件", "*.mp4"),
            ("AVI 文件", "*.avi"),
            ("所有文件", "*.*")
        ]
        path = filedialog.asksaveasfilename(
            defaultextension=".mp4",
            initialfile=initial_file,
            filetypes=filetypes
        )
        if path:
            self.output_path.set(path)

    def auto_generate_output_path(self, input_path):
        dir_name = os.path.dirname(input_path)
        base_name = os.path.basename(input_path)
        name, ext = os.path.splitext(base_name)
        output_name = f"{name}_timelapse.mp4"
        self.output_path.set(os.path.join(dir_name, output_name))

    def log_message(self, message):
        self.log.config(state="normal")
        timestamp = time.strftime("%H:%M:%S")
        self.log.insert("end", f"[{timestamp}] {message}\n")
        self.log.see("end")
        self.log.config(state="disabled")
        self.root.update()

    def start_conversion(self):
        if self.running:
            return

        # 输入验证
        if not os.path.exists(self.input_path.get()):
            messagebox.showerror("错误", "输入文件不存在！")
            return
            
        if not self.output_path.get().strip():
            messagebox.showerror("错误", "请指定输出路径！")
            return

        try:
            if self.interval.get() <= 0 or self.fps.get() <= 0:
                raise ValueError("参数必须大于零")
        except ValueError as e:
            messagebox.showerror("参数错误", str(e))
            return

        self.running = True
        self.start_btn.config(text="转换中...", state="disabled")
        self.progress["value"] = 0
        self.log_message("开始视频转换,请稍候...")
        
        # 启动转换线程
        Thread(target=self.convert_video, daemon=True).start()

    def convert_video(self):
        try:
            cap = cv2.VideoCapture(self.input_path.get())
            if not cap.isOpened():
                raise IOError("无法打开输入视频文件")
            
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            input_fps = cap.get(cv2.CAP_PROP_FPS)
            frame_interval = int(self.interval.get() * input_fps)
            
            if frame_interval < 1:
                frame_interval = 1

            # 获取视频尺寸
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # 初始化输出视频
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(
                self.output_path.get(),
                fourcc,
                self.fps.get(),
                (width, height)
            )
            
            current_frame = 0
            saved_frames = 0
            
            while self.running and current_frame < total_frames:
                ret, frame = cap.read()
                if not ret:
                    break
                
                if current_frame % frame_interval == 0:
                    # 修正旋转问题（可选）
                    # frame = cv2.rotate(frame, cv2.ROTATE_180)
                    out.write(frame)
                    saved_frames += 1
                    progress = (current_frame / total_frames) * 100
                    self.update_progress(progress)
                
                current_frame += 1
            
            cap.release()
            out.release()
            
            if self.running:
                self.log_message(f"转换完成！共处理 {current_frame} 帧，保存 {saved_frames} 帧")
                messagebox.showinfo("完成", "视频转换成功完成！")
        
        except Exception as e:
            self.log_message(f"错误: {str(e)}")
            messagebox.showerror("转换错误", str(e))
        finally:
            self.running = False
            self.start_btn.config(text="开始转换", state="normal")

    def update_progress(self, value):
        self.progress["value"] = value
        self.root.update_idletasks()

    def on_close(self):
        if self.running:
            if messagebox.askokcancel("退出", "转换正在进行中，确定要退出吗？"):
                self.running = False
                self.root.destroy()
        else:
            self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = TimelapseConverter(root)
    root.mainloop()
