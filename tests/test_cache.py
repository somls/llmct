"""测试缓存功能"""

import pytest
import json
from mct import ResultCache


def test_cache_initialization(temp_cache_file):
    """测试缓存初始化"""
    cache = ResultCache(cache_file=temp_cache_file)
    assert cache.cache == {}
    assert cache.cache_file == temp_cache_file


def test_update_cache_success(temp_cache_file):
    """测试更新成功记录"""
    cache = ResultCache(cache_file=temp_cache_file)
    cache.update_cache('gpt-4', True, 1.5, '', 'Hello, world!')
    
    assert cache.is_cached('gpt-4')
    assert cache.get_failure_count('gpt-4') == 0
    
    result = cache.get_cached_result('gpt-4')
    assert result['success'] is True
    assert result['response_time'] == 1.5
    assert result['content'] == 'Hello, world!'


def test_update_cache_failure(temp_cache_file):
    """测试更新失败记录"""
    cache = ResultCache(cache_file=temp_cache_file)
    cache.update_cache('gpt-4', False, 0, 'HTTP_403', '')
    
    assert not cache.is_cached('gpt-4')
    assert cache.get_failure_count('gpt-4') == 1
    
    result = cache.get_cached_result('gpt-4')
    assert result['success'] is False
    assert result['error_code'] == 'HTTP_403'


def test_multiple_failures(temp_cache_file):
    """测试多次失败记录"""
    cache = ResultCache(cache_file=temp_cache_file)
    
    # 模拟5次失败
    for i in range(5):
        cache.update_cache('test-model', False, 0, f'HTTP_40{i}', '')
    
    assert cache.get_failure_count('test-model') == 5
    
    # 检查失败历史
    result = cache.get_cached_result('test-model')
    assert len(result['failure_history']) == 5


def test_persistent_failures(temp_cache_file):
    """测试持续失败统计"""
    cache = ResultCache(cache_file=temp_cache_file)
    
    # 创建多个失败模型
    cache.update_cache('model-1', False, 0, 'HTTP_403', '')
    cache.update_cache('model-1', False, 0, 'HTTP_403', '')
    cache.update_cache('model-1', False, 0, 'HTTP_403', '')
    cache.update_cache('model-1', False, 0, 'HTTP_403', '')
    
    cache.update_cache('model-2', False, 0, 'HTTP_429', '')
    cache.update_cache('model-2', False, 0, 'HTTP_429', '')
    
    failures = cache.get_persistent_failures(threshold=3)
    
    assert len(failures) == 1
    assert failures[0]['model_id'] == 'model-1'
    assert failures[0]['failure_count'] == 4


def test_reset_failures(temp_cache_file):
    """测试重置失败计数"""
    cache = ResultCache(cache_file=temp_cache_file)
    
    cache.update_cache('model-1', False, 0, 'HTTP_403', '')
    cache.update_cache('model-2', False, 0, 'HTTP_429', '')
    
    assert cache.get_failure_count('model-1') == 1
    assert cache.get_failure_count('model-2') == 1
    
    cache.reset_failure_counts()
    
    assert cache.get_failure_count('model-1') == 0
    assert cache.get_failure_count('model-2') == 0


def test_get_failed_models(temp_cache_file):
    """测试获取失败模型列表"""
    cache = ResultCache(cache_file=temp_cache_file)
    
    cache.update_cache('success-model', True, 1.0, '', 'OK')
    cache.update_cache('failed-model-1', False, 0, 'HTTP_403', '')
    cache.update_cache('failed-model-2', False, 0, 'HTTP_429', '')
    
    failed = cache.get_failed_models()
    
    assert len(failed) == 2
    assert 'failed-model-1' in failed
    assert 'failed-model-2' in failed
    assert 'success-model' not in failed


def test_cache_expiry(temp_cache_file):
    """测试缓存过期"""
    cache = ResultCache(cache_file=temp_cache_file, cache_duration_hours=0)
    
    cache.update_cache('gpt-4', True, 1.5, '', 'Hello')
    
    # 由于duration设置为0，缓存应该立即过期
    import time
    time.sleep(0.1)
    
    assert not cache.is_cached('gpt-4')


def test_save_and_load_cache(temp_cache_file):
    """测试缓存保存和加载"""
    cache1 = ResultCache(cache_file=temp_cache_file)
    cache1.update_cache('gpt-4', True, 1.5, '', 'Hello')
    cache1.save_cache()
    
    # 创建新实例，应该能加载之前的缓存
    cache2 = ResultCache(cache_file=temp_cache_file)
    assert cache2.is_cached('gpt-4')
    assert cache2.get_failure_count('gpt-4') == 0
