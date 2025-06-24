#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级日志管理器 - Advanced Logger
按实验日期自动创建文件夹，记录详细的网络状态信息
"""

import os
import logging
import time
from datetime import datetime
from pathlib import Path
import json

class AdvancedLogger:
    def __init__(self, experiment_name="socket_experiment"):
        """
        初始化高级日志管理器
        :param experiment_name: 实验名称
        """
        self.experiment_name = experiment_name
        self.base_log_dir = Path("logs")
        self.session_start_time = datetime.now()
        
        # 创建当前实验会话的日志目录
        self.current_session_dir = self._create_session_directory()
        
        # 初始化各种日志记录器
        self.setup_loggers()
        
        # TCP状态跟踪
        self.tcp_states = []
        self.connection_stats = {}
        
    def _create_session_directory(self):
        """创建当前实验会话的日志目录"""
        date_str = self.session_start_time.strftime("%Y-%m-%d")
        time_str = self.session_start_time.strftime("%H-%M-%S")
        
        session_dir = self.base_log_dir / date_str / f"{self.experiment_name}_{time_str}"
        session_dir.mkdir(parents=True, exist_ok=True)
        
        return session_dir
    
    def setup_loggers(self):
        """设置各种专用日志记录器"""
        
        # 主要日志记录器
        self.main_logger = self._create_logger(
            "main", 
            self.current_session_dir / "main.log",
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        
        # TCP状态日志记录器
        self.tcp_logger = self._create_logger(
            "tcp_states",
            self.current_session_dir / "tcp_states.log",
            "%(asctime)s - TCP - %(message)s"
        )
        
        # 网络性能日志记录器
        self.perf_logger = self._create_logger(
            "performance",
            self.current_session_dir / "performance.log",
            "%(asctime)s - PERF - %(message)s"
        )
        
        # 错误日志记录器
        self.error_logger = self._create_logger(
            "errors",
            self.current_session_dir / "errors.log",
            "%(asctime)s - ERROR - %(message)s"
        )
        
        # 连接详情日志记录器
        self.conn_logger = self._create_logger(
            "connections",
            self.current_session_dir / "connections.log",
            "%(asctime)s - CONN - %(message)s"
        )
    
    def _create_logger(self, name, log_file, format_str):
        """创建特定的日志记录器"""
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        
        # 清除已有的处理器
        logger.handlers.clear()
        
        # 文件处理器
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter(format_str)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(f"[{name.upper()}] %(message)s")
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        return logger
    
    def log_tcp_state_change(self, connection_id, old_state, new_state, details=""):
        """记录TCP状态变化"""
        timestamp = datetime.now()
        state_info = {
            "timestamp": timestamp.isoformat(),
            "connection_id": connection_id,
            "old_state": old_state,
            "new_state": new_state,
            "details": details
        }
        
        self.tcp_states.append(state_info)
        
        message = f"Connection[{connection_id}] {old_state} -> {new_state}"
        if details:
            message += f" ({details})"
        
        self.tcp_logger.info(message)
    
    def log_connection_event(self, event_type, connection_info):
        """记录连接事件"""
        timestamp = datetime.now().isoformat()
        
        message = f"{event_type}: {json.dumps(connection_info, ensure_ascii=False)}"
        self.conn_logger.info(message)
        
        # 更新连接统计
        conn_id = connection_info.get('connection_id', 'unknown')
        if conn_id not in self.connection_stats:
            self.connection_stats[conn_id] = {
                'start_time': timestamp,
                'events': [],
                'bytes_sent': 0,
                'bytes_received': 0
            }
        
        self.connection_stats[conn_id]['events'].append({
            'timestamp': timestamp,
            'event': event_type,
            'details': connection_info
        })
    
    def log_performance_metric(self, metric_name, value, unit="", details=""):
        """记录性能指标"""
        message = f"{metric_name}: {value}"
        if unit:
            message += f" {unit}"
        if details:
            message += f" - {details}"
        
        self.perf_logger.info(message)
    
    def log_error(self, error_type, error_message, context=""):
        """记录错误信息"""
        message = f"{error_type}: {error_message}"
        if context:
            message += f" [Context: {context}]"
        
        self.error_logger.error(message)
    
    def log_handshake_analysis(self, connection_id, handshake_type, step, timestamp, details):
        """记录握手过程分析"""
        message = f"Connection[{connection_id}] {handshake_type} Step{step}: {details}"
        self.tcp_logger.info(message)
        
        # 保存到专门的握手分析文件
        handshake_file = self.current_session_dir / f"handshake_analysis_{connection_id}.json"
        
        handshake_data = {
            "connection_id": connection_id,
            "type": handshake_type,
            "step": step,
            "timestamp": timestamp,
            "details": details
        }
        
        # 追加到文件
        if handshake_file.exists():
            with open(handshake_file, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        else:
            existing_data = []
        
        existing_data.append(handshake_data)
        
        with open(handshake_file, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=2)
    
    def generate_session_summary(self):
        """生成本次实验会话的总结报告"""
        summary = {
            "experiment_name": self.experiment_name,
            "session_start": self.session_start_time.isoformat(),
            "session_end": datetime.now().isoformat(),
            "total_connections": len(self.connection_stats),
            "tcp_state_changes": len(self.tcp_states),
            "connection_stats": self.connection_stats,
            "tcp_state_history": self.tcp_states
        }
        
        summary_file = self.current_session_dir / "session_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        self.main_logger.info(f"实验会话总结已保存: {summary_file}")
        return summary
    
    def get_session_directory(self):
        """获取当前会话的日志目录"""
        return str(self.current_session_dir)
    
    def info(self, message):
        """记录普通信息"""
        self.main_logger.info(message)
    
    def warning(self, message):
        """记录警告信息"""
        self.main_logger.warning(message)
    
    def error(self, message):
        """记录错误信息"""
        self.main_logger.error(message)

# 全局日志管理器实例
_global_logger = None

def get_advanced_logger(experiment_name="socket_experiment"):
    """获取全局高级日志管理器实例"""
    global _global_logger
    if _global_logger is None:
        _global_logger = AdvancedLogger(experiment_name)
    return _global_logger

def create_new_session(experiment_name="socket_experiment"):
    """创建新的实验会话"""
    global _global_logger
    _global_logger = AdvancedLogger(experiment_name)
    return _global_logger
