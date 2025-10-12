"""自适应并发控制 - 动态调整并发数"""

import threading
import time
from collections import deque
from typing import Optional


class AdaptiveConcurrencyController:
    """
    自适应并发控制器
    
    根据成功率和延迟自动调整并发数:
    - 成功率高 + 延迟低 -> 增加并发
    - 成功率低 或 延迟高 -> 减少并发
    """
    
    def __init__(
        self, 
        initial_concurrency: int = 10, 
        min_concurrency: int = 3, 
        max_concurrency: int = 50,
        window_size: int = 20
    ):
        """
        Args:
            initial_concurrency: 初始并发数
            min_concurrency: 最小并发数
            max_concurrency: 最大并发数
            window_size: 滑动窗口大小（用于统计）
        """
        self.current = initial_concurrency
        self.min_c = min_concurrency
        self.max_c = max_concurrency
        self.window_size = window_size
        
        # 滑动窗口统计
        self.success_window = deque(maxlen=window_size)
        self.latency_window = deque(maxlen=window_size)
        
        # 429错误统计
        self.consecutive_429 = 0
        self.consecutive_success = 0
        
        self.lock = threading.Lock()
        self._last_adjust_time = time.time()
        self._adjust_interval = 5  # 至少5秒调整一次
    
    def record_result(
        self, 
        success: bool, 
        latency: float, 
        is_rate_limit: bool = False
    ):
        """
        记录测试结果
        
        Args:
            success: 是否成功
            latency: 响应延迟（秒）
            is_rate_limit: 是否是429错误
        """
        with self.lock:
            self.success_window.append(1 if success else 0)
            if success and latency > 0:
                self.latency_window.append(latency)
            
            if is_rate_limit:
                self.consecutive_429 += 1
                self.consecutive_success = 0
            elif success:
                self.consecutive_success += 1
                self.consecutive_429 = 0
            else:
                self.consecutive_success = 0
            
            # 检查是否需要调整
            self._try_adjust()
    
    def _try_adjust(self):
        """尝试调整并发数"""
        now = time.time()
        
        # 检查调整间隔
        if now - self._last_adjust_time < self._adjust_interval:
            return
        
        # 检查是否有足够的数据
        if len(self.success_window) < self.window_size // 2:
            return
        
        # 计算统计指标
        success_rate = sum(self.success_window) / len(self.success_window)
        avg_latency = (
            sum(self.latency_window) / len(self.latency_window)
            if self.latency_window else 0
        )
        
        old_concurrency = self.current
        
        # 遭遇429错误，立即降低
        if self.consecutive_429 >= 3:
            self.current = max(int(self.current * 0.5), self.min_c)
            self.consecutive_429 = 0
        
        # 连续成功，尝试提高
        elif self.consecutive_success >= 20 and success_rate > 0.95 and avg_latency < 2.0:
            self.current = min(int(self.current * 1.3), self.max_c)
            self.consecutive_success = 0
        
        # 成功率低或延迟高，降低并发
        elif success_rate < 0.8 or avg_latency > 5.0:
            self.current = max(int(self.current * 0.8), self.min_c)
        
        # 性能良好，逐步提高
        elif success_rate > 0.9 and avg_latency < 3.0 and self.current < self.max_c:
            self.current = min(self.current + 2, self.max_c)
        
        self._last_adjust_time = now
        
        # 记录调整
        if old_concurrency != self.current:
            from llmct.utils.logger import get_logger
            logger = get_logger()
            logger.info(
                f"并发数调整: {old_concurrency} -> {self.current} "
                f"(成功率={success_rate:.2%}, 延迟={avg_latency:.2f}s)"
            )
    
    def get_current_concurrency(self) -> int:
        """获取当前并发数"""
        return self.current
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        with self.lock:
            success_rate = (
                sum(self.success_window) / len(self.success_window)
                if self.success_window else 0
            )
            avg_latency = (
                sum(self.latency_window) / len(self.latency_window)
                if self.latency_window else 0
            )
            
            return {
                'current_concurrency': self.current,
                'success_rate': round(success_rate * 100, 2),
                'avg_latency': round(avg_latency, 3),
                'consecutive_429': self.consecutive_429,
                'consecutive_success': self.consecutive_success,
                'window_size': len(self.success_window)
            }
    
    def reset(self):
        """重置控制器"""
        with self.lock:
            self.success_window.clear()
            self.latency_window.clear()
            self.consecutive_429 = 0
            self.consecutive_success = 0
            self._last_adjust_time = time.time()
