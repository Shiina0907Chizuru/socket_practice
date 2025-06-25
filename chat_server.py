#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
聊天服务器 - 支持图片传输
基于TCP协议的聊天服务器实现（支持文本和图片消息）
"""

import socket
import threading
import logging
import json
import base64
import os
from datetime import datetime

class ChatServer:
    def __init__(self, host='localhost', port=8887):
        """
        初始化聊天服务器
        :param host: 服务器IP地址
        :param port: 服务器端口号
        """
        self.host = host
        self.port = port
        self.server_socket = None
        self.clients = []  # 存储客户端连接
        self.running = False
        
        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('chat_server.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # 创建接收文件的目录
        self.upload_dir = "uploaded_images"
        if not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir)
    
    def start_server(self):
        """启动服务器"""
        try:
            # 1. 创建服务器socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # 设置socket超时，避免accept()阻塞无法响应Ctrl+C
            self.server_socket.settimeout(1.0)
            
            # 2. 绑定地址和端口
            self.server_socket.bind((self.host, self.port))
            
            # 3. 开始监听
            self.server_socket.listen(5)
            self.running = True
            
            self.logger.info(f"🚀 聊天服务器启动成功！监听 {self.host}:{self.port}")
            self.logger.info("📁 图片上传目录：" + os.path.abspath(self.upload_dir))
            print(f"🚀 聊天服务器启动成功！监听 {self.host}:{self.port}")
            print("📁 图片上传目录：" + os.path.abspath(self.upload_dir))
            print("⚡ 服务器支持文本和图片消息传输")
            print("按 Ctrl+C 停止服务器\n")
            
            # 4. 接受客户端连接
            self.accept_connections()
            
        except Exception as e:
            self.logger.error(f"启动服务器失败: {e}")
            print(f"❌ 启动服务器失败: {e}")

    def accept_connections(self):
        """接受客户端连接"""
        while self.running:
            try:
                # 接受客户端连接（使用超时避免阻塞）
                client_socket, client_address = self.server_socket.accept()
                self.logger.info(f"新客户端连接: {client_address}")
                print(f"✅ 新客户端连接: {client_address}")
                
                # 为每个客户端创建处理线程
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, client_address),
                    daemon=True
                )
                client_thread.start()
                
            except socket.timeout:
                # 超时是正常的，继续循环检查self.running
                continue
            except OSError as e:
                # 服务器socket被关闭时会触发此异常
                if self.running:
                    self.logger.error(f"接受连接时出错: {e}")
                break
            except Exception as e:
                if self.running:
                    self.logger.error(f"接受连接时出错: {e}")
                break
    
    def handle_client(self, client_socket, client_address):
        """
        处理客户端连接
        :param client_socket: 客户端套接字
        :param client_address: 客户端地址
        """
        self.clients.append(client_socket)
        
        try:
            # 发送欢迎消息
            welcome_msg = f"🎉 欢迎连接到聊天服务器！当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            self.send_message(client_socket, welcome_msg)
            
            while self.running:
                try:
                    # 接收消息长度
                    length_data = client_socket.recv(4)
                    if not length_data:
                        break
                    
                    message_length = int.from_bytes(length_data, byteorder='big')
                    
                    # 接收完整消息
                    message_data = b""
                    while len(message_data) < message_length:
                        chunk = client_socket.recv(min(message_length - len(message_data), 4096))
                        if not chunk:
                            break
                        message_data += chunk
                    
                    if not message_data:
                        break
                    
                    # 处理消息
                    self.process_message(client_socket, client_address, message_data)
                    
                except socket.timeout:
                    continue
                except socket.error as e:
                    self.logger.error(f"处理客户端 {client_address} 时出错: {e}")
                    break
                    
        except Exception as e:
            self.logger.error(f"客户端处理异常: {e}")
        finally:
            # 关闭客户端连接
            if client_socket in self.clients:
                self.clients.remove(client_socket)
            client_socket.close()
            self.logger.info(f"客户端 {client_address} 断开连接")
            print(f"👋 客户端 {client_address} 断开连接")
    
    def process_message(self, client_socket, client_address, message_data):
        """处理收到的消息"""
        try:
            # 尝试解析为JSON（图片或结构化消息）
            try:
                message_json = json.loads(message_data.decode('utf-8'))
                
                if message_json.get('type') == 'image':
                    # 处理图片消息
                    self.handle_image_message(client_socket, client_address, message_json)
                elif message_json.get('type') == 'user_info':
                    # 处理用户信息
                    self.handle_user_info(client_socket, client_address, message_json)
                elif message_json.get('type') == 'text':
                    # 处理带用户信息的文本消息
                    self.handle_user_text_message(client_socket, client_address, message_json)
                else:
                    # 处理其他结构化消息
                    response = f"收到结构化消息: {message_json.get('type', 'unknown')}"
                    self.send_message(client_socket, response)
                    
            except json.JSONDecodeError:
                # 普通文本消息
                message = message_data.decode('utf-8')
                self.handle_text_message(client_socket, client_address, message)
                
        except Exception as e:
            self.logger.error(f"处理消息时出错: {e}")
            self.send_message(client_socket, f"消息处理错误: {str(e)}")

    def handle_text_message(self, client_socket, client_address, message):
        """处理文本消息"""
        self.logger.info(f"📝 收到来自 {client_address} 的文本消息: {message}")
        print(f"📝 {client_address}: {message}")
        
        # 处理特殊命令
        if message.lower() == 'quit':
            self.send_message(client_socket, "再见！")
            return
        elif message.lower() == 'time':
            response = f"⏰ 服务器时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        elif message.lower() == 'info':
            response = f"ℹ️ 服务器信息 - 地址: {self.host}:{self.port}, 在线客户端: {len(self.clients)}"
        elif message.lower() == 'hello':
            response = "👋 你好！很高兴见到你！"
        else:
            # 回声服务：将收到的消息返回给客户端
            response = f"💬 服务器回复: {message}"
        
        self.send_message(client_socket, response)
    
    def handle_image_message(self, client_socket, client_address, image_data):
        """处理图片消息"""
        try:
            filename = image_data.get('filename', 'unknown.jpg')
            file_size = image_data.get('size', 0)
            image_base64 = image_data.get('data', '')
            
            self.logger.info(f"🖼️ 收到来自 {client_address} 的图片: {filename} ({file_size} bytes)")
            print(f"🖼️ {client_address} 发送图片: {filename} ({file_size} bytes)")
            
            # 保存图片到本地
            if image_base64:
                try:
                    image_bytes = base64.b64decode(image_base64)
                    
                    # 生成唯一的文件名
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    safe_filename = f"{timestamp}_{filename}"
                    file_path = os.path.join(self.upload_dir, safe_filename)
                    
                    with open(file_path, 'wb') as f:
                        f.write(image_bytes)
                    
                    self.logger.info(f"图片已保存到: {file_path}")
                    
                    # 发送成功响应
                    response = f"✅ 图片 '{filename}' 接收成功！已保存到服务器。"
                    self.send_message(client_socket, response)
                    
                    # 这里可以扩展为广播图片给其他客户端
                    # self.broadcast_image(client_address, image_data)
                    
                except Exception as e:
                    self.logger.error(f"保存图片失败: {e}")
                    self.send_message(client_socket, f"❌ 图片保存失败: {str(e)}")
            else:
                self.send_message(client_socket, "❌ 图片数据为空")
                
        except Exception as e:
            self.logger.error(f"处理图片消息失败: {e}")
            self.send_message(client_socket, f"❌ 图片处理失败: {str(e)}")
    
    def handle_user_info(self, client_socket, client_address, user_data):
        """处理用户信息"""
        try:
            username = user_data.get('username', '匿名用户')
            avatar = user_data.get('avatar')
            
            self.logger.info(f"👤 用户 {client_address} 设置用户名: {username}")
            print(f"👤 用户 {client_address} 设置用户名: {username}")
            
            # 存储用户信息（可以扩展为字典来跟踪所有用户）
            # 这里可以将用户信息关联到客户端socket
            
            # 发送确认消息
            response = f"✅ 用户信息已收到！欢迎 {username}！"
            self.send_message(client_socket, response)
            
        except Exception as e:
            self.logger.error(f"处理用户信息失败: {e}")
            self.send_message(client_socket, f"❌ 用户信息处理失败: {str(e)}")

    def handle_user_text_message(self, client_socket, client_address, message_data):
        """处理带用户信息的文本消息"""
        try:
            username = message_data.get('username', '匿名用户')
            message = message_data.get('message', '')
            
            self.logger.info(f"💬 用户 {username} ({client_address}): {message}")
            print(f"💬 {username} ({client_address}): {message}")
            
            # 处理特殊命令
            if message.lower() == 'quit':
                self.send_message(client_socket, f"再见 {username}！")
                return
            elif message.lower() == 'time':
                response = f"⏰ 服务器时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            elif message.lower() == 'info':
                response = f"ℹ️ 服务器信息 - 地址: {self.host}:{self.port}, 在线客户端: {len(self.clients)}"
            elif message.lower() == 'hello':
                response = f"👋 你好 {username}！很高兴见到你！"
            else:
                # 回声服务：将收到的消息返回给客户端
                response = f"💬 服务器回复 {username}: {message}"
            
            self.send_message(client_socket, response)
            
        except Exception as e:
            self.logger.error(f"处理用户文本消息失败: {e}")
            self.send_message(client_socket, f"❌ 消息处理失败: {str(e)}")
    
    def send_message(self, client_socket, message):
        """发送消息给客户端"""
        try:
            data = message.encode('utf-8')
            length = len(data).to_bytes(4, byteorder='big')
            client_socket.send(length + data)
        except Exception as e:
            self.logger.error(f"发送消息失败: {e}")
    
    def broadcast_message(self, sender_address, message):
        """广播消息给所有客户端"""
        broadcast_msg = f"[{sender_address}] {message}"
        disconnected_clients = []
        
        for client in self.clients:
            try:
                self.send_message(client, broadcast_msg)
            except:
                disconnected_clients.append(client)
        
        # 移除断开连接的客户端
        for client in disconnected_clients:
            if client in self.clients:
                self.clients.remove(client)
    
    def stop_server(self):
        """停止服务器"""
        print("\n🛑 正在停止服务器...")
        self.running = False
        
        # 关闭所有客户端连接
        for client in self.clients[:]:  # 使用切片复制避免修改时的问题
            try:
                client.close()
            except:
                pass
        self.clients.clear()
        
        # 关闭服务器socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        self.logger.info("服务器已停止")
        print("🛑 服务器已停止")

def main():
    """主函数"""
    # 创建服务器实例
    server = ChatServer()
    
    try:
        # 启动服务器
        server.start_server()
    except KeyboardInterrupt:
        print("\n⚠️ 接收到停止信号...")
    except Exception as e:
        print(f"❌ 服务器运行出错: {e}")
    finally:
        # 确保服务器总是会被停止
        server.stop_server()
        print("👋 程序已退出")

if __name__ == "__main__":
    main()
