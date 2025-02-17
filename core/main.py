import tkinter as tk
from tkinter import messagebox, BooleanVar
import json
import pystray
from PIL import Image, ImageDraw
import threading
import winsound

class EyeProtector:
    def __init__(self):
        self.load_settings()
        self.create_tray_icon()
        self.create_floating_window()
        self.update_work_time()

    def load_settings(self):
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
                self.work_minutes = config.get('work_time', 45)
                self.break_seconds = config.get('break_time', 300)
                self.sound_enabled = config.get('sound_enabled', True)  # 新增
        except:
            self.work_minutes = 45
            self.break_seconds = 300
            self.sound_enabled = True  # 默认开启

    def save_settings(self):
        with open('config.json', 'w') as f:
            json.dump({
                'work_time': self.work_minutes,
                'break_time': self.break_seconds,
                'sound_enabled': self.sound_enabled  # 新增配置项
            }, f)

    def create_tray_icon(self):
        image = Image.new('RGB', (64, 64), 'white')
        draw = ImageDraw.Draw(image)
        draw.ellipse((16, 16, 48, 48), outline='#000000')
        draw.ellipse((18, 18, 46, 46), fill='#FFFFFF')
        draw.ellipse((24, 24, 40, 40), fill='#000000')

        menu = pystray.Menu(
            pystray.MenuItem("设置", self.show_settings),
            pystray.MenuItem("退出", self.exit_app)
        )
        self.tray_icon = pystray.Icon("eye_protector", image, "护眼程序", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def toggle_sound(self):
        """实时更新声音状态"""
        self.sound_enabled = self.sound_var.get()
        # self.save_settings()  # 可选：如需实时保存配置
    
    def show_settings(self):
        self.settings_win = tk.Toplevel(self.root)
        self.settings_win.title("设置")
        self.settings_win.attributes('-topmost', True)
        
        tk.Label(self.settings_win, text="工作时间（分钟）:").grid(row=0, column=0, padx=10, pady=10)
        self.work_entry = tk.Entry(self.settings_win)
        self.work_entry.insert(0, str(self.work_minutes))
        self.work_entry.grid(row=0, column=1, padx=10, pady=10)

        tk.Label(self.settings_win, text="休息时间（秒）:").grid(row=1, column=0, padx=10, pady=10)
        self.break_entry = tk.Entry(self.settings_win)
        self.break_entry.insert(0, str(self.break_seconds))
        self.break_entry.grid(row=1, column=1, padx=10, pady=10)

        # 在原有设置项下方新增（row需要根据实际布局调整）
        self.sound_var = BooleanVar(value=self.sound_enabled)
        sound_check = tk.Checkbutton(
            self.settings_win, 
            text="启用提示音",
            variable=self.sound_var,
            command=self.toggle_sound  # 绑定实时切换
        )
        sound_check.grid(row=2, columnspan=2, pady=5, sticky='w')
        
        tk.Button(self.settings_win, text="保存", command=self.save_settings_from_ui).grid(row=3, columnspan=2, pady=10)

    def save_settings_from_ui(self):
        try:
            self.work_minutes = int(self.work_entry.get())
            self.break_seconds = int(self.break_entry.get())
            self.sound_enabled = self.sound_var.get()
            self.save_settings()
            
            # 取消所有活动计时器
            if hasattr(self, 'work_timer'):
                self.root.after_cancel(self.work_timer)
            if hasattr(self, 'break_timer'):
                self.root.after_cancel(self.break_timer)
                
            # 关闭所有弹窗
            self.settings_win.destroy()
            for win in ['break_win', 'rest_end_win']:
                if hasattr(self, win) and getattr(self, win).winfo_exists():
                    getattr(self, win).destroy()
                    delattr(self, win)
            
            self.update_work_time()
            messagebox.showinfo("成功", "设置已更新！")
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字")

    def exit_app(self):
        self.tray_icon.stop()
        self.root.quit()

    def create_floating_window(self):
        self.root = tk.Tk()
        self.root.title("护眼程序")
        self.root.withdraw()

        self.float_win = tk.Toplevel(self.root)
        self.float_win.overrideredirect(True)
        self.float_win.attributes('-topmost', True)
        self.float_win.geometry("60x60+100+100")
        
        self.canvas = tk.Canvas(self.float_win, width=60, height=60, bg='white', highlightthickness=0)
        self.canvas.pack()
        self.circle = self.canvas.create_oval(10, 10, 50, 50, fill='#FF4500')
        self.time_text = self.canvas.create_text(30, 30, text='', fill='white')

        self.float_win.bind("<ButtonPress-1>", self.start_move)
        self.float_win.bind("<B1-Motion>", self.on_move)

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def on_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.float_win.winfo_x() + deltax
        y = self.float_win.winfo_y() + deltay
        self.float_win.geometry(f"+{x}+{y}")

    def update_work_time(self):
        # 重置所有工作相关状态
        if hasattr(self, 'work_timer'):
            self.root.after_cancel(self.work_timer)
        if hasattr(self, 'break_timer'):
            self.root.after_cancel(self.break_timer)
        
        # 强制恢复工作状态颜色
        self.canvas.itemconfig(self.circle, fill='#FF4500')  # 新增颜色重置
        
        self.remaining = self.work_minutes * 60
        self.update_display()
        self.schedule_work()

    def schedule_work(self):
        self.work_timer = self.root.after(1000, self.countdown_work)

    def countdown_work(self):
        self.remaining -= 1
        if self.remaining <= 0:
            if self.sound_enabled:  # 新增判断
                winsound.Beep(1000, 1000)  # 添加提示音
            self.show_break_alert()
        else:
            self.update_display()
            self.schedule_work()

    def update_display(self):
        mins, secs = divmod(self.remaining, 60)
        self.canvas.itemconfig(self.time_text, text=f"{mins:02d}:{secs:02d}")

    def show_break_alert(self):
        if hasattr(self, 'break_win') and self.break_win.winfo_exists():
            return
        
        self.break_win = tk.Toplevel(self.root)
        self.break_win.overrideredirect(True)  # 移除标题栏
        self.break_win.attributes('-topmost', True)
        screen_width = self.break_win.winfo_screenwidth()
        screen_height = self.break_win.winfo_screenheight()
        x = (screen_width - 300) // 2
        y = (screen_height - 150) // 2
        self.break_win.geometry(f"300x150+{x}+{y}")
        
        tk.Label(self.break_win, text="喂！再看眼睛等着瞎吧", font=('Arial', 16)).pack(pady=10)
        tk.Label(self.break_win, text="请选择是否休息：", font=('Arial', 12)).pack()
        
        button_frame = tk.Frame(self.break_win)
        button_frame.pack(pady=20)
        tk.Button(button_frame, text="开始休息", font=('Arial', 12), command=self.start_break, width=10).grid(row=0, column=0, padx=10)
        tk.Button(button_frame, text="不休息", font=('Arial', 12), command=self.skip_break, width=10).grid(row=0, column=1, padx=10)
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)

    def skip_break(self):
        if hasattr(self, 'break_win'):
            self.break_win.destroy()
            del self.break_win
        self.update_work_time()

    def start_break(self):
        if hasattr(self, 'break_win'):
            self.break_win.destroy()
            del self.break_win
        if hasattr(self, 'work_timer'):
            self.root.after_cancel(self.work_timer)
        self.remaining_break = self.break_seconds
        self.start_break_countdown()

    def start_break_countdown(self):
        self.canvas.itemconfig(self.circle, fill='#32CD32')
        self.update_break_display()
        self.schedule_break()

    def schedule_break(self):
        self.break_timer = self.root.after(1000, self.countdown_break)

    def countdown_break(self):
        self.remaining_break -= 1
        if self.remaining_break <= 0:
            if self.sound_enabled:
                winsound.Beep(1000, 1000)  # 添加提示音
            self.show_rest_end_alert()
        else:
            self.update_break_display()
            self.schedule_break()

    def update_break_display(self):
        mins, secs = divmod(self.remaining_break, 60)
        self.canvas.itemconfig(self.time_text, text=f"{mins:02d}:{secs:02d}")

    def show_rest_end_alert(self):
        self.rest_end_win = tk.Toplevel(self.root)
        self.rest_end_win.overrideredirect(True)  # 移除标题栏
        self.rest_end_win.attributes('-topmost', True)
        screen_width = self.rest_end_win.winfo_screenwidth()
        screen_height = self.rest_end_win.winfo_screenheight()
        x = (screen_width - 300) // 2
        y = (screen_height - 150) // 2
        self.rest_end_win.geometry(f"300x150+{x}+{y}")
        
        tk.Label(self.rest_end_win, text="休息时间结束！", font=('Arial', 16)).pack(pady=10)
        tk.Label(self.rest_end_win, text="请确认是否重新开始工作。", font=('Arial', 12)).pack()
        tk.Button(self.rest_end_win, text="确认", font=('Arial', 12),
                  command=self.confirm_rest_end).pack(pady=20)

    def confirm_rest_end(self):
        if hasattr(self, 'rest_end_win'):
            self.rest_end_win.destroy()
            del self.rest_end_win
        self.canvas.itemconfig(self.circle, fill='#FF4500')
        self.update_work_time()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = EyeProtector()
    app.run()