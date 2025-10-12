#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大模型连通性测试工具 - 异步优化版
使用异步并发测试，大幅提升测试速度
"""

import argparse
import asyncio
import sys
import time
from typing import List, Dict
from datetime import datetime

# 导入优化模块
from llmct.core.async_tester import AsyncModelTester
from llmct.core.classifier import ModelClassifier
from llmct.utils.sqlite_cache import SQLiteCache
from llmct.utils.adaptive_concurrency import AdaptiveConcurrencyController
from llmct.utils.logger import get_logger

logger = get_logger()


class AsyncModelTestRunner:
    """异步模型测试运行器"""
    
    def __init__(
        self,
        api_key: str,
        base_url: str,
        timeout: int = 30,
        initial_concurrency: int = 10,
        cache_enabled: bool = True
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.cache = SQLiteCache() if cache_enabled else None
        self.concurrency_controller = AdaptiveConcurrencyController(
            initial_concurrency=initial_concurrency,
            min_concurrency=3,
            max_concurrency=30
        )
        self.classifier = ModelClassifier()
        
        # 统计信息
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'cached': 0,
            'skipped': 0,
            'start_time': None,
            'end_time': None
        }
    
    async def validate_credentials(self) -> bool:
        """验证API凭证"""
        import aiohttp
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/v1/models"
                headers = {'Authorization': f'Bearer {self.api_key}'}
                
                async with session.get(url, headers=headers, timeout=10) as response:
                    if response.status == 401:
                        error_data = await response.json()
                        error_msg = error_data.get('error', {}).get('message', '认证失败')
                        print(f"\n{'='*110}")
                        print(f"[严重错误] API认证失败: {error_msg}")
                        print(f"{'='*110}")
                        print("\n可能的原因:")
                        print("  1. API密钥已过期")
                        print("  2. API密钥格式错误")
                        print("  3. Base URL配置错误")
                        print("\n请检查您的API配置后重试。")
                        print(f"{'='*110}\n")
                        return False
                    elif response.status == 200:
                        data = await response.json()
                        model_count = len(data.get('data', []))
                        print(f"[信息] API认证成功，发现 {model_count} 个模型\n")
                        return True
                    else:
                        print(f"[警告] API响应异常: HTTP {response.status}")
                        return False
        except Exception as e:
            print(f"[错误] 连接失败: {e}")
            return False
    
    async def get_models(self) -> List[Dict]:
        """获取模型列表"""
        import aiohttp
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/v1/models"
                headers = {'Authorization': f'Bearer {self.api_key}'}
                
                async with session.get(url, headers=headers, timeout=self.timeout) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('data', [])
                    else:
                        print(f"[错误] 获取模型列表失败: HTTP {response.status}")
                        return []
        except Exception as e:
            print(f"[错误] 获取模型列表失败: {e}")
            return []
    
    def filter_models(self, models: List[Dict], only_failed: bool = False, max_failures: int = 0) -> List[Dict]:
        """过滤模型列表"""
        if not self.cache:
            return models
        
        filtered = []
        for model in models:
            model_id = model.get('id', model.get('model', 'unknown'))
            
            # 跳过失败次数过多的模型
            if max_failures > 0:
                failure_count = self.cache.get_failure_count(model_id)
                if failure_count >= max_failures:
                    self.stats['skipped'] += 1
                    continue
            
            # 仅测试失败模型
            if only_failed:
                if model_id in self.cache.get_failed_models():
                    filtered.append(model)
            else:
                filtered.append(model)
        
        return filtered
    
    def print_progress(self, current: int, total: int, result: Dict):
        """打印测试进度"""
        model_id = result['model']
        success = result['success']
        response_time = result['response_time']
        error_code = result['error_code']
        
        # 截断过长的模型名
        if len(model_id) > 45:
            model_id = model_id[:42] + '...'
        
        # 格式化输出
        status = "OK" if success else "FAIL"
        time_str = f"{response_time:.2f}s" if response_time > 0 else "-"
        error_str = error_code if error_code else "-"
        
        # 获取当前并发数
        current_concurrency = self.concurrency_controller.get_current_concurrency()
        stats = self.concurrency_controller.get_stats()
        
        print(f"[{current}/{total}] {status} {model_id:<45} | {time_str:>8} | {error_str:<12} | 并发:{current_concurrency}")
    
    async def test_all_models_async(
        self,
        test_message: str = "hello",
        only_failed: bool = False,
        max_failures: int = 0
    ):
        """异步测试所有模型"""
        
        self.stats['start_time'] = time.time()
        
        print(f"\n{'='*110}")
        print(f"大模型连通性测试 [异步优化版]")
        print(f"Base URL: {self.base_url}")
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*110}\n")
        
        # 验证凭证
        print("正在验证API凭证...")
        if not await self.validate_credentials():
            sys.exit(1)
        
        # 获取模型列表
        print("正在获取模型列表...")
        all_models = await self.get_models()
        
        if not all_models:
            print("[错误] 未获取到任何模型")
            return
        
        # 过滤模型
        models = self.filter_models(all_models, only_failed, max_failures)
        
        if not models:
            print(f"\n[提示] 没有需要测试的模型")
            if only_failed:
                print("  - 原因：没有失败的模型记录")
                print("  - 建议：先运行一次全量测试")
            return
        
        print(f"共发现 {len(all_models)} 个模型，将测试 {len(models)} 个模型")
        if max_failures > 0:
            print(f"失败阈值: 跳过失败{max_failures}次以上的模型")
        print()
        
        self.stats['total'] = len(models)
        
        # 分类模型
        model_types = {}
        for model in models:
            model_id = model.get('id', model.get('model', 'unknown'))
            model_types[model_id] = self.classifier.classify(model_id)
        
        # 创建异步测试器
        async with AsyncModelTester(
            self.api_key,
            self.base_url,
            self.timeout,
            self.concurrency_controller.get_current_concurrency()
        ) as tester:
            
            # 使用信号量控制并发
            results = []
            completed = 0
            
            async def test_with_progress(model):
                nonlocal completed
                
                model_id = model.get('id', model.get('model', 'unknown'))
                
                # 检查缓存
                if self.cache and self.cache.is_cached(model_id):
                    cached_result = self.cache.get_cached_result(model_id)
                    result = {
                        'model': model_id,
                        'success': cached_result['success'] == 1,
                        'response_time': cached_result['response_time'],
                        'error_code': cached_result.get('error_code', ''),
                        'content': f"[缓存] {cached_result['content']}"
                    }
                    self.stats['cached'] += 1
                else:
                    # 获取当前并发数（可能被动态调整）
                    current_concurrency = self.concurrency_controller.get_current_concurrency()
                    semaphore = asyncio.Semaphore(current_concurrency)
                    
                    result = await tester.test_model_with_semaphore(
                        semaphore,
                        model,
                        model_types.get(model_id, 'language'),
                        test_message
                    )
                    
                    # 更新并发控制器
                    is_rate_limit = result['error_code'] == 'HTTP_429'
                    self.concurrency_controller.record_result(
                        result['success'],
                        result['response_time'],
                        is_rate_limit,
                        result['error_code']
                    )
                    
                    # 更新缓存
                    if self.cache:
                        self.cache.update_cache(
                            model_id,
                            result['success'],
                            result['response_time'],
                            result['error_code'],
                            result['content']
                        )
                
                # 更新统计
                if result['success']:
                    self.stats['success'] += 1
                else:
                    self.stats['failed'] += 1
                
                completed += 1
                self.print_progress(completed, len(models), result)
                
                return result
            
            # 并发执行所有测试
            tasks = [test_with_progress(model) for model in models]
            results = await asyncio.gather(*tasks, return_exceptions=False)
        
        self.stats['end_time'] = time.time()
        
        # 刷新缓存
        if self.cache:
            self.cache.flush()
        
        # 打印总结
        self.print_summary()
    
    def print_summary(self):
        """打印测试总结"""
        elapsed = self.stats['end_time'] - self.stats['start_time']
        
        print(f"\n{'='*110}")
        print(f"测试完成")
        print(f"{'='*110}")
        print(f"总计: {self.stats['total']}")
        print(f"成功: {self.stats['success']} ({self.stats['success']/self.stats['total']*100:.1f}%)" if self.stats['total'] > 0 else "成功: 0")
        print(f"失败: {self.stats['failed']}")
        print(f"缓存命中: {self.stats['cached']}")
        print(f"跳过: {self.stats['skipped']}")
        print(f"总耗时: {elapsed:.1f}秒")
        print(f"平均速度: {self.stats['total']/elapsed:.1f}个/秒" if elapsed > 0 else "平均速度: -")
        
        # 并发控制器统计
        cc_stats = self.concurrency_controller.get_stats()
        print(f"\n并发控制:")
        print(f"  最终并发数: {cc_stats['current_concurrency']}")
        print(f"  成功率: {cc_stats['success_rate']:.1f}%")
        print(f"  429错误次数: {cc_stats['total_429_count']}")
        print(f"  并发调整次数: {cc_stats['adjustments_count']}")
        
        print(f"{'='*110}\n")


def main():
    parser = argparse.ArgumentParser(
        description='大模型连通性测试工具 - 异步优化版',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--api-key', required=True, help='API密钥')
    parser.add_argument('--base-url', required=True, help='API基础URL')
    parser.add_argument('--message', default='hello', help='测试消息')
    parser.add_argument('--timeout', type=int, default=30, help='超时时间(秒)')
    parser.add_argument('--concurrency', type=int, default=10, help='初始并发数')
    parser.add_argument('--only-failed', action='store_true', help='仅测试失败模型')
    parser.add_argument('--max-failures', type=int, default=0, help='失败次数阈值')
    parser.add_argument('--no-cache', action='store_true', help='禁用缓存')
    
    args = parser.parse_args()
    
    try:
        runner = AsyncModelTestRunner(
            api_key=args.api_key,
            base_url=args.base_url,
            timeout=args.timeout,
            initial_concurrency=args.concurrency,
            cache_enabled=not args.no_cache
        )
        
        asyncio.run(runner.test_all_models_async(
            test_message=args.message,
            only_failed=args.only_failed,
            max_failures=args.max_failures
        ))
        
    except KeyboardInterrupt:
        print("\n\n测试已取消")
        sys.exit(0)
    except Exception as e:
        print(f"\n[错误] 程序异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
