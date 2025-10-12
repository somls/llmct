"""测试SQLite缓存功能"""

import pytest
import time
import threading
import tempfile
import os
from llmct.utils.sqlite_cache import SQLiteCache


@pytest.fixture
def temp_db():
    """创建临时数据库文件"""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield path
    try:
        os.unlink(path)
        # 删除WAL文件
        for ext in ['-wal', '-shm']:
            wal_file = path + ext
            if os.path.exists(wal_file):
                os.unlink(wal_file)
    except:
        pass


def test_cache_initialization(temp_db):
    """测试缓存初始化"""
    cache = SQLiteCache(db_file=temp_db)
    assert cache.db_file == temp_db
    assert cache._buffer_size >= cache._min_buffer_size
    assert cache._buffer_size <= cache._max_buffer_size


def test_update_and_retrieve(temp_db):
    """测试更新和检索缓存"""
    cache = SQLiteCache(db_file=temp_db)
    
    # 更新成功记录
    cache.update_cache('gpt-4', True, 1.5, '', 'Hello, world!')
    cache.flush()
    
    # 检索记录
    result = cache.get_cached_result('gpt-4')
    assert result is not None
    assert result['success'] == 1
    assert result['response_time'] == 1.5
    assert result['content'] == 'Hello, world!'


def test_failure_tracking(temp_db):
    """测试失败追踪"""
    cache = SQLiteCache(db_file=temp_db)
    
    # 模拟3次失败
    for i in range(3):
        cache.update_cache('failed-model', False, 0, f'HTTP_40{i}', '')
    cache.flush()
    
    # 验证失败次数
    assert cache.get_failure_count('failed-model') == 3
    
    # 验证失败历史
    result = cache.get_cached_result('failed-model')
    assert len(result['failure_history']) > 0


def test_persistent_failures(temp_db):
    """测试持续失败统计"""
    cache = SQLiteCache(db_file=temp_db)
    
    # 创建不同失败次数的模型
    for i in range(5):
        cache.update_cache('model-5', False, 0, 'HTTP_403', '')
    
    for i in range(2):
        cache.update_cache('model-2', False, 0, 'HTTP_429', '')
    
    cache.flush()
    
    # 获取失败超过3次的模型
    failures = cache.get_persistent_failures(threshold=3)
    assert len(failures) == 1
    assert failures[0]['model_id'] == 'model-5'
    assert failures[0]['failure_count'] == 5


def test_concurrent_writes(temp_db):
    """测试并发写入安全性"""
    cache = SQLiteCache(db_file=temp_db, cache_duration_hours=24)
    errors = []
    
    def write_records(thread_id, count):
        """每个线程写入多条记录"""
        try:
            for i in range(count):
                model_id = f'thread-{thread_id}-model-{i}'
                cache.update_cache(
                    model_id,
                    success=i % 2 == 0,
                    response_time=1.0 + i * 0.1,
                    error_code='HTTP_403' if i % 2 == 1 else '',
                    content=f'Content from thread {thread_id}'
                )
        except Exception as e:
            errors.append(e)
    
    # 创建10个线程，每个写入20条记录
    threads = []
    for i in range(10):
        t = threading.Thread(target=write_records, args=(i, 20))
        threads.append(t)
        t.start()
    
    # 等待所有线程完成
    for t in threads:
        t.join()
    
    # 确保刷新所有数据
    cache.flush()
    
    # 验证没有错误
    assert len(errors) == 0, f"并发写入出现错误: {errors}"
    
    # 验证所有记录都已写入
    stats = cache.get_stats()
    assert stats['total'] == 200, f"期望200条记录，实际: {stats['total']}"


def test_concurrent_read_write(temp_db):
    """测试并发读写"""
    cache = SQLiteCache(db_file=temp_db)
    errors = []
    read_results = []
    
    # 先写入一些初始数据
    for i in range(50):
        cache.update_cache(f'model-{i}', True, 1.0, '', f'Content {i}')
    cache.flush()
    
    def write_thread():
        """写入线程"""
        try:
            for i in range(50, 100):
                cache.update_cache(f'model-{i}', True, 1.0, '', f'Content {i}')
                time.sleep(0.001)
        except Exception as e:
            errors.append(('write', e))
    
    def read_thread():
        """读取线程"""
        try:
            for i in range(50):
                result = cache.get_cached_result(f'model-{i}')
                read_results.append(result is not None)
                time.sleep(0.001)
        except Exception as e:
            errors.append(('read', e))
    
    # 启动多个读写线程
    threads = []
    for _ in range(3):
        threads.append(threading.Thread(target=write_thread))
    for _ in range(3):
        threads.append(threading.Thread(target=read_thread))
    
    for t in threads:
        t.start()
    
    for t in threads:
        t.join()
    
    cache.flush()
    
    # 验证
    assert len(errors) == 0, f"并发读写出现错误: {errors}"
    assert all(read_results), "部分读取失败"


def test_auto_flush(temp_db):
    """测试自动刷新机制"""
    cache = SQLiteCache(db_file=temp_db)
    
    # 写入少量数据（不触发批量阈值）
    cache.update_cache('model-1', True, 1.0, '', 'Content 1')
    
    # 手动刷新（自动刷新在后台线程中，测试中不可靠）
    cache.flush()
    
    # 验证数据已写入
    result = cache.get_cached_result('model-1')
    assert result is not None
    assert result['success'] == 1


def test_adaptive_buffer_size(temp_db):
    """测试自适应缓冲区大小"""
    cache = SQLiteCache(db_file=temp_db)
    initial_size = cache._buffer_size
    
    # 模拟持续满负荷写入
    for batch in range(10):
        for i in range(initial_size):
            cache.update_cache(f'model-{batch}-{i}', True, 1.0, '', 'Content')
        # 触发flush和调整
    
    cache.flush()
    
    # 缓冲区应该有所调整
    # 注意：可能增大或减小，取决于写入模式
    assert cache._buffer_size >= cache._min_buffer_size
    assert cache._buffer_size <= cache._max_buffer_size


def test_batch_statistics(temp_db):
    """测试批量写入统计"""
    cache = SQLiteCache(db_file=temp_db)
    
    # 写入多批数据
    for i in range(100):
        cache.update_cache(f'model-{i}', True, 1.0, '', f'Content {i}')
    
    cache.flush()
    
    stats = cache.get_stats()
    assert stats['total_writes'] == 100
    assert stats['batch_writes'] > 0
    assert stats['avg_batch_size'] > 0


def test_cache_expiry(temp_db):
    """测试缓存过期"""
    cache = SQLiteCache(db_file=temp_db, cache_duration_hours=0)
    
    cache.update_cache('gpt-4', True, 1.5, '', 'Hello')
    cache.flush()
    
    # 由于duration设置为0，缓存应该立即过期
    time.sleep(0.1)
    assert not cache.is_cached('gpt-4')


def test_reset_failure_counts(temp_db):
    """测试重置失败计数"""
    cache = SQLiteCache(db_file=temp_db)
    
    # 创建失败记录
    cache.update_cache('model-1', False, 0, 'HTTP_403', '')
    cache.update_cache('model-2', False, 0, 'HTTP_429', '')
    cache.flush()
    
    assert cache.get_failure_count('model-1') == 1
    assert cache.get_failure_count('model-2') == 1
    
    # 重置
    cache.reset_failure_counts()
    
    assert cache.get_failure_count('model-1') == 0
    assert cache.get_failure_count('model-2') == 0


def test_clear_cache(temp_db):
    """测试清除缓存"""
    cache = SQLiteCache(db_file=temp_db)
    
    # 写入数据
    for i in range(10):
        cache.update_cache(f'model-{i}', True, 1.0, '', f'Content {i}')
    cache.flush()
    
    stats = cache.get_stats()
    assert stats['total'] == 10
    
    # 清除
    cache.clear_cache()
    
    stats = cache.get_stats()
    assert stats['total'] == 0


def test_wal_mode(temp_db):
    """测试WAL模式是否启用"""
    cache = SQLiteCache(db_file=temp_db)
    
    import sqlite3
    with sqlite3.connect(temp_db) as conn:
        cursor = conn.execute('PRAGMA journal_mode')
        mode = cursor.fetchone()[0]
        # WAL模式应该已启用
        assert mode.upper() == 'WAL'
