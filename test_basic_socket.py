#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SOCKET网络编程实验 - 基础功能测试脚本
用于测试server.py、client_gui.py和client_console.py的基本功能
"""

import socket
import threading
import time
import sys
import subprocess
import os
from datetime import datetime

class BasicSocketTester:
    def __init__(self):
        self.test_results = []
        self.server_process = None
        
    def log_test(self, test_name, success, message=""):
        """记录测试结果"""
        status = "✅ PASS" if success else "❌ FAIL"
        timestamp = datetime.now().strftime("%H:%M:%S")
        result = f"[{timestamp}] {test_name}: {status}"
        if message:
            result += f" - {message}"
        
        print(result)
        self.test_results.append((test_name, success, message))
    
    def test_server_functionality(self, host='localhost', port=8889):
        """测试服务器核心功能（不启动server.py，直接使用SocketServer类）"""
        print(f"\n=== 测试服务器核心功能 ({host}:{port}) ===")
        
        try:
            # 导入server模块
            import server
            
            # 创建服务器实例
            test_server = server.SocketServer(host, port)
            self.log_test("服务器类创建", True, f"SocketServer({host}, {port})")
            
            # 在单独线程中启动服务器
            server_thread = threading.Thread(target=test_server.start_server)
            server_thread.daemon = True
            server_thread.start()
            
            # 等待服务器启动
            time.sleep(1)
            
            # 测试基本连接
            try:
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client_socket.settimeout(5.0)
                client_socket.connect((host, port))
                self.log_test("客户端连接建立", True, f"连接到 {host}:{port}")
                
                # 接收欢迎消息
                welcome = client_socket.recv(1024).decode('utf-8')
                if "欢迎连接到服务器" in welcome:
                    self.log_test("欢迎消息接收", True, "收到欢迎消息")
                else:
                    self.log_test("欢迎消息接收", False, f"意外消息: {welcome}")
                
                # 测试回声服务
                test_message = "Hello, Server!"
                client_socket.send(test_message.encode('utf-8'))
                response = client_socket.recv(1024).decode('utf-8')
                if test_message in response:
                    self.log_test("回声服务测试", True, f"收到: {response}")
                else:
                    self.log_test("回声服务测试", False, f"响应不匹配: {response}")
                
                # 测试time命令
                client_socket.send("time".encode('utf-8'))
                time_response = client_socket.recv(1024).decode('utf-8')
                if "服务器时间" in time_response:
                    self.log_test("time命令测试", True, "时间命令正常")
                else:
                    self.log_test("time命令测试", False, f"时间响应异常: {time_response}")
                
                # 测试info命令
                client_socket.send("info".encode('utf-8'))
                info_response = client_socket.recv(1024).decode('utf-8')
                if "服务器信息" in info_response:
                    self.log_test("info命令测试", True, "信息命令正常")
                else:
                    self.log_test("info命令测试", False, f"信息响应异常: {info_response}")
                
                client_socket.close()
                self.log_test("客户端连接关闭", True)
                
            except Exception as e:
                self.log_test("客户端连接测试", False, str(e))
            
            # 停止服务器
            test_server.stop_server()
            self.log_test("服务器停止", True)
            
        except ImportError:
            self.log_test("服务器模块导入", False, "无法导入server.py")
        except Exception as e:
            self.log_test("服务器功能测试", False, str(e))
    
    def test_server_startup_with_input_simulation(self):
        """测试server.py启动（通过模拟输入）"""
        print(f"\n=== 测试server.py启动 ===")
        
        try:
            # 检查server.py文件是否存在
            if not os.path.exists("server.py"):
                self.log_test("server.py文件检查", False, "server.py不存在")
                return
            
            self.log_test("server.py文件检查", True, "文件存在")
            
            # 模拟输入并启动server.py（测试10秒后终止）
            try:
                # 使用Popen启动server.py，通过stdin提供输入
                # 修复Windows下的中文编码问题
                process = subprocess.Popen(
                    [sys.executable, "server.py"],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding='gbk',  # 使用gbk编码处理Windows中文
                    errors='ignore'  # 忽略编码错误
                )
                
                # 模拟用户输入（默认值）
                input_data = "\n\n"  # 两个回车表示使用默认localhost和8888
                stdout, stderr = process.communicate(input=input_data, timeout=3)
                
                if process.returncode == 0 or "服务器启动成功" in stdout:
                    self.log_test("server.py启动测试", True, "服务器可以启动")
                else:
                    self.log_test("server.py启动测试", False, f"启动失败: {stderr}")
                    
            except subprocess.TimeoutExpired:
                # 超时说明服务器在运行，这是正常的
                process.terminate()
                self.log_test("server.py启动测试", True, "服务器正常运行（超时终止）")
            except Exception as e:
                self.log_test("server.py启动测试", False, f"启动异常: {e}")
                
        except Exception as e:
            self.log_test("server.py测试", False, str(e))
    
    def test_client_files_existence(self):
        """测试客户端文件是否存在"""
        print(f"\n=== 测试客户端文件存在性 ===")
        
        client_files = [
            ("client_gui.py", "图形界面客户端"),
            ("client_console.py", "控制台客户端")
        ]
        
        for filename, description in client_files:
            if os.path.exists(filename):
                self.log_test(f"{description}文件检查", True, f"{filename}存在")
                
                # 检查文件是否可以导入（语法检查）
                try:
                    # 使用subprocess检查Python语法，修复编码问题
                    result = subprocess.run(
                        [sys.executable, "-m", "py_compile", filename],
                        capture_output=True,
                        text=True,
                        timeout=10,
                        encoding='gbk',  # 使用gbk编码
                        errors='ignore'  # 忽略编码错误
                    )
                    
                    if result.returncode == 0:
                        self.log_test(f"{description}语法检查", True, "语法正确")
                    else:
                        self.log_test(f"{description}语法检查", False, f"语法错误: {result.stderr}")
                        
                except Exception as e:
                    self.log_test(f"{description}语法检查", False, str(e))
            else:
                self.log_test(f"{description}文件检查", False, f"{filename}不存在")
    
    def test_socket_basic_operations(self):
        """测试基本socket操作"""
        print(f"\n=== 测试基本Socket操作 ===")
        
        try:
            # 测试socket创建
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.log_test("Socket创建", True, "TCP套接字创建成功")
            
            # 测试地址重用选项
            test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.log_test("Socket选项设置", True, "SO_REUSEADDR设置成功")
            
            # 测试绑定（使用一个临时端口）
            test_socket.bind(('localhost', 0))  # 端口0表示系统自动分配
            bound_address = test_socket.getsockname()
            self.log_test("Socket绑定", True, f"绑定到 {bound_address}")
            
            # 测试监听
            test_socket.listen(1)
            self.log_test("Socket监听", True, "开始监听连接")
            
            # 关闭socket
            test_socket.close()
            self.log_test("Socket关闭", True, "套接字关闭成功")
            
        except Exception as e:
            self.log_test("基本Socket操作", False, str(e))
    
    def test_concurrent_connections(self, host='localhost', port=8890, num_clients=3):
        """测试并发连接"""
        print(f"\n=== 测试并发连接 ({num_clients}个客户端) ===")
        
        try:
            # 导入并创建服务器
            import server
            test_server = server.SocketServer(host, port)
            
            # 启动服务器线程
            server_thread = threading.Thread(target=test_server.start_server)
            server_thread.daemon = True
            server_thread.start()
            
            time.sleep(1)  # 等待服务器启动
            
            successful_connections = 0
            
            def test_client(client_id):
                nonlocal successful_connections
                try:
                    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    client_socket.settimeout(5.0)
                    client_socket.connect((host, port))
                    
                    # 接收欢迎消息
                    welcome = client_socket.recv(1024)
                    
                    # 发送测试消息
                    message = f"客户端{client_id}的消息"
                    client_socket.send(message.encode('utf-8'))
                    
                    # 接收响应
                    response = client_socket.recv(1024)
                    if response:
                        successful_connections += 1
                        
                    client_socket.close()
                    
                except Exception as e:
                    print(f"    客户端{client_id}连接失败: {e}")
            
            # 创建并发客户端
            threads = []
            for i in range(1, num_clients + 1):
                thread = threading.Thread(target=test_client, args=(i,))
                threads.append(thread)
                thread.start()
            
            # 等待所有客户端完成
            for thread in threads:
                thread.join(timeout=10)
            
            success_rate = (successful_connections / num_clients) * 100
            if success_rate >= 80:
                self.log_test("并发连接测试", True, f"成功率: {success_rate:.1f}% ({successful_connections}/{num_clients})")
            else:
                self.log_test("并发连接测试", False, f"成功率过低: {success_rate:.1f}%")
            
            # 停止服务器
            test_server.stop_server()
            
        except Exception as e:
            self.log_test("并发连接测试", False, str(e))
    
    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 60)
        print("🧪 SOCKET网络编程实验 - 基础功能测试")
        print("=" * 60)
        print(f"测试开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        start_time = time.time()
        
        try:
            # 运行各项测试
            self.test_socket_basic_operations()
            self.test_client_files_existence()
            self.test_server_functionality()
            self.test_server_startup_with_input_simulation()
            self.test_concurrent_connections()
            
        except KeyboardInterrupt:
            print("\n⚠️  测试被用户中断")
        except Exception as e:
            print(f"\n❌ 测试执行出错: {e}")
        
        end_time = time.time()
        
        # 生成测试报告
        self.generate_test_report(end_time - start_time)
    
    def generate_test_report(self, total_time):
        """生成测试报告"""
        print("\n" + "=" * 60)
        print("📊 基础功能测试结果报告")
        print("=" * 60)
        
        # 统计测试结果
        total_tests = len(self.test_results)
        passed_tests = sum(1 for _, success, _ in self.test_results if success)
        failed_tests = total_tests - passed_tests
        
        print(f"📈 测试统计:")
        print(f"   总测试数: {total_tests}")
        print(f"   通过测试: {passed_tests} ✅")
        print(f"   失败测试: {failed_tests} ❌")
        print(f"   成功率: {(passed_tests/total_tests*100):.1f}%")
        print(f"   测试耗时: {total_time:.2f}秒")
        
        if failed_tests > 0:
            print(f"\n❌ 失败测试详情:")
            for test_name, success, message in self.test_results:
                if not success:
                    print(f"   • {test_name}: {message}")
        
        print("\n" + "=" * 60)
        print("🏁 基础功能测试完成!")
        
        # 评估整体测试结果
        overall_success = (passed_tests / total_tests) >= 0.8 if total_tests > 0 else False
        if overall_success:
            print("🎉 恭喜！基础Socket功能测试通过，文件配合使用正常！")
        else:
            print("⚠️  部分基础功能测试失败，请检查相关文件。")
        
        return overall_success

def main():
    """主函数"""
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("🧪 SOCKET网络编程实验 - 基础功能测试脚本")
        print("=" * 50)
        print("功能: 测试server.py、client_gui.py、client_console.py基础功能")
        print("用法: python test_basic_socket.py")
        print("\n测试内容:")
        print("• 基本Socket操作")
        print("• 客户端文件存在性和语法检查")
        print("• 服务器核心功能")
        print("• 服务器启动模拟")
        print("• 并发连接处理")
        print("=" * 50)
        return
    
    try:
        input("按 Enter 键开始基础功能测试，或 Ctrl+C 取消...")
    except KeyboardInterrupt:
        print("\n❌ 测试已取消")
        return
    
    tester = BasicSocketTester()
    
    try:
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试运行出错: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
