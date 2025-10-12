"""日志管理模块"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


class Logger:
    """统一的日志管理器"""
    
    def __init__(self, name="llmct", level=logging.INFO, log_file=None):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logger.handlers.clear()
        
        # 日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 控制台输出 - 仅显示 ERROR 及以上级别，避免打乱测试显示
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.ERROR)  # 控制台只显示错误和严重错误
        self.logger.addHandler(console_handler)
        
        # 文件输出（可选）
        if log_file:
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def debug(self, msg, **kwargs):
        self.logger.debug(msg, extra=kwargs)
    
    def info(self, msg, **kwargs):
        self.logger.info(msg, extra=kwargs)
    
    def warning(self, msg, **kwargs):
        self.logger.warning(msg, extra=kwargs)
    
    def error(self, msg, **kwargs):
        self.logger.error(msg, extra=kwargs)
    
    def critical(self, msg, **kwargs):
        self.logger.critical(msg, extra=kwargs)


# 全局日志实例
_logger = None


def get_logger(name="llmct", level=logging.INFO, log_file=None):
    """获取日志实例"""
    global _logger
    if _logger is None:
        _logger = Logger(name, level, log_file)
    return _logger
