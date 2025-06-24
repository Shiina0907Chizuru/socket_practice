#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SOCKET网络编程实验 - 客户端GUI
基于TCP协议的C/S架构客户端实现（带图形界面）
"""

import socket
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import logging
from datetime import datetime

class SocketClientGUI:
    def __init__(self, root):
        """
        初始化客户端GUI
        :param root: tkinter根窗口
        """
        self.root = root
        self.root.title("SOCKET网络编程实验 - 客户端")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        # 客户端socket
        self.client_socket = None
        self.connected = False
        
        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('client.log', encoding='utf-8'),
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
        # 连接配置框架
        connection_frame = ttk.LabelFrame(self.root, text="连接配置", padding="10")
        connection_frame.pack(fill="x", padx=10, pady=5)
        
        # IP地址输入
        ttk.Label(connection_frame, text="服务器IP地址:").grid(row=0, column=0, sticky="w", padx=5)
        self.ip_var = tk.StringVar(value="localhost")
        self.ip_entry = ttk.Entry(connection_frame, textvariable=self.ip_var, width=20)
        self.ip_entry.grid(row=0, column=1, padx=5)
        
        # 端口号输入
        ttk.Label(connection_frame, text="端口号:").grid(row=0, column=2, sticky="w", padx=5)
        self.port_var = tk.StringVar(value="8888")
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
        message_frame = ttk.LabelFrame(self.root, text="消息记录", padding="10")
        message_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.message_text = scrolledtext.ScrolledText(
            message_frame, 
            height=15, 
            width=70,
            state="disabled",
            font=("Consolas", 10)
        )
        self.message_text.pack(fill="both", expand=True)
        
        # 消息输入区域
        input_frame = ttk.LabelFrame(self.root, text="发送消息", padding="10")
        input_frame.pack(fill="x", padx=10, pady=5)
        
        # 消息输入框
        self.message_var = tk.StringVar()
        self.message_entry = ttk.Entry(input_frame, textvariable=self.message_var, width=50)
        self.message_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.message_entry.bind("<Return>", lambda e: self.send_message())
        
        # 发送按钮
        self.send_btn = ttk.Button(input_frame, text="发送", command=self.send_message)
        self.send_btn.pack(side="right")
        
        # 快捷命令按钮
        command_frame = ttk.LabelFrame(self.root, text="快捷命令", padding="10")
        command_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(command_frame, text="获取时间", command=lambda: self.send_command("time")).pack(side="left", padx=5)
        ttk.Button(command_frame, text="服务器信息", command=lambda: self.send_command("info")).pack(side="left", padx=5)
        ttk.Button(command_frame, text="断开连接", command=lambda: self.send_command("quit")).pack(side="left", padx=5)
        
        # 初始状态下禁用发送相关组件
        self.set_send_state(False)
    
    def set_send_state(self, enabled):
        """设置发送相关组件的启用状态"""
        state = "normal" if enabled else "disabled"
        self.message_entry.config(state=state)
        self.send_btn.config(state=state)
        for widget in self.root.children.values():
            if isinstance(widget, ttk.LabelFrame) and widget.cget("text") == "快捷命令":
                for btn in widget.children.values():
                    if isinstance(btn, ttk.Button):
                        btn.config(state=state)
    
    def append_message(self, message, color="black"):
        """在消息区域添加消息"""
        self.message_text.config(state="normal")
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        self.message_text.insert(tk.END, formatted_message)
        self.message_text.see(tk.END)
        self.message_text.config(state="disabled")
        
        # 可以为不同类型的消息设置不同颜色
        if color != "black":
            start = self.message_text.index(f"end-{len(formatted_message)}c")
            end = self.message_text.index("end-1c")
            self.message_text.tag_add(color, start, end)
            self.message_text.tag_config(color, foreground=color)
    
    def toggle_connection(self):
        """切换连接状态"""
        if not self.connected:
            self.connect_to_server()
        else:
            self.disconnect_from_server()
    
    def connect_to_server(self):
        """连接到服务器"""
        try:
            host = self.ip_var.get().strip()
            port = int(self.port_var.get().strip())
            
            if not host:
                messagebox.showerror("错误", "请输入服务器IP地址")
                return
            
            # 1. 创建TCP套接字
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.settimeout(10)  # 设置连接超时
            
            # 2. 连接到服务器
            self.append_message(f"正在连接到 {host}:{port}...", "blue")
            self.client_socket.connect((host, port))
            
            self.connected = True
            self.status_var.set("已连接")
            self.status_label.config(foreground="green")
            self.connect_btn.config(text="断开")
            self.set_send_state(True)
            
            self.append_message(f"成功连接到服务器 {host}:{port}", "green")
            self.logger.info(f"连接到服务器成功: {host}:{port}")
            
            # 启动接收消息的线程
            receive_thread = threading.Thread(target=self.receive_messages)
            receive_thread.daemon = True
            receive_thread.start()
            
        except ValueError:
            messagebox.showerror("错误", "端口号必须是整数")
        except socket.timeout:
            messagebox.showerror("连接超时", "连接服务器超时，请检查IP地址和端口号")
            self.append_message("连接超时", "red")
        except ConnectionRefusedError:
            messagebox.showerror("连接拒绝", "服务器拒绝连接，请确认服务器已启动")
            self.append_message("连接被拒绝", "red")
        except Exception as e:
            messagebox.showerror("连接错误", f"连接失败: {str(e)}")
            self.append_message(f"连接失败: {str(e)}", "red")
            self.logger.error(f"连接失败: {e}")
    
    def disconnect_from_server(self):
        """断开与服务器的连接"""
        if self.client_socket:
            try:
                # 4. 关闭连接
                self.client_socket.close()
            except:
                pass
            self.client_socket = None
        
        self.connected = False
        self.status_var.set("未连接")
        self.status_label.config(foreground="red")
        self.connect_btn.config(text="连接")
        self.set_send_state(False)
        
        self.append_message("已断开连接", "orange")
        self.logger.info("断开连接")
    
    def receive_messages(self):
        """接收服务器消息的线程函数"""
        while self.connected and self.client_socket:
            try:
                # 3. 接收服务器响应
                data = self.client_socket.recv(1024)
                if not data:
                    break
                
                message = data.decode('utf-8')
                self.append_message(f"服务器: {message}", "blue")
                
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
        """发送消息到服务器"""
        if not self.connected or not self.client_socket:
            messagebox.showwarning("警告", "请先连接到服务器")
            return
        
        message = self.message_var.get().strip()
        if not message:
            return
        
        try:
            # 3. 发送消息到服务器
            self.client_socket.send(message.encode('utf-8'))
            self.append_message(f"发送: {message}")
            self.message_var.set("")  # 清空输入框
            
            # 如果发送了quit命令，断开连接
            if message.lower() == 'quit':
                self.root.after(1000, self.disconnect_from_server)
                
        except Exception as e:
            messagebox.showerror("发送错误", f"发送消息失败: {str(e)}")
            self.append_message(f"发送失败: {str(e)}", "red")
            self.logger.error(f"发送消息失败: {e}")
    
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
    app = SocketClientGUI(root)
    
    # 设置窗口图标（如果有的话）
    try:
        root.iconbitmap("client.ico")
    except:
        pass
    
    # 启动GUI主循环
    root.mainloop()

if __name__ == "__main__":
    main()
