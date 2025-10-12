"""重试机制"""

import time
import functools
from typing import Callable, Type, Tuple


def retry_on_exception(
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    logger=None
):
    """
    装饰器：异常时重试
    
    Args:
        exceptions: 需要重试的异常类型
        max_attempts: 最大重试次数
        delay: 初始延迟（秒）
        backoff: 延迟倍数
        logger: 日志记录器
    
    Example:
        @retry_on_exception(
            exceptions=(APIConnectionError, RateLimitError),
            max_attempts=3,
            delay=2.0
        )
        def test_model(model_id):
            # 测试逻辑
            pass
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts:
                        if logger:
                            logger.error(f"重试失败，已达最大次数 {max_attempts}: {e}")
                        raise
                    
                    if logger:
                        logger.warning(
                            f"第{attempt}次尝试失败: {e}, "
                            f"{current_delay:.1f}秒后重试"
                        )
                    
                    time.sleep(current_delay)
                    current_delay *= backoff
            
            return None
        
        return wrapper
    return decorator


class RetryStrategy:
    """重试策略类"""
    
    def __init__(self, max_attempts=3, delay=1.0, backoff=2.0):
        self.max_attempts = max_attempts
        self.delay = delay
        self.backoff = backoff
    
    def execute(self, func, *args, **kwargs):
        """执行带重试的函数"""
        current_delay = self.delay
        last_exception = None
        
        for attempt in range(1, self.max_attempts + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.max_attempts:
                    time.sleep(current_delay)
                    current_delay *= self.backoff
        
        if last_exception:
            raise last_exception
