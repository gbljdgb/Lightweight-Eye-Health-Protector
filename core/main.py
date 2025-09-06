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
                self.sound_enabled = config.get('sound_enabled', True)
                # 加载待办事项列表
                self.todo_items = config.get('todo_items', ['拉单杠', '做眼保健操', '站立拉伸', '喝水'])  # 默认待办事项
        except:
            self.work_minutes = 45
            self.break_seconds = 300
            self.sound_enabled = True
            self.todo_items = ['拉单杠', '做眼保健操', '站立拉伸', '喝水']  # 默认待办事项

    def save_settings(self):
        with open('config.json', 'w') as f:
            json.dump({
                'work_time': self.work_minutes,
                'break_time': self.break_seconds,
                'sound_enabled': self.sound_enabled,
                'todo_items': self.todo_items  # 保存待办事项列表
            }, f)

    def create_tray_icon(self):
        image = Image.new('RGB', (64, 64), 'white')
        draw = ImageDraw.Draw(image)
        draw.ellipse((16, 16, 48, 48), outline='#000000')
        draw.ellipse((18, 18, 46, 46), fill='#FFFFFF')
        draw.ellipse((24, 24, 40, 40), fill='#000000')

        menu = pystray.Menu(
            pystray.MenuItem("设置", self.show_settings),
            pystray.MenuItem("立刻进入休息", self.enter_break_immediately),
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
        self.settings_win.geometry("500x450")  # 增大窗口以适应待办事项配置和新按钮
        
        tk.Label(self.settings_win, text="工作时间（分钟）:").grid(row=0, column=0, padx=10, pady=10)
        self.work_entry = tk.Entry(self.settings_win)
        self.work_entry.insert(0, str(self.work_minutes))
        self.work_entry.grid(row=0, column=1, padx=10, pady=10)

        tk.Label(self.settings_win, text="休息时间（秒）:").grid(row=1, column=0, padx=10, pady=10)
        self.break_entry = tk.Entry(self.settings_win)
        self.break_entry.insert(0, str(self.break_seconds))
        self.break_entry.grid(row=1, column=1, padx=10, pady=10)

        # 在原有设置项下方新增
        self.sound_var = BooleanVar(value=self.sound_enabled)
        sound_check = tk.Checkbutton(
            self.settings_win,
            text="启用提示音",
            variable=self.sound_var,
            command=self.toggle_sound  # 绑定实时切换
        )
        sound_check.grid(row=2, columnspan=2, pady=5, sticky='w')
        
        # 添加待办事项配置区域
        tk.Label(self.settings_win, text="待办事项配置:").grid(row=3, column=0, padx=10, pady=10, sticky='nw')
        
        todo_frame = tk.Frame(self.settings_win)
        todo_frame.grid(row=3, column=1, padx=10, pady=10, sticky='nsew')
        
        # 创建滚动条
        scrollbar = tk.Scrollbar(todo_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 创建列表框显示待办事项
        self.todo_listbox = tk.Listbox(todo_frame, width=30, height=6, yscrollcommand=scrollbar.set)
        self.todo_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.todo_listbox.yview)
        
        # 填充待办事项到列表框
        for item in self.todo_items:
            self.todo_listbox.insert(tk.END, item)
        
        # 添加待办事项输入框和按钮
        todo_input_frame = tk.Frame(self.settings_win)
        todo_input_frame.grid(row=4, column=1, padx=10, pady=5, sticky='ew')
        
        self.new_todo_entry = tk.Entry(todo_input_frame)
        self.new_todo_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        button_frame = tk.Frame(self.settings_win)
        button_frame.grid(row=5, column=1, padx=10, pady=5, sticky='ew')
        
        tk.Button(button_frame, text="添加", command=self.add_todo_item).pack(side=tk.LEFT, padx=2)
        tk.Button(button_frame, text="删除选中", command=self.remove_todo_item).pack(side=tk.LEFT, padx=2)
        
        # 保存按钮
        tk.Button(self.settings_win, text="保存", command=self.save_settings_from_ui).grid(row=6, columnspan=2, pady=10)
        
        # 立刻进入休息按钮
        tk.Button(self.settings_win, text="立刻进入休息", command=self.enter_break_immediately, bg='#FF4500', fg='white').grid(row=7, columnspan=2, pady=10)
        
        # 设置列权重，使UI更美观
        self.settings_win.grid_columnconfigure(1, weight=1)
        self.settings_win.grid_rowconfigure(3, weight=1)

    def add_todo_item(self):
        """添加新的待办事项"""
        new_item = self.new_todo_entry.get().strip()
        if new_item and new_item not in self.todo_listbox.get(0, tk.END):
            self.todo_listbox.insert(tk.END, new_item)
            self.new_todo_entry.delete(0, tk.END)

    def remove_todo_item(self):
        """删除选中的待办事项"""
        try:
            selected_index = self.todo_listbox.curselection()[0]
            self.todo_listbox.delete(selected_index)
        except IndexError:
            messagebox.showinfo("提示", "请先选择要删除的待办事项")

    def save_settings_from_ui(self):
        try:
            self.work_minutes = int(self.work_entry.get())
            self.break_seconds = int(self.break_entry.get())
            self.sound_enabled = self.sound_var.get()
            
            # 获取待办事项列表
            self.todo_items = list(self.todo_listbox.get(0, tk.END))
            if not self.todo_items:
                # 如果没有待办事项，设置默认值
                self.todo_items = ['拉单杠', '做眼保健操', '站立拉伸', '喝水']
            
            self.save_settings()
            
            # 取消所有活动计时器
            if hasattr(self, 'work_timer'):
                self.root.after_cancel(self.work_timer)
            if hasattr(self, 'break_timer'):
                self.root.after_cancel(self.break_timer)
                
            # 关闭所有弹窗和清理状态
            # 先保存设置窗口的引用，因为destroy后会失去引用
            settings_win_ref = self.settings_win
            
            # 关闭所有相关窗口
            windows_to_close = ['break_win', 'rest_end_win', 'large_break_win']
            for win_name in windows_to_close:
                if hasattr(self, win_name) and getattr(self, win_name).winfo_exists():
                    getattr(self, win_name).destroy()
                    delattr(self, win_name)
            
            # 清理其他可能的属性
            for attr in ['break_time_label', 'todo_vars', 'confirm_button']:
                if hasattr(self, attr):
                    delattr(self, attr)
            
            # 关闭设置窗口
            settings_win_ref.destroy()
            
            # 重置并更新工作时间
            self.update_work_time()
            
            # 显示成功消息，使用root作为父窗口确保在顶层
            messagebox.showinfo("成功", "设置已更新！", parent=self.root)
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字")

    def exit_app(self):
        """完整退出程序并回收所有资源"""
        try:
            # 停止所有计时器
            if hasattr(self, 'work_timer'):
                self.root.after_cancel(self.work_timer)
            if hasattr(self, 'break_timer'):
                self.root.after_cancel(self.break_timer)
                
            # 关闭所有打开的窗口
            windows_to_close = ['break_win', 'rest_end_win', 'large_break_win', 'settings_win']
            for win_name in windows_to_close:
                if hasattr(self, win_name) and getattr(self, win_name).winfo_exists():
                    getattr(self, win_name).destroy()
                    delattr(self, win_name)
                    
            # 停止托盘图标
            if hasattr(self, 'tray_icon'):
                self.tray_icon.stop()
                delattr(self, 'tray_icon')
                
            # 释放其他可能的资源
            for attr in ['break_time_label', 'todo_vars', 'confirm_button', 'todo_listbox', 'sound_var']:
                if hasattr(self, attr):
                    delattr(self, attr)
                    
            # 确保所有窗口都被销毁
            for widget in self.root.winfo_children():
                widget.destroy()
                
            # 完全退出程序
            self.root.destroy()
        except Exception as e:
            # 如果发生任何错误，仍然尝试强制退出
            print(f"退出过程中发生错误: {e}")
            import sys
            sys.exit(0)

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
        self.canvas.itemconfig(self.circle, fill='#FF4500')
        
        self.remaining = self.work_minutes * 60
        self.update_display()
        self.schedule_work()

    def schedule_work(self):
        self.work_timer = self.root.after(1000, self.countdown_work)

    def countdown_work(self):
        self.remaining -= 1
        if self.remaining <= 0:
            if self.sound_enabled:
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
        tk.Button(button_frame, text="不休息", font=('Arial', 12), command=self.confirm_skip_break, width=10).grid(row=0, column=1, padx=10)
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        
    def confirm_skip_break(self):
        """二次确认是否跳过休息"""
        # 先将休息提醒窗口隐藏，确保确认框显示在前面
        if hasattr(self, 'break_win'):
            self.break_win.withdraw()
        
        # 使用root作为父窗口，确保对话框显示在前面
        result = messagebox.askyesno(
            "确认跳过休息", 
            "长时间不休息对眼睛伤害很大！\n确定要跳过休息吗？",
            parent=self.root
        )
        
        # 如果用户取消，则恢复休息提醒窗口
        if not result and hasattr(self, 'break_win') and self.break_win.winfo_exists():
            self.break_win.deiconify()
        elif result:
            self.skip_break()

    def skip_break(self):
        # 关闭休息提醒窗口
        if hasattr(self, 'break_win'):
            self.break_win.destroy()
            del self.break_win
        # 关闭放大的休息倒计时页面
        if hasattr(self, 'large_break_win'):
            self.large_break_win.destroy()
            del self.large_break_win
            # 如果存在break_time_label属性，也一并删除
            if hasattr(self, 'break_time_label'):
                del self.break_time_label
        self.update_work_time()

    def start_break(self):
        if hasattr(self, 'break_win'):
            self.break_win.destroy()
            del self.break_win
        if hasattr(self, 'work_timer'):
            self.root.after_cancel(self.work_timer)
        self.remaining_break = self.break_seconds
        
        # 创建放大的休息倒计时页面
        self.create_large_break_window()
        self.start_break_countdown()
    
    def create_large_break_window(self):
        """创建放大的休息倒计时页面"""
        self.large_break_win = tk.Toplevel(self.root)
        self.large_break_win.title("休息时间")
        self.large_break_win.attributes('-topmost', True)
        
        # 设置窗口大小为屏幕的80%
        screen_width = self.large_break_win.winfo_screenwidth()
        screen_height = self.large_break_win.winfo_screenheight()
        win_width = int(screen_width * 0.8)
        win_height = int(screen_height * 0.8)
        x = (screen_width - win_width) // 2
        y = (screen_height - win_height) // 2
        
        self.large_break_win.geometry(f"{win_width}x{win_height}+{x}+{y}")
        self.large_break_win.configure(bg='#32CD32')
        
        # 创建顶部框架放置紧急按钮
        top_frame = tk.Frame(self.large_break_win, bg='#32CD32')
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=20, pady=10)
        
        # 将关闭按钮移到右上角，样式调整为不那么显眼
        tk.Button(
            top_frame, 
            text="紧急结束", 
            font=('Arial', 10),
            command=self.skip_break,
            width=10,
            height=1,
            bg='#666666',  # 使用不太显眼的颜色
            fg='white',
            relief='flat'
        ).pack(side=tk.RIGHT)
        
        # 添加标题
        tk.Label(
            self.large_break_win, 
            text="休息一下，保护眼睛！", 
            font=('Arial', 36, 'bold'),
            bg='#32CD32',
            fg='white'
        ).pack(pady=50)
        
        # 添加大号倒计时显示
        self.break_time_label = tk.Label(
            self.large_break_win, 
            text="", 
            font=('Arial', 72, 'bold'),
            bg='#32CD32',
            fg='white'
        )
        self.break_time_label.pack(pady=30)
        
        # 添加护眼提示信息
        tk.Label(
            self.large_break_win, 
            text="请远离电脑，看看远处，让眼睛得到充分休息。\n紧急情况下，可点击右上角按钮提前结束休息。", 
            font=('Arial', 18),
            bg='#32CD32',
            fg='white',
            justify='center'
        ).pack(pady=20)

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
        time_str = f"{mins:02d}:{secs:02d}"
        
        # 更新悬浮窗口上的倒计时
        self.canvas.itemconfig(self.time_text, text=time_str)
        
        # 更新放大休息页面上的倒计时
        if hasattr(self, 'break_time_label'):
            self.break_time_label.config(text=time_str)

    def show_rest_end_alert(self):
        self.rest_end_win = tk.Toplevel(self.root)
        # 不再移除标题栏，保留关闭按钮
        # self.rest_end_win.overrideredirect(True)
        self.rest_end_win.attributes('-topmost', True)
        self.rest_end_win.title("休息结束")
        screen_width = self.rest_end_win.winfo_screenwidth()
        screen_height = self.rest_end_win.winfo_screenheight()
        x = (screen_width - 400) // 2  # 增大窗口宽度以适应待办事项
        y = (screen_height - 300) // 2  # 增大窗口高度以适应待办事项和滚动区域
        self.rest_end_win.geometry(f"400x300+{x}+{y}")
        
        tk.Label(self.rest_end_win, text="休息时间结束！", font=('Arial', 16)).pack(pady=10)
        
        # 增加待办事项区域，添加滚动功能
        todo_frame = tk.Frame(self.rest_end_win)
        todo_frame.pack(pady=10, fill=tk.BOTH, expand=True, padx=20)
        
        tk.Label(todo_frame, text="请完成以下活动后再开始工作：", font=('Arial', 12)).pack(anchor='w', pady=(0, 5))
        
        # 创建带滚动条的画布来容纳待办事项
        canvas = tk.Canvas(todo_frame, width=340, height=100)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(todo_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 创建内部框架放置待办事项
        checkbox_frame = tk.Frame(canvas)
        canvas.create_window((0, 0), window=checkbox_frame, anchor='nw')
        
        # 创建待办事项复选框
        self.todo_vars = []
        for item in self.todo_items:
            var = BooleanVar()
            self.todo_vars.append(var)
            check = tk.Checkbutton(checkbox_frame, text=item, variable=var, font=('Arial', 10), width=35, anchor='w')
            check.pack(anchor='w', pady=2)
        
        # 绑定事件以更新滚动区域
        def update_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        checkbox_frame.bind("<Configure>", update_scroll_region)
        
        # 添加确认按钮
        button_frame = tk.Frame(self.rest_end_win)
        button_frame.pack(pady=10, fill=tk.X)
        
        self.confirm_button = tk.Button(button_frame, text="完成并开始工作", font=('Arial', 12),
                  command=self.confirm_rest_end, state=tk.DISABLED, width=20)  # 初始禁用
        self.confirm_button.pack()
        
        # 为每个复选框添加检查状态变化的回调
        def check_todo_status():
            # 检查是否所有待办事项都已勾选
            all_checked = all(var.get() for var in self.todo_vars)
            # 根据检查结果启用或禁用确认按钮
            self.confirm_button.config(state=tk.NORMAL if all_checked else tk.DISABLED)
        
        # 为每个复选框绑定状态变化事件
        for var in self.todo_vars:
            var.trace_add("write", lambda *args: check_todo_status())
            
        # 添加窗口关闭事件处理
        self.rest_end_win.protocol("WM_DELETE_WINDOW", self.skip_break)

    def confirm_rest_end(self):
        # 关闭休息结束提醒窗口
        if hasattr(self, 'rest_end_win'):
            self.rest_end_win.destroy()
            del self.rest_end_win
        # 关闭放大的休息倒计时页面
        if hasattr(self, 'large_break_win'):
            self.large_break_win.destroy()
            del self.large_break_win
            # 如果存在break_time_label属性，也一并删除
            if hasattr(self, 'break_time_label'):
                del self.break_time_label
        self.canvas.itemconfig(self.circle, fill='#FF4500')
        self.update_work_time()

    def enter_break_immediately(self):
        """立即进入休息状态"""
        # 先清理现有的计时器和窗口
        if hasattr(self, 'work_timer'):
            self.root.after_cancel(self.work_timer)
        if hasattr(self, 'break_timer'):
            self.root.after_cancel(self.break_timer)
            
        # 关闭可能存在的窗口
        windows_to_close = ['break_win', 'rest_end_win', 'large_break_win']
        for win_name in windows_to_close:
            if hasattr(self, win_name) and getattr(self, win_name).winfo_exists():
                getattr(self, win_name).destroy()
                if hasattr(self, win_name):
                    delattr(self, win_name)
        
        # 立即开始休息
        self.remaining_break = self.break_seconds
        self.create_large_break_window()
        self.start_break_countdown()
        
        # 播放提示音
        if self.sound_enabled:
            winsound.Beep(1000, 1000)
            
        # 如果设置窗口存在且可见，则隐藏它
        if hasattr(self, 'settings_win') and self.settings_win.winfo_exists():
            self.settings_win.withdraw()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = EyeProtector()
    app.run()