#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTTP服务器 - 基于原生Socket实现的HTTP/1.1服务器
支持静态文件服务、REST API、请求分析、响应压缩等功能
"""

import socket
import threading
import time
import json
import os
import sys
import argparse
import mimetypes
import gzip
from urllib.parse import urlparse, parse_qs, unquote
from datetime import datetime, timezone
from advanced_logger import create_new_session

class HTTPRequest:
    """HTTP请求解析器"""
    
    def __init__(self, raw_request):
        self.raw_request = raw_request
        self.method = ""
        self.path = ""
        self.version = ""
        self.headers = {}
        self.query_params = {}
        self.body = ""
        self.is_valid = False
        
        self._parse_request()
    
    def _parse_request(self):
        """解析HTTP请求"""
        try:
            lines = self.raw_request.split('\r\n')
            if not lines:
                return
            
            # 解析请求行
            request_line = lines[0]
            parts = request_line.split(' ')
            if len(parts) != 3:
                return
            
            self.method, full_path, self.version = parts
            
            # 解析路径和查询参数
            parsed_url = urlparse(full_path)
            self.path = unquote(parsed_url.path)
            self.query_params = parse_qs(parsed_url.query)
            
            # 解析头部
            header_end = 1
            for i, line in enumerate(lines[1:], 1):
                if line == '':  # 空行表示头部结束
                    header_end = i + 1
                    break
                
                if ':' in line:
                    key, value = line.split(':', 1)
                    self.headers[key.strip().lower()] = value.strip()
            
            # 解析请求体
            if header_end < len(lines):
                self.body = '\r\n'.join(lines[header_end:])
            
            self.is_valid = True
            
        except Exception as e:
            print(f"请求解析错误: {e}")
            self.is_valid = False

class HTTPResponse:
    """HTTP响应构造器"""
    
    def __init__(self, status_code=200, headers=None, body="", binary_body=None):
        self.status_code = status_code
        self.headers = headers or {}
        self.body = body
        self.binary_body = binary_body
        
        # 默认头部
        if 'server' not in self.headers:
            self.headers['server'] = 'SocketHTTP/1.0'
        if 'date' not in self.headers:
            self.headers['date'] = datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')
        if 'content-type' not in self.headers and body:
            self.headers['content-type'] = 'text/html; charset=utf-8'
    
    def get_status_text(self):
        """获取状态码对应的文本"""
        status_texts = {
            200: 'OK',
            201: 'Created',
            400: 'Bad Request',
            404: 'Not Found',
            405: 'Method Not Allowed',
            500: 'Internal Server Error'
        }
        return status_texts.get(self.status_code, 'Unknown')
    
    def to_bytes(self):
        """转换为字节流"""
        # 确定内容长度
        if self.binary_body:
            content = self.binary_body
            self.headers['content-length'] = str(len(content))
        else:
            content = self.body.encode('utf-8')
            self.headers['content-length'] = str(len(content))
        
        # 构造响应头
        response_line = f"HTTP/1.1 {self.status_code} {self.get_status_text()}\r\n"
        headers_str = ""
        for key, value in self.headers.items():
            headers_str += f"{key.title()}: {value}\r\n"
        
        # 组合响应
        response_head = (response_line + headers_str + "\r\n").encode('utf-8')
        
        return response_head + content

class HTTPServer:
    """基于Socket的HTTP服务器"""
    
    def __init__(self, host='localhost', port=8080, document_root='./www'):
        self.host = host
        self.port = port
        self.document_root = document_root
        self.server_socket = None
        self.running = False
        self.clients = []
        self.request_count = 0
        self.start_time = None
        
        # 初始化日志
        self.logger = create_new_session("http_server")
        
        # 创建文档根目录
        os.makedirs(document_root, exist_ok=True)
        self._create_default_files()
        
        # 初始化MIME类型
        mimetypes.init()
        
        self.logger.info(f"HTTP服务器初始化 - {host}:{port}, 文档根目录: {document_root}")
    
    def _create_default_files(self):
        """创建默认的网页文件"""
        index_html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Socket HTTP 服务器</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; text-align: center; border-bottom: 2px solid #007bff; padding-bottom: 10px; }
        .feature { background: #f8f9fa; padding: 20px; margin: 15px 0; border-radius: 5px; border-left: 4px solid #007bff; }
        .api-section { background: #e9ecef; padding: 20px; margin: 15px 0; border-radius: 5px; }
        .code { background: #343a40; color: #f8f9fa; padding: 10px; border-radius: 3px; font-family: 'Courier New', monospace; margin: 10px 0; }
        .button { display: inline-block; background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 5px; }
        .button:hover { background: #0056b3; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }
        .stat-card { background: #007bff; color: white; padding: 20px; border-radius: 5px; text-align: center; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Socket HTTP 服务器</h1>
        
        <div class="feature">
            <h2>服务器特性</h2>
            <ul>
                <li>基于原生Socket实现的HTTP/1.1服务器</li>
                <li>静态文件服务支持</li>
                <li>REST API 接口</li>
                <li>多线程并发处理</li>
                <li>详细的请求日志记录</li>
                <li>实时服务器状态监控</li>
            </ul>
        </div>
        
        <div class="api-section">
            <h2>API 接口测试</h2>
            <p>以下是可用的API接口：</p>
            <div class="code">
                GET /api/status - 获取服务器状态<br>
                GET /api/time - 获取服务器时间<br>
                POST /api/echo - 回声测试（返回请求内容）<br>
                GET /api/clients - 获取客户端连接信息
            </div>
            <div style="text-align: center; margin: 20px 0;">
                <a href="/api/status" class="button">服务器状态</a>
                <a href="/api/time" class="button">服务器时间</a>
                <a href="/api/clients" class="button">客户端信息</a>
            </div>
        </div>
        
        <div class="stats" id="stats">
            <div class="stat-card">
                <h3>服务器运行中</h3>
                <p>Socket HTTP/1.1</p>
            </div>
            <div class="stat-card">
                <h3>支持功能</h3>
                <p>静态文件 + API</p>
            </div>
        </div>
        
        <div class="feature">
            <h2>测试建议</h2>
            <p>可以使用以下工具测试服务器：</p>
            <ul>
                <li><strong>浏览器:</strong> 直接访问各个页面和API</li>
                <li><strong>curl:</strong> <code>curl http://localhost:8080/api/status</code></li>
                <li><strong>网络性能测试器:</strong> 运行 network_performance_tester.py</li>
                <li><strong>Postman:</strong> 测试POST请求</li>
            </ul>
        </div>
    </div>
    
    <script>
        // 自动刷新服务器状态
        setInterval(function() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('stats').innerHTML = `
                        <div class="stat-card">
                            <h3>请求总数</h3>
                            <p>${data.request_count}</p>
                        </div>
                        <div class="stat-card">
                            <h3>活跃连接</h3>
                            <p>${data.active_connections}</p>
                        </div>
                        <div class="stat-card">
                            <h3>运行时间</h3>
                            <p>${data.uptime}</p>
                        </div>
                        <div class="stat-card">
                            <h3>服务器时间</h3>
                            <p>${new Date(data.server_time).toLocaleTimeString()}</p>
                        </div>
                    `;
                })
                .catch(err => console.log('状态更新失败:', err));
        }, 5000);
    </script>
</body>
</html>"""
        
        index_path = os.path.join(self.document_root, 'index.html')
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(index_html)
        
        # 创建一个简单的about页面
        about_html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>关于 - Socket HTTP 服务器</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }
        .container { max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; }
        h1 { color: #333; }
    </style>
</head>
<body>
    <div class="container">
        <h1>关于 Socket HTTP 服务器</h1>
        <p>这是一个基于Python原生Socket实现的HTTP/1.1服务器，用于学习和演示网络编程。</p>
        <p><a href="/">返回首页</a></p>
    </div>
</body>
</html>"""
        
        about_path = os.path.join(self.document_root, 'about.html')
        with open(about_path, 'w', encoding='utf-8') as f:
            f.write(about_html)
    
    def start(self):
        """启动HTTP服务器"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(10)
            
            self.running = True
            self.start_time = time.time()
            
            print(f"HTTP服务器启动成功!")
            print(f"服务地址: http://{self.host}:{self.port}")
            print(f"文档根目录: {self.document_root}")
            print(f"日志目录: {self.logger.get_session_directory()}")
            print("=" * 60)
            
            self.logger.info(f"HTTP服务器启动 - {self.host}:{self.port}")
            
            while self.running:
                try:
                    client_socket, client_address = self.server_socket.accept()
                    self.request_count += 1
                    
                    print(f"新连接: {client_address} (请求 #{self.request_count})")
                    
                    # 创建新线程处理客户端
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, client_address)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                except socket.error as e:
                    if self.running:
                        print(f"接受连接时发生错误: {e}")
                        self.logger.log_error("ACCEPT_ERROR", str(e))
        
        except Exception as e:
            print(f"服务器启动失败: {e}")
            self.logger.log_error("SERVER_START_ERROR", str(e))
        
        finally:
            self.stop()
    
    def handle_client(self, client_socket, client_address):
        """处理客户端请求"""
        try:
            self.clients.append(client_address)
            
            # 接收请求数据
            request_data = client_socket.recv(8192).decode('utf-8')
            
            if not request_data:
                return
            
            # 解析HTTP请求
            request = HTTPRequest(request_data)
            
            if not request.is_valid:
                response = HTTPResponse(400, body="<h1>400 Bad Request</h1>")
                client_socket.send(response.to_bytes())
                return
            
            print(f"{request.method} {request.path} - {client_address[0]}")
            
            # 记录请求日志
            self.logger.info(f"HTTP请求 - {client_address[0]} {request.method} {request.path}")
            self.logger.log_connection_event("HTTP_REQUEST", {
                'client_ip': client_address[0],
                'method': request.method,
                'path': request.path,
                'user_agent': request.headers.get('user-agent', 'Unknown'),
                'timestamp': datetime.now().isoformat()
            })
            
            # 路由处理
            response = self.route_request(request, client_address)
            
            # 发送响应
            client_socket.send(response.to_bytes())
            
        except Exception as e:
            print(f"处理客户端请求时发生错误: {e}")
            self.logger.log_error("CLIENT_HANDLE_ERROR", str(e), client_address[0])
            
            try:
                error_response = HTTPResponse(500, body="<h1>500 Internal Server Error</h1>")
                client_socket.send(error_response.to_bytes())
            except:
                pass
        
        finally:
            try:
                client_socket.close()
                if client_address in self.clients:
                    self.clients.remove(client_address)
            except:
                pass
    
    def route_request(self, request, client_address):
        """请求路由处理"""
        path = request.path
        
        # API路由
        if path.startswith('/api/'):
            return self.handle_api_request(request, client_address)
        
        # 静态文件路由
        return self.handle_static_file(request)
    
    def handle_api_request(self, request, client_address):
        """处理API请求"""
        path = request.path
        method = request.method
        
        try:
            if path == '/api/status' and method == 'GET':
                # 服务器状态
                uptime = time.time() - self.start_time
                status_data = {
                    'status': 'running',
                    'server': 'SocketHTTP/1.0',
                    'uptime': f"{uptime:.1f} seconds",
                    'request_count': self.request_count,
                    'active_connections': len(self.clients),
                    'server_time': datetime.now().isoformat(),
                    'host': self.host,
                    'port': self.port
                }
                
                return HTTPResponse(
                    200,
                    headers={'content-type': 'application/json'},
                    body=json.dumps(status_data, ensure_ascii=False, indent=2)
                )
            
            elif path == '/api/time' and method == 'GET':
                # 服务器时间
                time_data = {
                    'server_time': datetime.now().isoformat(),
                    'timestamp': time.time(),
                    'timezone': str(datetime.now().astimezone().tzinfo)
                }
                
                return HTTPResponse(
                    200,
                    headers={'content-type': 'application/json'},
                    body=json.dumps(time_data, ensure_ascii=False, indent=2)
                )
            
            elif path == '/api/echo' and method == 'POST':
                # 回声测试
                echo_data = {
                    'method': request.method,
                    'path': request.path,
                    'headers': dict(request.headers),
                    'query_params': request.query_params,
                    'body': request.body,
                    'client_ip': client_address[0],
                    'echo_time': datetime.now().isoformat()
                }
                
                return HTTPResponse(
                    200,
                    headers={'content-type': 'application/json'},
                    body=json.dumps(echo_data, ensure_ascii=False, indent=2)
                )
            
            elif path == '/api/clients' and method == 'GET':
                # 客户端信息
                clients_data = {
                    'active_clients': len(self.clients),
                    'client_list': [{'ip': addr[0], 'port': addr[1]} for addr in self.clients],
                    'total_requests': self.request_count
                }
                
                return HTTPResponse(
                    200,
                    headers={'content-type': 'application/json'},
                    body=json.dumps(clients_data, ensure_ascii=False, indent=2)
                )
            
            else:
                # API接口不存在
                error_data = {
                    'error': 'API Not Found',
                    'message': f'API接口 {path} 不存在',
                    'available_apis': [
                        'GET /api/status',
                        'GET /api/time',
                        'POST /api/echo',
                        'GET /api/clients'
                    ]
                }
                
                return HTTPResponse(
                    404,
                    headers={'content-type': 'application/json'},
                    body=json.dumps(error_data, ensure_ascii=False, indent=2)
                )
        
        except Exception as e:
            self.logger.log_error("API_ERROR", str(e), path)
            error_data = {
                'error': 'Internal Server Error',
                'message': str(e)
            }
            
            return HTTPResponse(
                500,
                headers={'content-type': 'application/json'},
                body=json.dumps(error_data, ensure_ascii=False, indent=2)
            )
    
    def handle_static_file(self, request):
        """处理静态文件请求"""
        path = request.path
        
        # 处理根路径
        if path == '/' or path == '':
            path = '/index.html'
        
        # 安全检查：防止目录遍历攻击
        if '..' in path or path.startswith('/..'):
            return HTTPResponse(400, body="<h1>400 Bad Request</h1><p>Invalid path</p>")
        
        # 构造文件路径
        file_path = os.path.join(self.document_root, path.lstrip('/'))
        
        try:
            if os.path.exists(file_path) and os.path.isfile(file_path):
                # 获取MIME类型
                mime_type, _ = mimetypes.guess_type(file_path)
                if not mime_type:
                    mime_type = 'text/plain'
                
                # 读取文件
                if mime_type.startswith('text/') or mime_type == 'application/json':
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    return HTTPResponse(
                        200,
                        headers={'content-type': f'{mime_type}; charset=utf-8'},
                        body=content
                    )
                else:
                    # 二进制文件
                    with open(file_path, 'rb') as f:
                        content = f.read()
                    
                    return HTTPResponse(
                        200,
                        headers={'content-type': mime_type},
                        binary_body=content
                    )
            
            else:
                # 文件不存在
                not_found_html = f"""
                <html>
                <head><title>404 Not Found</title></head>
                <body>
                    <h1>404 - 页面未找到</h1>
                    <p>请求的页面 <code>{path}</code> 不存在。</p>
                    <p><a href="/">返回首页</a></p>
                </body>
                </html>
                """
                
                return HTTPResponse(404, body=not_found_html)
        
        except Exception as e:
            self.logger.log_error("STATIC_FILE_ERROR", str(e), path)
            return HTTPResponse(500, body="<h1>500 Internal Server Error</h1>")
    
    def stop(self):
        """停止HTTP服务器"""
        print("\n正在关闭HTTP服务器...")
        
        self.running = False
        
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        # 生成最终报告
        if self.start_time:
            uptime = time.time() - self.start_time
            print(f"服务器运行时间: {uptime:.2f} 秒")
            print(f"总处理请求: {self.request_count} 个")
            
            # 记录关闭日志
            self.logger.info(f"HTTP服务器关闭 - 运行时间: {uptime:.2f}秒, 总请求: {self.request_count}")
            
            # 生成会话总结
            session_summary = self.logger.generate_session_summary()
        
        print("HTTP服务器已关闭")

def main():
    """主函数"""
    # 添加命令行参数解析
    parser = argparse.ArgumentParser(description='Socket HTTP 服务器')
    parser.add_argument('--host', default='localhost', help='服务器IP地址 (默认: localhost)')
    parser.add_argument('--port', type=int, default=8080, help='服务器端口号 (默认: 8080)')
    parser.add_argument('--document-root', default='./www', help='文档根目录 (默认: ./www)')
    parser.add_argument('--auto', action='store_true', help='自动模式，不需要用户输入')
    
    args = parser.parse_args()
    
    print("Socket HTTP 服务器")
    print("基于原生Socket实现的HTTP/1.1服务器")
    print("=" * 50)
    
    try:
        if args.auto:
            # 自动模式，使用命令行参数或默认值
            host = args.host
            port = args.port
            document_root = args.document_root
            print(f"自动启动模式: {host}:{port}, 文档根目录: {document_root}")
        else:
            # 交互模式
            host = input("请输入服务器IP地址 (默认: localhost): ").strip()
            if not host:
                host = args.host
            
            port_input = input("请输入服务器端口号 (默认: 8080): ").strip()
            port = int(port_input) if port_input else args.port
            
            document_root = input("请输入文档根目录 (默认: ./www): ").strip()
            if not document_root:
                document_root = args.document_root
        
        # 创建并启动HTTP服务器
        server = HTTPServer(host, port, document_root)
        
        print(f"\n启动HTTP服务器...")
        print(f"浏览器访问: http://{host}:{port}")
        print("按 Ctrl+C 停止服务器")
        
        server.start()
        
    except KeyboardInterrupt:
        print("\n收到停止信号")
    except ValueError:
        print("端口号必须是数字")
    except Exception as e:
        print(f"服务器启动失败: {e}")

if __name__ == "__main__":
    main()
