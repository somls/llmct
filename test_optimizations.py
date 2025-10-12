"""测试优化功能的验证脚本"""

import sys
import time

def test_imports():
    """测试模块导入"""
    print("=" * 60)
    print("Test 1: Module Import")
    print("=" * 60)
    
    try:
        from llmct.utils.sqlite_cache import SQLiteCache
        print("[PASS] SQLiteCache import success")
    except Exception as e:
        print(f"[FAIL] SQLiteCache import failed: {e}")
        return False
    
    try:
        from llmct.utils.adaptive_concurrency import AdaptiveConcurrencyController
        print("[PASS] AdaptiveConcurrencyController import success")
    except Exception as e:
        print(f"[FAIL] AdaptiveConcurrencyController import failed: {e}")
        return False
    
    try:
        from llmct.models import TestResult, ModelType, ErrorCode
        print("[PASS] Type definitions import success")
    except Exception as e:
        print(f"[FAIL] Type definitions import failed: {e}")
        return False
    
    try:
        from llmct.core.async_tester import AsyncModelTester
        print("[PASS] AsyncModelTester import success")
    except Exception as e:
        print(f"[FAIL] AsyncModelTester import failed: {e}")
        return False
    
    print("\nAll modules imported successfully!\n")
    return True


def test_sqlite_cache():
    """测试SQLite缓存"""
    print("=" * 60)
    print("Test 2: SQLite Cache")
    print("=" * 60)
    
    from llmct.utils.sqlite_cache import SQLiteCache
    
    # 创建缓存
    cache = SQLiteCache('test_optimization_cache.db')
    
    # 测试写入
    print("Testing batch write...")
    start = time.time()
    for i in range(100):
        cache.update_cache(
            f'test-model-{i}',
            success=i % 2 == 0,
            response_time=1.5,
            error_code='HTTP_403' if i % 2 == 1 else '',
            content='test content'
        )
    cache.flush()
    elapsed = time.time() - start
    print(f"[PASS] 100 records written in: {elapsed:.3f}s")
    
    # 测试查询
    print("\nTesting queries...")
    start = time.time()
    for i in range(100):
        result = cache.get_cached_result(f'test-model-{i}')
    elapsed = time.time() - start
    print(f"[PASS] 100 queries in: {elapsed:.3f}s")
    print(f"  Avg per query: {elapsed/100*1000:.2f}ms")
    
    # 测试统计
    stats = cache.get_stats()
    print(f"\nCache statistics:")
    print(f"  Total: {stats['total']}")
    print(f"  Success: {stats['success_count']}")
    print(f"  Failed: {stats['fail_count']}")
    
    # 清理
    import os
    try:
        os.remove('test_optimization_cache.db')
    except:
        pass
    
    print("\n[PASS] SQLite cache test completed!\n")
    return True


def test_adaptive_concurrency():
    """测试自适应并发控制"""
    print("=" * 60)
    print("Test 3: Adaptive Concurrency")
    print("=" * 60)
    
    from llmct.utils.adaptive_concurrency import AdaptiveConcurrencyController
    
    controller = AdaptiveConcurrencyController(
        initial_concurrency=10,
        min_concurrency=3,
        max_concurrency=50
    )
    
    print(f"Initial concurrency: {controller.get_current_concurrency()}")
    
    # 模拟429错误
    print("\nSimulating 3x 429 errors...")
    for i in range(3):
        controller.record_result(success=False, latency=5.0, is_rate_limit=True)
    print(f"After 429 errors: {controller.get_current_concurrency()}")
    
    # 模拟成功请求
    print("\nSimulating 20 successful requests...")
    for i in range(20):
        controller.record_result(success=True, latency=1.5, is_rate_limit=False)
    print(f"After success: {controller.get_current_concurrency()}")
    
    # 统计信息
    stats = controller.get_stats()
    print(f"\nStatistics:")
    print(f"  Current concurrency: {stats['current_concurrency']}")
    print(f"  Success rate: {stats['success_rate']:.1f}%")
    print(f"  Avg latency: {stats['avg_latency']:.3f}s")
    
    print("\n[PASS] Adaptive concurrency test completed!\n")
    return True


def test_types():
    """测试类型定义"""
    print("=" * 60)
    print("Test 4: Type Definitions")
    print("=" * 60)
    
    from llmct.models import TestResult, ModelType, TestConfig
    
    # 测试TestResult
    result = TestResult(
        model="gpt-4",
        success=True,
        response_time=1.23,
        content="Hello!"
    )
    print(f"[PASS] TestResult created: {result.model}")
    
    # 转换为字典
    result_dict = result.to_dict()
    print(f"[PASS] Converted to dict: {len(result_dict)} fields")
    
    # 从字典创建
    result2 = TestResult.from_dict(result_dict)
    print(f"[PASS] Created from dict: {result2.model}")
    
    # 测试枚举
    model_type = ModelType.LANGUAGE
    print(f"[PASS] Enum type: {model_type.value}")
    
    # 测试配置
    config = TestConfig(
        api_key="test-key",
        base_url="https://api.test.com",
        max_concurrent=20
    )
    print(f"[PASS] TestConfig created: concurrent={config.max_concurrent}")
    
    print("\n[PASS] Type definitions test completed!\n")
    return True


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("LLMCT Optimization Tests")
    print("=" * 60 + "\n")
    
    tests = [
        ("Module Import", test_imports),
        ("SQLite Cache", test_sqlite_cache),
        ("Adaptive Concurrency", test_adaptive_concurrency),
        ("Type Definitions", test_types),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n[FAIL] {name} test failed: {e}\n")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # 总结
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {name}")
    
    print(f"\nPass rate: {passed}/{total} ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("\nAll tests passed!")
        return 0
    else:
        print(f"\n{total - passed} test(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
