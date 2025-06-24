#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SOCKET网络编程实验 - 客户端控制台版
基于TCP协议的C/S架构客户端实现（命令行版本）
"""

import socket
import threading
import logging
from datetime import datetime

class SocketClient:
    def __init__(self, host='localhost', port=8888):
        """
        初始化客户端
        :param host: 服务器IP地址
        :param port: 服务器端口号
        """
        self.host = host
        self.port = port
        self.client_socket = None
        self.connected = False
        
        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('client_console.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def connect_to_server(self):
        """连接到服务器"""
        try:
            # 1. 创建TCP套接字
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            # 2. 连接到服务器
            print(f"正在连接到服务器 {self.host}:{self.port}...")
            self.client_socket.connect((self.host, self.port))
            
            self.connected = True
            print(f"成功连接到服务器 {self.host}:{self.port}")
            self.logger.info(f"连接到服务器成功: {self.host}:{self.port}")
            
            return True
            
        except ConnectionRefusedError:
            print("连接被拒绝，请确认服务器已启动")
            self.logger.error("连接被拒绝")
            return False
        except Exception as e:
            print(f"连接失败: {e}")
            self.logger.error(f"连接失败: {e}")
            return False
    
    def disconnect_from_server(self):
        """断开与服务器的连接"""
        self.connected = False
        if self.client_socket:
            try:
                # 4. 关闭连接
                self.client_socket.close()
            except:
                pass
            self.client_socket = None
        
        print("已断开连接")
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
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] 服务器: {message}")
                
            except socket.error:
                break
            except Exception as e:
                self.logger.error(f"接收消息错误: {e}")
                break
        
        # 如果连接断开，更新状态
        if self.connected:
            self.disconnect_from_server()
    
    def send_message(self, message):
        """发送消息到服务器"""
        if not self.connected or not self.client_socket:
            print("错误: 未连接到服务器")
            return False
        
        try:
            # 3. 发送消息到服务器
            self.client_socket.send(message.encode('utf-8'))
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] 发送: {message}")
            return True
            
        except Exception as e:
            print(f"发送消息失败: {e}")
            self.logger.error(f"发送消息失败: {e}")
            return False
    
    def start_interactive_session(self):
        """启动交互式会话"""
        if not self.connect_to_server():
            return
        
        # 启动接收消息的线程
        receive_thread = threading.Thread(target=self.receive_messages)
        receive_thread.daemon = True
        receive_thread.start()
        
        print("\n=== 开始交互式会话 ===")
        print("输入消息发送给服务器，输入 'quit' 退出")
        print("支持的命令:")
        print("- time: 获取服务器时间")
        print("- info: 获取服务器信息")
        print("- quit: 断开连接并退出")
        print("=" * 30)
        
        try:
            while self.connected:
                try:
                    message = input(">>> ").strip()
                    if not message:
                        continue
                    
                    if not self.send_message(message):
                        break
                    
                    if message.lower() == 'quit':
                        break
                        
                except KeyboardInterrupt:
                    print("\n接收到中断信号，正在断开连接...")
                    break
                except EOFError:
                    print("\n输入结束，正在断开连接...")
                    break
                    
        finally:
            self.disconnect_from_server()

def main():
    """主函数"""
    print("=== SOCKET网络编程实验 - 客户端控制台版 ===")
    
    # 获取连接配置
    try:
        host = input("请输入服务器IP地址 (默认: localhost): ").strip()
        if not host:
            host = 'localhost'
        
        port_input = input("请输入服务器端口号 (默认: 8888): ").strip()
        port = int(port_input) if port_input else 8888
        
        # 创建客户端并开始交互
        client = SocketClient(host, port)
        client.start_interactive_session()
        
    except ValueError:
        print("端口号必须是整数！")
    except Exception as e:
        print(f"客户端运行出错: {e}")

if __name__ == "__main__":
    main()
