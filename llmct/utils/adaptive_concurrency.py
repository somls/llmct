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
        self.error_types = deque(maxlen=window_size)  # 错误类型记录
        
        # 错误统计
        self.consecutive_429 = 0
        self.consecutive_success = 0
        self.total_429_count = 0
        self.last_429_time = 0
        
        # 调整历史
        self.adjustment_history = deque(maxlen=10)
        
        self.lock = threading.Lock()
        self._last_adjust_time = time.time()
        self._adjust_interval = 3  # 缩短到3秒调整一次
        self._aggressive_mode = False  # 激进模式（429后启用）
    
    def record_result(
        self, 
        success: bool, 
        latency: float, 
        is_rate_limit: bool = False,
        error_type: str = ''
    ):
        """
        记录测试结果
        
        Args:
            success: 是否成功
            latency: 响应延迟（秒）
            is_rate_limit: 是否是429错误
            error_type: 错误类型
        """
        with self.lock:
            self.success_window.append(1 if success else 0)
            if success and latency > 0:
                self.latency_window.append(latency)
            
            # 记录错误类型
            self.error_types.append(error_type if not success else '')
            
            if is_rate_limit:
                self.consecutive_429 += 1
                self.consecutive_success = 0
                self.total_429_count += 1
                self.last_429_time = time.time()
                self._aggressive_mode = True
                # 立即降低并发，不等待
                self._handle_rate_limit()
            elif success:
                self.consecutive_success += 1
                self.consecutive_429 = 0
            else:
                self.consecutive_success = 0
                self.consecutive_429 = 0
            
            # 检查是否需要调整
            self._try_adjust()
    
    def _handle_rate_limit(self):
        """处理429限流错误 - 立即响应"""
        old = self.current
        # 激进降低50%
        self.current = max(int(self.current * 0.5), self.min_c)
        self._log_adjustment(old, self.current, 'rate_limit', immediate=True)
    
    def _try_adjust(self):
        """尝试调整并发数"""
        now = time.time()
        
        # 激进模式下缩短调整间隔
        adjust_interval = self._adjust_interval if not self._aggressive_mode else 1.5
        
        # 检查调整间隔
        if now - self._last_adjust_time < adjust_interval:
            return
        
        # 检查是否有足够的数据
        min_samples = self.window_size // 3 if self._aggressive_mode else self.window_size // 2
        if len(self.success_window) < min_samples:
            return
        
        # 计算统计指标
        success_rate = sum(self.success_window) / len(self.success_window)
        avg_latency = (
            sum(self.latency_window) / len(self.latency_window)
            if self.latency_window else 0
        )
        
        # 计算近期429错误率
        recent_429_rate = sum(1 for e in self.error_types if '429' in str(e)) / len(self.error_types) if self.error_types else 0
        
        old_concurrency = self.current
        reason = ''
        
        # 策略 1: 近期仍有429错误，继续降低
        if recent_429_rate > 0.05:  # 5%以上是429
            self.current = max(int(self.current * 0.7), self.min_c)
            reason = 'high_429_rate'
        
        # 策略 2: 成功率极低，大幅降低
        elif success_rate < 0.6:
            self.current = max(int(self.current * 0.6), self.min_c)
            reason = 'very_low_success'
        
        # 策略 3: 成功率低或延迟高，中幅降低
        elif success_rate < 0.8 or avg_latency > 5.0:
            self.current = max(int(self.current * 0.8), self.min_c)
            reason = 'low_success_or_high_latency'
        
        # 策略 4: 性能良好，小幅提高
        elif success_rate > 0.9 and avg_latency < 3.0:
            if self._aggressive_mode:
                # 激进模式下谨慎提升
                if self.consecutive_success >= 30:
                    self.current = min(self.current + 1, self.max_c)
                    reason = 'gradual_recovery'
            else:
                # 正常模式下积极提升
                if self.consecutive_success >= 15:
                    self.current = min(self.current + 3, self.max_c)
                    reason = 'good_performance'
        
        # 策略 5: 极佳性能，大幅提高
        elif success_rate > 0.95 and avg_latency < 2.0 and self.consecutive_success >= 25:
            increase = int(self.current * 0.3) if not self._aggressive_mode else int(self.current * 0.2)
            self.current = min(self.current + increase, self.max_c)
            reason = 'excellent_performance'
        
        # 检查是否可以退出激进模式
        if self._aggressive_mode and recent_429_rate == 0 and success_rate > 0.9:
            if now - self.last_429_time > 60:  # 60秒没有429错误
                self._aggressive_mode = False
                reason += '_exit_aggressive'
        
        self._last_adjust_time = now
        
        # 记录调整
        if old_concurrency != self.current:
            self._log_adjustment(old_concurrency, self.current, reason)
    
    def _log_adjustment(self, old_val: int, new_val: int, reason: str, immediate: bool = False):
        """记录调整历史"""
        adjustment = {
            'time': time.time(),
            'old': old_val,
            'new': new_val,
            'reason': reason,
            'immediate': immediate
        }
        self.adjustment_history.append(adjustment)
        
        from llmct.utils.logger import get_logger
        logger = get_logger()
        
        prefix = '[IMMEDIATE]' if immediate else ''
        success_rate = sum(self.success_window) / len(self.success_window) if self.success_window else 0
        avg_latency = sum(self.latency_window) / len(self.latency_window) if self.latency_window else 0
        
        logger.info(
            f"{prefix}并发数调整: {old_val} -> {new_val} | "
            f"原因: {reason} | 成功率: {success_rate:.1%} | 延迟: {avg_latency:.2f}s"
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
            
            recent_429_rate = (
                sum(1 for e in self.error_types if '429' in str(e)) / len(self.error_types)
                if self.error_types else 0
            )
            
            return {
                'current_concurrency': self.current,
                'success_rate': round(success_rate * 100, 2),
                'avg_latency': round(avg_latency, 3),
                'consecutive_429': self.consecutive_429,
                'consecutive_success': self.consecutive_success,
                'total_429_count': self.total_429_count,
                'recent_429_rate': round(recent_429_rate * 100, 2),
                'window_size': len(self.success_window),
                'aggressive_mode': self._aggressive_mode,
                'adjustments_count': len(self.adjustment_history)
            }
    
    def get_adjustment_history(self) -> list:
        """获取调整历史"""
        with self.lock:
            return list(self.adjustment_history)
    
    def reset(self):
        """重置控制器"""
        with self.lock:
            self.success_window.clear()
            self.latency_window.clear()
            self.error_types.clear()
            self.consecutive_429 = 0
            self.consecutive_success = 0
            self.total_429_count = 0
            self.last_429_time = 0
            self._aggressive_mode = False
            self.adjustment_history.clear()
            self._last_adjust_time = time.time()
