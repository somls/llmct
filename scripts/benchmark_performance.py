#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能基准测试脚本
比较优化前后的性能差异
"""

import time
import sys
import tempfile
import os
from statistics import mean, median, stdev

# 设置Windows控制台输出编码
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


def benchmark_sqlite_cache():
    """基准测试：SQLite缓存性能"""
    print("=" * 80)
    print("基准测试 1: SQLite缓存性能")
    print("=" * 80)
    
    from llmct.utils.sqlite_cache import SQLiteCache
    
    # 创建临时数据库
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    try:
        cache = SQLiteCache(db_file=db_path)
        
        # 测试 1: 批量写入性能
        print("\n[测试 1] 批量写入 1000 条记录")
        write_times = []
        
        for batch in range(10):
            start = time.time()
            for i in range(100):
                model_id = f'batch-{batch}-model-{i}'
                cache.update_cache(
                    model_id,
                    success=i % 2 == 0,
                    response_time=1.0 + i * 0.01,
                    error_code='HTTP_403' if i % 2 == 1 else '',
                    content=f'Content for {model_id}'
                )
            elapsed = time.time() - start
            write_times.append(elapsed)
        
        cache.flush()
        
        print(f"  平均写入时间: {mean(write_times)*1000:.2f}ms / 100条")
        print(f"  中位数: {median(write_times)*1000:.2f}ms")
        print(f"  标准差: {stdev(write_times)*1000:.2f}ms")
        print(f"  总计: {sum(write_times):.3f}s / 1000条")
        
        # 测试 2: 查询性能
        print("\n[测试 2] 查询 1000 条记录")
        query_times = []
        
        for batch in range(10):
            start = time.time()
            for i in range(100):
                model_id = f'batch-{batch}-model-{i}'
                result = cache.get_cached_result(model_id)
            elapsed = time.time() - start
            query_times.append(elapsed)
        
        print(f"  平均查询时间: {mean(query_times)*1000:.2f}ms / 100条")
        print(f"  单次查询: {mean(query_times)*10:.2f}ms")
        print(f"  中位数: {median(query_times)*1000:.2f}ms")
        
        # 测试 3: 统计查询
        print("\n[测试 3] 统计查询性能")
        stats_times = []
        
        for _ in range(100):
            start = time.time()
            stats = cache.get_stats()
            elapsed = time.time() - start
            stats_times.append(elapsed)
        
        print(f"  平均统计查询: {mean(stats_times)*1000:.2f}ms")
        print(f"  统计结果: {stats}")
        
        # 测试 4: 并发写入（多线程）
        print("\n[测试 4] 并发写入性能")
        import threading
        
        def concurrent_write(thread_id, count):
            for i in range(count):
                cache.update_cache(
                    f'thread-{thread_id}-{i}',
                    success=True,
                    response_time=1.0,
                    error_code='',
                    content='Test'
                )
        
        start = time.time()
        threads = []
        for i in range(10):
            t = threading.Thread(target=concurrent_write, args=(i, 50))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        cache.flush()
        elapsed = time.time() - start
        
        print(f"  10个线程并发写入500条: {elapsed:.3f}s")
        print(f"  吞吐量: {500/elapsed:.1f} 条/秒")
        
        print("\n✓ SQLite缓存基准测试完成")
        return True
        
    finally:
        try:
            os.unlink(db_path)
            for ext in ['-wal', '-shm']:
                wal_file = db_path + ext
                if os.path.exists(wal_file):
                    os.unlink(wal_file)
        except:
            pass


def benchmark_adaptive_concurrency():
    """基准测试：自适应并发控制"""
    print("\n" + "=" * 80)
    print("基准测试 2: 自适应并发控制")
    print("=" * 80)
    
    from llmct.utils.adaptive_concurrency import AdaptiveConcurrencyController
    
    controller = AdaptiveConcurrencyController(
        initial_concurrency=10,
        min_concurrency=3,
        max_concurrency=50
    )
    
    # 测试 1: 响应速度
    print("\n[测试 1] 调整响应速度")
    
    # 模拟429错误
    start = time.time()
    controller.record_result(False, 5.0, is_rate_limit=True, error_type='HTTP_429')
    elapsed = time.time() - start
    
    print(f"  429错误响应时间: {elapsed*1000:.2f}ms")
    print(f"  调整后并发数: {controller.get_current_concurrency()}")
    
    # 测试 2: 记录性能
    print("\n[测试 2] 记录性能（10000次）")
    
    controller.reset()
    controller.current = 10
    
    start = time.time()
    for i in range(10000):
        controller.record_result(
            success=i % 10 != 0,  # 90%成功率
            latency=1.0 + (i % 5) * 0.1,
            is_rate_limit=(i % 100 == 0),
            error_type='HTTP_429' if i % 100 == 0 else ''
        )
    elapsed = time.time() - start
    
    print(f"  总时间: {elapsed:.3f}s")
    print(f"  平均每次记录: {elapsed/10000*1000:.3f}ms")
    
    stats = controller.get_stats()
    print(f"  最终统计: {stats}")
    
    # 测试 3: 并发记录
    print("\n[测试 3] 多线程并发记录")
    
    import threading
    controller.reset()
    
    def concurrent_record(count):
        for i in range(count):
            controller.record_result(
                success=True,
                latency=1.0,
                is_rate_limit=False
            )
    
    start = time.time()
    threads = []
    for i in range(10):
        t = threading.Thread(target=concurrent_record, args=(500,))
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    elapsed = time.time() - start
    
    print(f"  10个线程记录5000次: {elapsed:.3f}s")
    print(f"  吞吐量: {5000/elapsed:.1f} 次/秒")
    
    print("\n✓ 自适应并发控制基准测试完成")
    return True


def benchmark_test_execution():
    """基准测试：测试执行速度"""
    print("\n" + "=" * 80)
    print("基准测试 3: 测试执行速度对比")
    print("=" * 80)
    
    # 这个测试需要实际的API，所以只做模拟
    print("\n[模拟] 串行 vs 并行执行")
    
    import asyncio
    
    async def mock_test(delay=0.1):
        """模拟单个测试"""
        await asyncio.sleep(delay)
        return {'success': True}
    
    # 串行执行
    print("\n  串行执行100个测试（每个100ms）:")
    start = time.time()
    
    async def serial_test():
        results = []
        for i in range(100):
            result = await mock_test(0.1)
            results.append(result)
        return results
    
    asyncio.run(serial_test())
    serial_time = time.time() - start
    print(f"    耗时: {serial_time:.2f}s")
    
    # 并行执行（并发10）
    print("\n  并行执行100个测试（并发10）:")
    start = time.time()
    
    async def parallel_test():
        semaphore = asyncio.Semaphore(10)
        
        async def test_with_sem():
            async with semaphore:
                return await mock_test(0.1)
        
        tasks = [test_with_sem() for _ in range(100)]
        return await asyncio.gather(*tasks)
    
    asyncio.run(parallel_test())
    parallel_time = time.time() - start
    print(f"    耗时: {parallel_time:.2f}s")
    
    speedup = serial_time / parallel_time
    print(f"\n  加速比: {speedup:.2f}x")
    print(f"  效率提升: {(speedup-1)*100:.1f}%")
    
    print("\n✓ 测试执行速度基准测试完成")
    return True


def benchmark_memory_usage():
    """基准测试：内存使用"""
    print("\n" + "=" * 80)
    print("基准测试 4: 内存使用分析")
    print("=" * 80)
    
    try:
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        # 初始内存
        mem_before = process.memory_info().rss / 1024 / 1024  # MB
        print(f"\n  初始内存: {mem_before:.2f} MB")
        
        # 创建大量缓存对象
        from llmct.utils.sqlite_cache import SQLiteCache
        fd, db_path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            cache = SQLiteCache(db_file=db_path)
            
            # 写入10000条记录
            for i in range(10000):
                cache.update_cache(
                    f'model-{i}',
                    success=i % 2 == 0,
                    response_time=1.0,
                    error_code='',
                    content=f'Content {i}' * 10  # 增大内容
                )
            
            cache.flush()
            
            mem_after = process.memory_info().rss / 1024 / 1024
            print(f"  写入10000条后: {mem_after:.2f} MB")
            print(f"  内存增长: {mem_after - mem_before:.2f} MB")
            
            # 查询所有记录
            for i in range(10000):
                cache.get_cached_result(f'model-{i}')
            
            mem_query = process.memory_info().rss / 1024 / 1024
            print(f"  查询10000条后: {mem_query:.2f} MB")
            
        finally:
            try:
                os.unlink(db_path)
                for ext in ['-wal', '-shm']:
                    wal_file = db_path + ext
                    if os.path.exists(wal_file):
                        os.unlink(wal_file)
            except:
                pass
        
        print("\n✓ 内存使用基准测试完成")
        return True
        
    except ImportError:
        print("\n  [跳过] 需要安装psutil: pip install psutil")
        return True


def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("LLMCT 性能基准测试套件")
    print("=" * 80)
    print(f"Python版本: {sys.version}")
    print(f"开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    try:
        results.append(("SQLite缓存", benchmark_sqlite_cache()))
    except Exception as e:
        print(f"\n✗ SQLite缓存测试失败: {e}")
        import traceback
        traceback.print_exc()
        results.append(("SQLite缓存", False))
    
    try:
        results.append(("自适应并发", benchmark_adaptive_concurrency()))
    except Exception as e:
        print(f"\n✗ 自适应并发测试失败: {e}")
        import traceback
        traceback.print_exc()
        results.append(("自适应并发", False))
    
    try:
        results.append(("测试执行", benchmark_test_execution()))
    except Exception as e:
        print(f"\n✗ 测试执行基准失败: {e}")
        import traceback
        traceback.print_exc()
        results.append(("测试执行", False))
    
    try:
        results.append(("内存使用", benchmark_memory_usage()))
    except Exception as e:
        print(f"\n✗ 内存使用测试失败: {e}")
        import traceback
        traceback.print_exc()
        results.append(("内存使用", False))
    
    # 总结
    print("\n" + "=" * 80)
    print("基准测试总结")
    print("=" * 80)
    
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}  {name}")
    
    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)
    
    print(f"\n通过率: {passed_count}/{total_count} ({passed_count/total_count*100:.0f}%)")
    
    if passed_count == total_count:
        print("\n所有基准测试通过!")
        return 0
    else:
        print(f"\n{total_count - passed_count} 个基准测试失败")
        return 1


if __name__ == '__main__':
    sys.exit(main())
