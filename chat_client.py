#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SOCKET网络编程实验 - 聊天客户端GUI (支持图片传输和用户系统)
基于TCP协议的C/S架构客户端实现（带图形界面、文件传输和用户信息）
"""

import socket
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import logging
import base64
import json
import os
from datetime import datetime
from PIL import Image, ImageTk
import io

class AvatarCropWindow:
    def __init__(self, parent, image):
        self.parent = parent
        self.original_image = image
        self.result_image = None
        
        # 创建裁剪窗口
        self.window = tk.Toplevel(parent)
        self.window.title("裁剪头像 - 拖拽选择正方形区域")
        self.window.geometry("800x700")  # 增加高度到700
        self.window.resizable(False, False)
        self.window.grab_set()  # 模态窗口
        
        # 计算显示尺寸（保持原始比例）
        self.display_width = 700
        self.display_height = 450  # 减少图片显示区域高度为450
        
        # 计算缩放比例
        img_width, img_height = image.size
        scale_x = self.display_width / img_width
        scale_y = self.display_height / img_height
        self.scale = min(scale_x, scale_y, 1.0)  # 不放大，只缩小
        
        # 计算显示图片尺寸
        self.scaled_width = int(img_width * self.scale)
        self.scaled_height = int(img_height * self.scale)
        
        # 缩放图片用于显示
        self.display_image = image.resize((self.scaled_width, self.scaled_height), Image.LANCZOS)
        self.photo = ImageTk.PhotoImage(self.display_image)
        
        # 创建界面
        self.create_widgets()
        
        # 选择区域相关
        self.start_x = None
        self.start_y = None
        self.current_rect = None
        self.selection_coords = None
        
    def create_widgets(self):
        """创建裁剪界面组件"""
        # 说明标签
        info_frame = tk.Frame(self.window)
        info_frame.pack(pady=5)
        
        tk.Label(info_frame, text="📌 操作说明：", font=("Arial", 10, "bold")).pack()
        tk.Label(info_frame, text="1. 在图片上拖拽鼠标选择正方形区域", font=("Arial", 9)).pack()
        tk.Label(info_frame, text="2. 松开鼠标后自动调整为正方形", font=("Arial", 9)).pack()
        tk.Label(info_frame, text="3. 点击'确认裁剪'完成操作", font=("Arial", 9)).pack()
        
        # 图片显示区域 - 限制高度
        canvas_frame = tk.Frame(self.window, bg="lightgray")
        canvas_frame.pack(pady=10, fill="x")  # 不使用expand=True
        
        self.canvas = tk.Canvas(
            canvas_frame, 
            width=self.scaled_width, 
            height=self.scaled_height,
            bg="white",
            cursor="crosshair"
        )
        self.canvas.pack()
        
        # 显示图片
        self.canvas.create_image(0, 0, anchor="nw", image=self.photo)
        
        # 绑定鼠标事件
        self.canvas.bind("<Button-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        
        # 预览区域 - 放在按钮前面
        preview_frame = tk.LabelFrame(self.window, text="预览", font=("Arial", 9))
        preview_frame.pack(pady=5)
        
        self.preview_label = tk.Label(preview_frame, text="请选择区域", width=22, height=9, bg="lightgray")
        self.preview_label.pack(padx=10, pady=5)
        
        # 按钮区域 - 确保在最下方
        button_frame = tk.Frame(self.window)
        button_frame.pack(side="bottom", pady=20)  # 使用side="bottom"确保在底部
        
        tk.Button(
            button_frame, 
            text="✅ 确认裁剪", 
            command=self.confirm_crop,
            bg="lightgreen",
            font=("Arial", 12, "bold"),
            width=12,
            height=2
        ).pack(side="left", padx=20)
        
        tk.Button(
            button_frame, 
            text="❌ 取消", 
            command=self.cancel_crop,
            bg="lightcoral",
            font=("Arial", 12, "bold"),
            width=12,
            height=2
        ).pack(side="left", padx=20)
        
    def on_mouse_down(self, event):
        """鼠标按下"""
        self.start_x = event.x
        self.start_y = event.y
        
        # 删除之前的选择框
        if self.current_rect:
            self.canvas.delete(self.current_rect)
            self.current_rect = None
    
    def on_mouse_drag(self, event):
        """鼠标拖拽"""
        if self.start_x is None or self.start_y is None:
            return
        
        # 删除之前的选择框
        if self.current_rect:
            self.canvas.delete(self.current_rect)
        
        # 计算当前选择区域（限制为正方形）
        width = abs(event.x - self.start_x)
        height = abs(event.y - self.start_y)
        size = min(width, height)  # 取较小值确保是正方形
        
        # 确定正方形的坐标
        if event.x >= self.start_x:
            end_x = self.start_x + size
        else:
            end_x = self.start_x - size
            
        if event.y >= self.start_y:
            end_y = self.start_y + size
        else:
            end_y = self.start_y - size
        
        # 确保不超出图片边界
        end_x = max(0, min(end_x, self.scaled_width))
        end_y = max(0, min(end_y, self.scaled_height))
        
        # 绘制选择框
        self.current_rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, end_x, end_y,
            outline="red", width=2, dash=(5, 5)
        )
        
        # 更新预览
        self.update_preview(self.start_x, self.start_y, end_x, end_y)
    
    def on_mouse_up(self, event):
        """鼠标松开"""
        if self.current_rect:
            # 获取最终选择区域
            coords = self.canvas.coords(self.current_rect)
            self.selection_coords = coords
            
            # 重新绘制选择框为实线
            self.canvas.delete(self.current_rect)
            self.current_rect = self.canvas.create_rectangle(
                *coords, outline="blue", width=3
            )
    
    def update_preview(self, x1, y1, x2, y2):
        """更新预览图"""
        try:
            # 计算在原始图片中的坐标
            orig_x1 = int(x1 / self.scale)
            orig_y1 = int(y1 / self.scale)
            orig_x2 = int(x2 / self.scale)
            orig_y2 = int(y2 / self.scale)
            
            # 确保坐标有效
            if abs(orig_x2 - orig_x1) < 10 or abs(orig_y2 - orig_y1) < 10:
                return
            
            # 裁剪原始图片
            crop_box = (
                min(orig_x1, orig_x2),
                min(orig_y1, orig_y2),
                max(orig_x1, orig_x2),
                max(orig_y1, orig_y2)
            )
            
            cropped = self.original_image.crop(crop_box)
            
            # 缩放到预览尺寸
            preview_size = (150, 150)
            preview_image = cropped.resize(preview_size, Image.LANCZOS)
            preview_photo = ImageTk.PhotoImage(preview_image)
            
            # 更新预览标签
            self.preview_label.config(image=preview_photo, text="")
            self.preview_label.image = preview_photo  # 保持引用
            
        except Exception as e:
            print(f"预览更新错误: {e}")
    
    def confirm_crop(self):
        """确认裁剪"""
        if not self.selection_coords:
            messagebox.showwarning("警告", "请先选择要裁剪的区域")
            return
        
        try:
            x1, y1, x2, y2 = self.selection_coords
            
            # 计算在原始图片中的坐标
            orig_x1 = int(x1 / self.scale)
            orig_y1 = int(y1 / self.scale)
            orig_x2 = int(x2 / self.scale)
            orig_y2 = int(y2 / self.scale)
            
            # 裁剪图片
            crop_box = (
                min(orig_x1, orig_x2),
                min(orig_y1, orig_y2),
                max(orig_x1, orig_x2),
                max(orig_y1, orig_y2)
            )
            
            self.result_image = self.original_image.crop(crop_box)
            
            # 调整到合适的头像尺寸（比如128x128）
            avatar_size = (128, 128)
            self.result_image = self.result_image.resize(avatar_size, Image.LANCZOS)
            
            self.window.destroy()
            
        except Exception as e:
            messagebox.showerror("错误", f"裁剪失败: {str(e)}")
    
    def cancel_crop(self):
        """取消裁剪"""
        self.result_image = None
        self.window.destroy()
    
    def show(self):
        """显示裁剪窗口并返回结果"""
        self.window.wait_window()  # 等待窗口关闭
        return self.result_image


class ChatClientGUI:
    def __init__(self, root):
        """
        初始化聊天客户端GUI
        :param root: tkinter根窗口
        """
        self.root = root
        self.root.title("聊天室客户端 - 支持用户系统和图片传输")
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        
        # 客户端socket和连接状态
        self.client_socket = None
        self.connected = False
        
        # 用户信息
        self.username = ""
        self.avatar_path = None
        self.avatar_base64 = None
        
        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('chat_client.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # 创建GUI界面
        self.create_widgets()
        
        # 绑定窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_widgets(self):
        """创建GUI组件"""
        # 用户信息配置框架
        user_frame = ttk.LabelFrame(self.root, text="👤 用户信息", padding="10")
        user_frame.pack(fill="x", padx=10, pady=5)
        
        # 用户名输入
        ttk.Label(user_frame, text="用户名:").grid(row=0, column=0, sticky="w", padx=5)
        self.username_var = tk.StringVar(value="用户")
        self.username_entry = ttk.Entry(user_frame, textvariable=self.username_var, width=20)
        self.username_entry.grid(row=0, column=1, padx=5)
        
        # 头像选择
        ttk.Label(user_frame, text="头像:").grid(row=0, column=2, sticky="w", padx=5)
        self.avatar_btn = ttk.Button(user_frame, text="📷 选择头像", command=self.select_avatar)
        self.avatar_btn.grid(row=0, column=3, padx=5)
        
        # 头像预览
        self.avatar_label = tk.Label(user_frame, text="无头像", bg="lightgray", width=8, height=2)
        self.avatar_label.grid(row=0, column=4, padx=5)
        
        # 连接配置框架
        connection_frame = ttk.LabelFrame(self.root, text="🔌 连接配置", padding="10")
        connection_frame.pack(fill="x", padx=10, pady=5)
        
        # IP地址输入
        ttk.Label(connection_frame, text="服务器IP地址:").grid(row=0, column=0, sticky="w", padx=5)
        self.ip_var = tk.StringVar(value="localhost")
        self.ip_entry = ttk.Entry(connection_frame, textvariable=self.ip_var, width=20)
        self.ip_entry.grid(row=0, column=1, padx=5)
        
        # 端口号输入
        ttk.Label(connection_frame, text="端口号:").grid(row=0, column=2, sticky="w", padx=5)
        self.port_var = tk.StringVar(value="8887")
        self.port_entry = ttk.Entry(connection_frame, textvariable=self.port_var, width=10)
        self.port_entry.grid(row=0, column=3, padx=5)
        
        # 连接/断开按钮
        self.connect_btn = ttk.Button(connection_frame, text="连接", command=self.toggle_connection)
        self.connect_btn.grid(row=0, column=4, padx=10)
        
        # 连接状态标签
        self.status_var = tk.StringVar(value="未连接")
        self.status_label = ttk.Label(connection_frame, textvariable=self.status_var, foreground="red")
        self.status_label.grid(row=0, column=5, padx=5)
        
        # 消息显示区域
        message_frame = ttk.LabelFrame(self.root, text="💬 聊天记录", padding="10")
        message_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 创建可滚动的Frame用于显示消息和图片
        self.canvas = tk.Canvas(message_frame, bg="white")
        self.scrollbar_v = ttk.Scrollbar(message_frame, orient="vertical", command=self.canvas.yview)
        self.scrollbar_h = ttk.Scrollbar(message_frame, orient="horizontal", command=self.canvas.xview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar_v.set, xscrollcommand=self.scrollbar_h.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar_v.pack(side="right", fill="y")
        
        # 消息计数器
        self.message_count = 0
        
        # 消息输入区域
        input_frame = ttk.LabelFrame(self.root, text="📝 发送消息", padding="10")
        input_frame.pack(fill="x", padx=10, pady=5)
        
        # 消息输入框
        self.message_var = tk.StringVar()
        self.message_entry = ttk.Entry(input_frame, textvariable=self.message_var, width=40)
        self.message_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.message_entry.bind("<Return>", lambda e: self.send_message())
        
        # 发送按钮
        self.send_btn = ttk.Button(input_frame, text="💬 发送文字", command=self.send_message)
        self.send_btn.pack(side="right", padx=(0, 5))
        
        # 发送图片按钮
        self.send_image_btn = ttk.Button(input_frame, text="🖼️ 发送图片", command=self.send_image)
        self.send_image_btn.pack(side="right", padx=(0, 5))
        
        # 快捷命令按钮
        command_frame = ttk.LabelFrame(self.root, text="⚡ 快捷命令", padding="10")
        command_frame.pack(fill="x", padx=10, pady=5)
        
        # 添加快捷命令按钮
        ttk.Button(command_frame, text="🕐 时间", command=lambda: self.send_command("time")).pack(side="left", padx=5)
        ttk.Button(command_frame, text="ℹ️ 信息", command=lambda: self.send_command("info")).pack(side="left", padx=5)
        ttk.Button(command_frame, text="👋 问候", command=lambda: self.send_command("hello")).pack(side="left", padx=5)
        
        # 初始状态设置
        self.set_send_state(False)
    
    def select_avatar(self):
        """选择头像"""
        file_path = filedialog.askopenfilename(
            title="选择头像图片",
            filetypes=[
                ("图片文件", "*.png *.jpg *.jpeg *.gif *.bmp"),
                ("PNG文件", "*.png"),
                ("JPEG文件", "*.jpg *.jpeg"),
                ("所有文件", "*.*")
            ]
        )
        
        if file_path:
            try:
                # 显示处理中提示
                self.avatar_label.config(text="处理中...", image="")
                self.root.update()  # 强制更新界面
                
                # 检查文件大小（限制为1MB）
                file_size = os.path.getsize(file_path)
                if file_size > 1024 * 1024:  # 1MB
                    messagebox.showerror("文件太大", "头像文件不能超过1MB")
                    self.avatar_label.config(text="无头像")
                    return
                
                # 打开图片进行裁剪
                original_image = Image.open(file_path)
                cropped_image = self.crop_avatar_image(original_image)
                
                if cropped_image is None:
                    # 用户取消了裁剪
                    self.avatar_label.config(text="无头像")
                    return
                
                # 将裁剪后的图片转换为bytes用于base64编码
                img_byte_arr = io.BytesIO()
                cropped_image.save(img_byte_arr, format='PNG')
                avatar_data = img_byte_arr.getvalue()
                
                # 编码为base64
                self.avatar_base64 = base64.b64encode(avatar_data).decode('utf-8')
                self.avatar_path = file_path
                
                # 显示头像预览 - 使用兼容的重采样方法
                preview_image = cropped_image.copy()
                
                # 使用兼容的重采样方法
                try:
                    # 尝试使用新版本的Pillow
                    preview_image.thumbnail((40, 40), Image.Resampling.LANCZOS)
                except AttributeError:
                    try:
                        # 使用旧版本的Pillow
                        preview_image.thumbnail((40, 40), Image.LANCZOS)
                    except AttributeError:
                        # 使用最基本的重采样方法
                        preview_image.thumbnail((40, 40), Image.ANTIALIAS)
                
                # 转换为PhotoImage
                photo = ImageTk.PhotoImage(preview_image)
                
                # 更新头像显示
                self.avatar_label.config(image=photo, text="")
                self.avatar_label.image = photo  # 保持引用
                
                self.logger.info(f"已选择并裁剪头像: {file_path}")
                
            except Exception as e:
                messagebox.showerror("头像错误", f"头像处理失败: {str(e)}")
                self.avatar_label.config(text="无头像", image="")
                self.logger.error(f"头像处理失败: {e}")
                # 重置头像相关变量
                self.avatar_base64 = None
                self.avatar_path = None

    def crop_avatar_image(self, image):
        """头像裁剪功能"""
        return AvatarCropWindow(self.root, image).show()


    def set_send_state(self, enabled):
        """设置发送相关组件的启用状态"""
        state = "normal" if enabled else "disabled"
        self.message_entry.config(state=state)
        self.send_btn.config(state=state)
        self.send_image_btn.config(state=state)
        
        # 在连接后禁用用户信息修改
        if enabled:
            self.username_entry.config(state="disabled")
            self.avatar_btn.config(state="disabled")
        else:
            self.username_entry.config(state="normal")
            self.avatar_btn.config(state="normal")
        
        # 快捷命令按钮状态
        for widget in self.root.children.values():
            if isinstance(widget, ttk.LabelFrame) and widget.cget("text") == "⚡ 快捷命令":
                for btn in widget.children.values():
                    if isinstance(btn, ttk.Button):
                        btn.config(state=state)
    
    def add_message(self, username, message, color="black", message_type="text", image_data=None, avatar_data=None):
        """在消息区域添加消息"""
        # 创建消息框架
        msg_frame = ttk.Frame(self.scrollable_frame, relief="solid", borderwidth=1)
        msg_frame.pack(fill="x", padx=10, pady=5, anchor="w")
        
        # 消息头部（用户信息）
        header_frame = ttk.Frame(msg_frame)
        header_frame.pack(fill="x", padx=5, pady=5)
        
        # 用户头像
        if avatar_data:
            try:
                avatar_image = Image.open(io.BytesIO(base64.b64decode(avatar_data)))
                avatar_image.thumbnail((30, 30), Image.Resampling.LANCZOS)
                avatar_photo = ImageTk.PhotoImage(avatar_image)
                
                avatar_label = tk.Label(header_frame, image=avatar_photo)
                avatar_label.image = avatar_photo  # 保持引用
                avatar_label.pack(side="left", padx=(0, 5))
            except:
                # 默认头像
                default_label = tk.Label(header_frame, text="👤", font=("Arial", 16))
                default_label.pack(side="left", padx=(0, 5))
        else:
            # 默认头像
            default_label = tk.Label(header_frame, text="👤", font=("Arial", 16))
            default_label.pack(side="left", padx=(0, 5))
        
        # 用户名和时间戳
        user_info_frame = ttk.Frame(header_frame)
        user_info_frame.pack(side="left", fill="x", expand=True)
        
        username_label = ttk.Label(user_info_frame, text=username, font=("Arial", 10, "bold"), foreground=color)
        username_label.pack(anchor="w")
        
        timestamp = datetime.now().strftime('%H:%M:%S')
        time_label = ttk.Label(user_info_frame, text=f"[{timestamp}]", foreground="gray", font=("Arial", 8))
        time_label.pack(anchor="w")
        
        # 消息内容
        content_frame = ttk.Frame(msg_frame)
        content_frame.pack(fill="x", padx=5, pady=(0, 5))
        
        if message_type == "text":
            # 文本消息
            msg_label = ttk.Label(content_frame, text=message, font=("Arial", 10), wraplength=600)
            msg_label.pack(anchor="w", padx=(35, 0))  # 缩进对齐头像
        elif message_type == "image":
            # 图片消息
            if image_data:
                try:
                    # 显示图片预览
                    img = Image.open(image_data)
                    # 调整图片大小
                    img.thumbnail((300, 300), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    
                    img_label = tk.Label(content_frame, image=photo, bg="white", relief="solid", borderwidth=1)
                    img_label.image = photo  # 保持引用
                    img_label.pack(anchor="w", pady=5, padx=(35, 0))  # 缩进对齐头像
                    
                    # 添加图片说明
                    desc_label = ttk.Label(content_frame, text=message, font=("Arial", 9), foreground="gray")
                    desc_label.pack(anchor="w", padx=(35, 0))
                except Exception as e:
                    # 如果图片无法显示，显示错误信息
                    error_label = ttk.Label(content_frame, text=f"图片显示错误: {str(e)}", foreground="red")
                    error_label.pack(anchor="w", padx=(35, 0))
        
        # 自动滚动到底部
        self.root.after(100, self._scroll_to_bottom)
        self.message_count += 1
    
    def _scroll_to_bottom(self):
        """滚动到底部"""
        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1.0)
    
    def toggle_connection(self):
        """切换连接状态"""
        if self.connected:
            self.disconnect_from_server()
        else:
            self.connect_to_server()
    
    def connect_to_server(self):
        """连接到服务器"""
        try:
            host = self.ip_var.get().strip()
            port = int(self.port_var.get().strip())
            self.username = self.username_var.get().strip() or "用户"
            
            # 1. 创建客户端socket
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.settimeout(10)  # 设置连接超时
            
            # 2. 连接到服务器
            self.client_socket.connect((host, port))
            
            self.connected = True
            self.status_var.set("已连接")
            self.status_label.config(foreground="green")
            self.connect_btn.config(text="断开")
            self.set_send_state(True)
            
            self.add_message("系统", f"✅ 成功连接到服务器 {host}:{port}", "green")
            self.logger.info(f"成功连接到服务器 {host}:{port}")
            
            # 3. 启动接收消息的线程（先启动接收线程）
            self.client_socket.settimeout(1)  # 设置接收超时，避免阻塞
            receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
            receive_thread.start()
            
            # 4. 等待一小段时间确保接收线程已经启动
            import time
            time.sleep(0.1)
            
            # 5. 发送用户信息到服务器
            self.send_user_info()
            
        except ValueError:
            messagebox.showerror("错误", "端口号必须是整数")
        except socket.timeout:
            messagebox.showerror("连接超时", "连接服务器超时，请检查IP地址和端口号")
            self.add_message("系统", "连接超时", "red")
        except ConnectionRefusedError:
            messagebox.showerror("连接拒绝", "服务器拒绝连接，请确认服务器已启动")
            self.add_message("系统", "连接被拒绝", "red")
        except Exception as e:
            messagebox.showerror("连接错误", f"连接失败: {str(e)}")
            self.add_message("系统", f"连接失败: {str(e)}", "red")
            self.logger.error(f"连接失败: {e}")
    
    def send_user_info(self):
        """发送用户信息到服务器"""
        try:
            user_info = {
                'type': 'user_info',
                'username': self.username,
                'avatar': self.avatar_base64,
                'timestamp': datetime.now().isoformat()
            }
            
            data = json.dumps(user_info).encode('utf-8')
            length = len(data).to_bytes(4, byteorder='big')
            self.client_socket.send(length + data)
            
            self.logger.info(f"已发送用户信息: {self.username}")
            
        except Exception as e:
            self.logger.error(f"发送用户信息失败: {e}")
    
    def disconnect_from_server(self):
        """断开与服务器的连接"""
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
            self.client_socket = None
        
        self.connected = False
        self.status_var.set("未连接")
        self.status_label.config(foreground="red")
        self.connect_btn.config(text="连接")
        self.set_send_state(False)
        
        self.add_message("系统", "已断开连接", "orange")
        self.logger.info("断开连接")
    
    def receive_messages(self):
        """接收服务器消息的线程函数"""
        while self.connected and self.client_socket:
            try:
                # 接收数据长度
                length_data = self.client_socket.recv(4)
                if not length_data:
                    break
                
                data_length = int.from_bytes(length_data, byteorder='big')
                
                # 接收完整数据
                data = b''
                while len(data) < data_length:
                    chunk = self.client_socket.recv(min(data_length - len(data), 4096))
                    if not chunk:
                        break
                    data += chunk
                
                if len(data) == data_length:
                    try:
                        # 尝试解析为JSON（用于图片等结构化数据）
                        message_data = json.loads(data.decode('utf-8'))
                        if message_data.get('type') == 'image':
                            # 处理图片消息
                            image_data = base64.b64decode(message_data['data'])
                            image_file = io.BytesIO(image_data)
                            username = message_data.get('username', '未知用户')
                            avatar_data = message_data.get('avatar')
                            filename = message_data.get('filename', 'unknown')
                            self.add_message(username, f"发送了图片: {filename}", "blue", "image", image_file, avatar_data)
                        else:
                            # 处理其他结构化消息
                            username = message_data.get('username', '服务器')
                            message_text = message_data.get('message', str(message_data))
                            avatar_data = message_data.get('avatar')
                            self.add_message(username, message_text, "blue", "text", None, avatar_data)
                    except json.JSONDecodeError:
                        # 普通文本消息
                        message = data.decode('utf-8')
                        self.add_message("服务器", message, "blue")
                
            except socket.timeout:
                continue
            except socket.error:
                break
            except Exception as e:
                self.logger.error(f"接收消息错误: {e}")
                break
        
        # 如果循环结束但仍然显示连接状态，则更新状态
        if self.connected:
            self.root.after(0, self.disconnect_from_server)
    
    def send_message(self):
        """发送文字消息到服务器"""
        if not self.connected or not self.client_socket:
            messagebox.showwarning("警告", "请先连接到服务器")
            return
        
        message = self.message_var.get().strip()
        if not message:
            return
        
        try:
            # 构建消息对象
            message_obj = {
                'type': 'text',
                'username': self.username,
                'message': message,
                'avatar': self.avatar_base64,
                'timestamp': datetime.now().isoformat()
            }
            
            # 发送消息
            data = json.dumps(message_obj).encode('utf-8')
            length = len(data).to_bytes(4, byteorder='big')
            self.client_socket.send(length + data)
            
            # 在本地显示发送的消息
            self.add_message(self.username, message, "green", "text", None, self.avatar_base64)
            self.message_var.set("")  # 清空输入框
            
            # 如果发送了quit命令，断开连接
            if message.lower() == 'quit':
                self.root.after(1000, self.disconnect_from_server)
                
        except Exception as e:
            messagebox.showerror("发送错误", f"发送消息失败: {str(e)}")
            self.add_message("系统", f"发送失败: {str(e)}", "red")
            self.logger.error(f"发送消息失败: {e}")
    
    def send_image(self):
        """发送图片"""
        if not self.connected or not self.client_socket:
            messagebox.showwarning("警告", "请先连接到服务器")
            return
        
        # 选择图片文件
        file_path = filedialog.askopenfilename(
            title="选择图片",
            filetypes=[
                ("图片文件", "*.png *.jpg *.jpeg *.gif *.bmp"),
                ("PNG文件", "*.png"),
                ("JPEG文件", "*.jpg *.jpeg"),
                ("所有文件", "*.*")
            ]
        )
        
        if not file_path:
            return
        
        try:
            # 检查文件大小（限制为5MB）
            file_size = os.path.getsize(file_path)
            if file_size > 5 * 1024 * 1024:  # 5MB
                messagebox.showerror("文件太大", "图片文件不能超过5MB")
                return
            
            # 读取图片文件
            with open(file_path, 'rb') as f:
                image_data = f.read()
            
            # 编码为base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # 构建图片消息
            image_message = {
                'type': 'image',
                'username': self.username,
                'filename': os.path.basename(file_path),
                'size': file_size,
                'data': image_base64,
                'avatar': self.avatar_base64,
                'timestamp': datetime.now().isoformat()
            }
            
            # 发送图片消息
            data = json.dumps(image_message).encode('utf-8')
            length = len(data).to_bytes(4, byteorder='big')
            self.client_socket.send(length + data)
            
            # 在本地显示发送的图片
            self.add_message(self.username, f"发送了图片: {os.path.basename(file_path)}", "green", "image", file_path, self.avatar_base64)
            self.logger.info(f"发送图片: {file_path}")
            
        except Exception as e:
            messagebox.showerror("发送错误", f"发送图片失败: {str(e)}")
            self.add_message("系统", f"图片发送失败: {str(e)}", "red")
            self.logger.error(f"发送图片失败: {e}")
    
    def send_command(self, command):
        """发送快捷命令"""
        if not self.connected:
            messagebox.showwarning("警告", "请先连接到服务器")
            return
        
        self.message_var.set(command)
        self.send_message()
    
    def on_closing(self):
        """窗口关闭事件处理"""
        if self.connected:
            self.disconnect_from_server()
        self.root.destroy()

def main():
    """主函数"""
    root = tk.Tk()
    app = ChatClientGUI(root)
    
    # 设置窗口图标（如果有的话）
    try:
        root.iconbitmap("chat.ico")
    except:
        pass
    
    # 启动GUI主循环
    root.mainloop()

if __name__ == "__main__":
    main()
