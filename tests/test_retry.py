"""测试重试机制"""

import pytest
import time
from llmct.utils.retry import retry_on_exception, RetryStrategy


def test_retry_success_first_attempt():
    """测试第一次尝试就成功"""
    call_count = {'count': 0}
    
    @retry_on_exception(max_attempts=3)
    def successful_func():
        call_count['count'] += 1
        return "success"
    
    result = successful_func()
    
    assert result == "success"
    assert call_count['count'] == 1


def test_retry_success_after_failures():
    """测试重试后成功"""
    call_count = {'count': 0}
    
    @retry_on_exception(
        exceptions=(ValueError,),
        max_attempts=3,
        delay=0.1,
        backoff=1
    )
    def eventually_successful_func():
        call_count['count'] += 1
        if call_count['count'] < 3:
            raise ValueError("Not yet")
        return "success"
    
    result = eventually_successful_func()
    
    assert result == "success"
    assert call_count['count'] == 3


def test_retry_max_attempts_exceeded():
    """测试超过最大重试次数"""
    call_count = {'count': 0}
    
    @retry_on_exception(
        exceptions=(ValueError,),
        max_attempts=3,
        delay=0.1,
        backoff=1
    )
    def always_failing_func():
        call_count['count'] += 1
        raise ValueError("Always fails")
    
    with pytest.raises(ValueError):
        always_failing_func()
    
    assert call_count['count'] == 3


def test_retry_with_backoff():
    """测试退避策略"""
    timestamps = []
    
    @retry_on_exception(
        exceptions=(ValueError,),
        max_attempts=3,
        delay=0.1,
        backoff=2.0
    )
    def func_with_backoff():
        timestamps.append(time.time())
        raise ValueError("Retry")
    
    try:
        func_with_backoff()
    except ValueError:
        pass
    
    # 验证重试间隔递增
    assert len(timestamps) == 3
    
    # 第一次和第二次之间的间隔应该约为0.1秒
    assert timestamps[1] - timestamps[0] >= 0.1
    
    # 第二次和第三次之间的间隔应该约为0.2秒
    assert timestamps[2] - timestamps[1] >= 0.2


def test_retry_strategy_class():
    """测试重试策略类"""
    call_count = {'count': 0}
    
    def func_to_retry():
        call_count['count'] += 1
        if call_count['count'] < 3:
            raise ValueError("Not yet")
        return "success"
    
    strategy = RetryStrategy(max_attempts=3, delay=0.1, backoff=1)
    result = strategy.execute(func_to_retry)
    
    assert result == "success"
    assert call_count['count'] == 3


def test_retry_strategy_failure():
    """测试重试策略失败"""
    def always_fails():
        raise ValueError("Always fails")
    
    strategy = RetryStrategy(max_attempts=2, delay=0.1, backoff=1)
    
    with pytest.raises(ValueError):
        strategy.execute(always_fails)


def test_retry_with_specific_exceptions():
    """测试只重试特定异常"""
    call_count = {'count': 0}
    
    @retry_on_exception(
        exceptions=(ValueError,),
        max_attempts=3,
        delay=0.1
    )
    def func_with_different_exceptions():
        call_count['count'] += 1
        if call_count['count'] == 1:
            raise ValueError("Retry this")
        raise TypeError("Don't retry this")
    
    with pytest.raises(TypeError):
        func_with_different_exceptions()
    
    # ValueError会被重试，但遇到TypeError就立即抛出
    assert call_count['count'] == 2
