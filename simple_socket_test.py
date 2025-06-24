#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SOCKET网络编程实验 - 自动化测试脚本
用于测试服务器和客户端的基本功能
"""

import socket
import threading
import time
import sys
from datetime import datetime

class SocketTester:
    def __init__(self):
        self.test_results = []
        
    def log_test(self, test_name, success, message=""):
        """记录测试结果"""
        status = "PASS" if success else "FAIL"
        timestamp = datetime.now().strftime("%H:%M:%S")
        result = f"[{timestamp}] {test_name}: {status}"
        if message:
            result += f" - {message}"
        
        print(result)
        self.test_results.append((test_name, success, message))
    
    def test_server_startup(self, host='localhost', port=8889):
        """测试服务器启动功能"""
        print(f"\n=== 测试服务器启动 ({host}:{port}) ===")
        
        try:
            # 创建测试服务器
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((host, port))
            server_socket.listen(1)
            
            self.log_test("服务器套接字创建", True, f"监听 {host}:{port}")
            
            # 测试连接超时
            server_socket.settimeout(0.1)
            try:
                client_socket, addr = server_socket.accept()
                self.log_test("无客户端连接测试", False, "意外接收到连接")
            except socket.timeout:
                self.log_test("无客户端连接测试", True, "正确超时")
            
            server_socket.close()
            self.log_test("服务器关闭", True)
            
        except Exception as e:
            self.log_test("服务器启动", False, str(e))
    
    def test_client_connection(self, host='localhost', port=8889):
        """测试客户端连接功能"""
        print(f"\n=== 测试客户端连接 ({host}:{port}) ===")
        
        # 启动测试服务器
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            server_socket.bind((host, port))
            server_socket.listen(1)
            server_running = True
            
            def test_server():
                nonlocal server_running
                try:
                    while server_running:
                        server_socket.settimeout(1.0)
                        try:
                            client_socket, addr = server_socket.accept()
                            self.log_test("客户端连接接受", True, f"来自 {addr}")
                            
                            # 测试数据接收
                            data = client_socket.recv(1024)
                            if data:
                                message = data.decode('utf-8')
                                self.log_test("数据接收", True, f"收到: {message}")
                                
                                # 发送响应
                                response = f"服务器回复: {message}"
                                client_socket.send(response.encode('utf-8'))
                                self.log_test("数据发送", True, f"发送: {response}")
                            
                            client_socket.close()
                            
                        except socket.timeout:
                            continue
                        except Exception as e:
                            if server_running:
                                self.log_test("服务器处理", False, str(e))
                            break
                            
                except Exception as e:
                    self.log_test("测试服务器", False, str(e))
            
            # 启动测试服务器线程
            server_thread = threading.Thread(target=test_server)
            server_thread.daemon = True
            server_thread.start()
            
            time.sleep(0.1)  # 等待服务器启动
            
            # 测试客户端连接
            try:
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client_socket.connect((host, port))
                self.log_test("客户端连接建立", True, f"连接到 {host}:{port}")
                
                # 测试数据发送
                test_message = "Hello, Server!"
                client_socket.send(test_message.encode('utf-8'))
                self.log_test("客户端数据发送", True, f"发送: {test_message}")
                
                # 测试数据接收
                response = client_socket.recv(1024)
                if response:
                    response_text = response.decode('utf-8')
                    self.log_test("客户端数据接收", True, f"收到: {response_text}")
                
                client_socket.close()
                self.log_test("客户端连接关闭", True)
                
            except Exception as e:
                self.log_test("客户端连接", False, str(e))
            
        except Exception as e:
            self.log_test("测试环境设置", False, str(e))
        finally:
            server_running = False
            try:
                server_socket.close()
            except:
                pass
    
    def test_concurrent_connections(self, host='localhost', port=8890, num_clients=3):
        """测试并发连接"""
        print(f"\n=== 测试并发连接 ({num_clients}个客户端) ===")
        
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            server_socket.bind((host, port))
            server_socket.listen(num_clients)
            server_running = True
            connected_clients = []
            
            def handle_client(client_socket, client_id):
                try:
                    data = client_socket.recv(1024)
                    if data:
                        message = data.decode('utf-8')
                        response = f"服务器回复客户端{client_id}: {message}"
                        client_socket.send(response.encode('utf-8'))
                        self.log_test(f"客户端{client_id}通信", True, f"处理消息: {message}")
                    client_socket.close()
                except Exception as e:
                    self.log_test(f"客户端{client_id}处理", False, str(e))
            
            def test_server():
                nonlocal server_running
                client_count = 0
                try:
                    while server_running and client_count < num_clients:
                        server_socket.settimeout(2.0)
                        try:
                            client_socket, addr = server_socket.accept()
                            client_count += 1
                            connected_clients.append(client_socket)
                            
                            # 为每个客户端创建处理线程
                            client_thread = threading.Thread(
                                target=handle_client, 
                                args=(client_socket, client_count)
                            )
                            client_thread.daemon = True
                            client_thread.start()
                            
                        except socket.timeout:
                            break
                        except Exception as e:
                            if server_running:
                                self.log_test("并发服务器", False, str(e))
                            break
                            
                except Exception as e:
                    self.log_test("并发测试服务器", False, str(e))
            
            # 启动服务器线程
            server_thread = threading.Thread(target=test_server)
            server_thread.daemon = True
            server_thread.start()
            
            time.sleep(0.1)  # 等待服务器启动
            
            # 创建多个客户端连接
            def create_client(client_id):
                try:
                    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    client_socket.connect((host, port))
                    
                    message = f"Hello from client {client_id}"
                    client_socket.send(message.encode('utf-8'))
                    
                    response = client_socket.recv(1024)
                    if response:
                        self.log_test(f"客户端{client_id}响应", True, response.decode('utf-8'))
                    
                    client_socket.close()
                    
                except Exception as e:
                    self.log_test(f"客户端{client_id}连接", False, str(e))
            
            # 并发创建客户端
            client_threads = []
            for i in range(1, num_clients + 1):
                thread = threading.Thread(target=create_client, args=(i,))
                client_threads.append(thread)
                thread.start()
            
            # 等待所有客户端完成
            for thread in client_threads:
                thread.join(timeout=5)
            
            self.log_test("并发连接测试", True, f"完成 {num_clients} 个客户端测试")
            
        except Exception as e:
            self.log_test("并发连接设置", False, str(e))
        finally:
            server_running = False
            for client in connected_clients:
                try:
                    client.close()
                except:
                    pass
            try:
                server_socket.close()
            except:
                pass
    
    def test_error_handling(self, host='localhost', port=8891):
        """测试错误处理"""
        print(f"\n=== 测试错误处理 ===")
        
        # 测试连接到不存在的服务器
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(1.0)
            client_socket.connect((host, port))  # 没有服务器监听
            self.log_test("连接不存在服务器", False, "应该失败但成功了")
        except ConnectionRefusedError:
            self.log_test("连接拒绝处理", True, "正确捕获ConnectionRefusedError")
        except Exception as e:
            self.log_test("连接错误处理", True, f"捕获异常: {type(e).__name__}")
        
        # 测试无效IP地址
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(1.0)
            client_socket.connect(("999.999.999.999", port))
            self.log_test("无效IP连接", False, "应该失败但成功了")
        except Exception as e:
            self.log_test("无效IP处理", True, f"正确捕获: {type(e).__name__}")
    
    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 50)
        print("SOCKET网络编程实验 - 自动化测试")
        print("=" * 50)
        
        start_time = time.time()
        
        # 运行各项测试
        self.test_server_startup()
        self.test_client_connection()
        self.test_concurrent_connections()
        self.test_error_handling()
        
        end_time = time.time()
        
        # 统计测试结果
        total_tests = len(self.test_results)
        passed_tests = sum(1 for _, success, _ in self.test_results if success)
        failed_tests = total_tests - passed_tests
        
        print("\n" + "=" * 50)
        print("测试结果汇总")
        print("=" * 50)
        print(f"总测试数: {total_tests}")
        print(f"通过测试: {passed_tests}")
        print(f"失败测试: {failed_tests}")
        print(f"成功率: {(passed_tests/total_tests*100):.1f}%")
        print(f"测试耗时: {(end_time-start_time):.2f}秒")
        
        if failed_tests > 0:
            print("\n失败的测试:")
            for test_name, success, message in self.test_results:
                if not success:
                    print(f"- {test_name}: {message}")
        
        print("\n测试完成！")
        
        return failed_tests == 0

def main():
    """主函数"""
    tester = SocketTester()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("SOCKET网络编程实验 - 自动化测试脚本")
        print("用法: python test_socket.py")
        print("这个脚本会自动测试基本的socket功能")
        return
    
    try:
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n测试运行出错: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
