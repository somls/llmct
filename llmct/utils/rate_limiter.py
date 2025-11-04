"""智能速率限制器"""

import time
import threading
from collections import deque
from typing import Callable


class RateLimiter:
    """速率限制器 - 控制API调用频率"""
    
    def __init__(self, max_calls: int, period: float = 60.0):
        """
        Args:
            max_calls: 时间窗口内最大调用次数
            period: 时间窗口（秒）
        
        Example:
            # 限制每分钟最多60次调用
            limiter = RateLimiter(max_calls=60, period=60.0)
        """
        self.max_calls = max_calls
        self.period = period
        self.calls = deque()
        self.lock = threading.Lock()
    
    def __call__(self, func: Callable) -> Callable:
        """装饰器模式"""
        def wrapper(*args, **kwargs):
            self.wait_if_needed()
            return func(*args, **kwargs)
        return wrapper
    
    def wait_if_needed(self):
        """如果需要，等待直到可以继续"""
        with self.lock:
            now = time.time()
            
            # 清理过期的调用记录
            while self.calls and self.calls[0] <= now - self.period:
                self.calls.popleft()
            
            # 如果达到限制，等待
            if len(self.calls) >= self.max_calls:
                sleep_time = self.period - (now - self.calls[0])
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    # 清理过期记录
                    now = time.time()
                    while self.calls and self.calls[0] <= now - self.period:
                        self.calls.popleft()
            
            # 记录本次调用
            self.calls.append(time.time())
    
    def get_remaining_calls(self) -> int:
        """获取剩余可用调用次数"""
        with self.lock:
            now = time.time()
            
            # 清理过期记录
            while self.calls and self.calls[0] <= now - self.period:
                self.calls.popleft()
            
            return self.max_calls - len(self.calls)
    
    def get_reset_time(self) -> float:
        """获取限制重置时间（秒）"""
        with self.lock:
            if not self.calls:
                return 0.0
            
            now = time.time()
            oldest_call = self.calls[0]
            reset_time = self.period - (now - oldest_call)
            
            return max(0.0, reset_time)
    
    def reset(self):
        """重置速率限制器"""
        with self.lock:
            self.calls.clear()


class AdaptiveRateLimiter:
    """自适应速率限制器 - 根据响应动态调整（优化版：避免丢失调用历史）"""

    def __init__(self, initial_rpm: int = 60, min_rpm: int = 10, max_rpm: int = 120):
        """
        Args:
            initial_rpm: 初始每分钟请求数
            min_rpm: 最小每分钟请求数
            max_rpm: 最大每分钟请求数
        """
        self.initial_rpm = initial_rpm
        self.min_rpm = min_rpm
        self.max_rpm = max_rpm
        self.current_rpm = initial_rpm
        # 优化：直接管理调用历史，避免创建新实例导致历史丢失
        self.calls = deque()
        self.period = 60.0
        self.consecutive_429 = 0
        self.consecutive_success = 0
        self.lock = threading.Lock()

    def wait_if_needed(self):
        """等待直到可以继续"""
        with self.lock:
            now = time.time()

            # 清理过期的调用记录
            while self.calls and self.calls[0] <= now - self.period:
                self.calls.popleft()

            # 如果达到当前RPM限制，等待
            if len(self.calls) >= self.current_rpm:
                sleep_time = self.period - (now - self.calls[0])
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    # 重新获取时间并清理过期记录
                    now = time.time()
                    while self.calls and self.calls[0] <= now - self.period:
                        self.calls.popleft()

            # 记录本次调用
            self.calls.append(now)

    def report_success(self):
        """报告成功的请求"""
        with self.lock:
            self.consecutive_429 = 0
            self.consecutive_success += 1

            # 连续10次成功，尝试提高速率
            if self.consecutive_success >= 10:
                self._increase_rate()
                self.consecutive_success = 0

    def report_rate_limit(self, retry_after: int = None):
        """
        报告速率限制错误

        Args:
            retry_after: 服务器建议的重试等待时间（秒）
        """
        with self.lock:
            self.consecutive_success = 0
            self.consecutive_429 += 1

            # 立即降低速率
            self._decrease_rate()

            # 如果服务器提供了重试时间，等待
            if retry_after:
                time.sleep(retry_after)

    def _increase_rate(self):
        """提高请求速率（优化：不再创建新实例）"""
        new_rpm = min(int(self.current_rpm * 1.2), self.max_rpm)
        if new_rpm > self.current_rpm:
            self.current_rpm = new_rpm
            # 不再创建新RateLimiter实例，保留调用历史

    def _decrease_rate(self):
        """降低请求速率（优化：不再创建新实例）"""
        new_rpm = max(int(self.current_rpm * 0.7), self.min_rpm)
        if new_rpm < self.current_rpm:
            self.current_rpm = new_rpm
            # 不再创建新RateLimiter实例，保留调用历史

    def get_current_rpm(self) -> int:
        """获取当前RPM"""
        return self.current_rpm

    def get_remaining_calls(self) -> int:
        """获取剩余可用调用次数"""
        with self.lock:
            now = time.time()

            # 清理过期记录
            while self.calls and self.calls[0] <= now - self.period:
                self.calls.popleft()

            return self.current_rpm - len(self.calls)

    def reset(self):
        """重置限制器"""
        with self.lock:
            self.current_rpm = self.initial_rpm
            self.calls.clear()
            self.consecutive_429 = 0
            self.consecutive_success = 0
