"""
v2.0 新功能使用示例
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def example_1_config_usage():
    """示例1：使用配置文件"""
    print("\n" + "="*60)
    print("示例1：配置文件使用")
    print("="*60)
    
    from llmct.utils.config import Config
    
    # 创建配置模板
    Config.create_template('example_config.yaml')
    
    # 加载配置
    config = Config()
    
    # 获取配置值
    print(f"API超时: {config.get('api.timeout')}秒")
    print(f"缓存启用: {config.get('cache.enabled')}")
    print(f"并发数: {config.get('performance.concurrent')}")
    
    # 设置配置值
    config.set('testing.only_failed', True)
    print(f"只测试失败模型: {config.get('testing.only_failed')}")


def example_2_logger():
    """示例2：日志系统使用"""
    print("\n" + "="*60)
    print("示例2：日志系统")
    print("="*60)
    
    from llmct.utils.logger import get_logger
    
    logger = get_logger()
    
    logger.info("这是一条信息日志")
    logger.warning("这是一条警告日志")
    logger.error("这是一条错误日志")
    
    # 可以添加额外信息
    logger.info("测试模型", model_id="gpt-4", response_time=1.5)


def example_3_retry():
    """示例3：重试机制"""
    print("\n" + "="*60)
    print("示例3：重试机制")
    print("="*60)
    
    from llmct.utils.retry import retry_on_exception
    
    call_count = {'count': 0}
    
    @retry_on_exception(
        exceptions=(ValueError,),
        max_attempts=3,
        delay=0.5,
        backoff=2.0
    )
    def unreliable_function():
        call_count['count'] += 1
        print(f"第 {call_count['count']} 次尝试")
        
        if call_count['count'] < 3:
            raise ValueError("暂时失败")
        
        return "成功！"
    
    result = unreliable_function()
    print(f"最终结果: {result}")


def example_4_classifier():
    """示例4：模型分类器"""
    print("\n" + "="*60)
    print("示例4：模型分类器")
    print("="*60)
    
    from llmct.core.classifier import ModelClassifier
    
    classifier = ModelClassifier()
    
    # 测试模型
    test_models = [
        'gpt-4o',
        'gpt-4-vision',
        'whisper-1',
        'text-embedding-ada-002',
        'dall-e-3',
        'qwen-vl-plus'
    ]
    
    print("\n模型分类结果：")
    for model in test_models:
        model_type = classifier.classify(model)
        print(f"  {model:<30} -> {model_type}")
    
    # 批量分类
    model_types = classifier.classify_batch(test_models)
    
    # 统计
    stats = classifier.get_statistics(test_models)
    print(f"\n类型统计:")
    for model_type, count in stats.items():
        print(f"  {model_type}: {count}")


def example_5_rate_limiter():
    """示例5：速率限制器"""
    print("\n" + "="*60)
    print("示例5：速率限制器")
    print("="*60)
    
    import time
    from llmct.utils.rate_limiter import RateLimiter
    
    # 创建限制器：每5秒最多3次调用
    limiter = RateLimiter(max_calls=3, period=5.0)
    
    print("尝试连续调用5次（每5秒限制3次）:")
    for i in range(5):
        limiter.wait_if_needed()
        print(f"  调用 {i+1} at {time.time():.2f}")
    
    remaining = limiter.get_remaining_calls()
    print(f"\n剩余可用调用次数: {remaining}")


def example_6_reporter():
    """示例6：多格式报告生成"""
    print("\n" + "="*60)
    print("示例6：多格式报告")
    print("="*60)
    
    from llmct.core.reporter import Reporter
    
    # 模拟测试结果
    sample_results = [
        {'model': 'gpt-4o', 'success': True, 'response_time': 1.2, 'error_code': '', 'content': 'Hello!'},
        {'model': 'gpt-3.5', 'success': True, 'response_time': 0.8, 'error_code': '', 'content': 'Hi there!'},
        {'model': 'test-model', 'success': False, 'response_time': 0, 'error_code': 'HTTP_403', 'content': ''},
    ]
    
    reporter = Reporter(base_url="https://api.test.com")
    
    # 保存为不同格式
    reporter.save_json(sample_results, 'example_output.json')
    reporter.save_csv(sample_results, 'example_output.csv')
    reporter.save_html(sample_results, 'example_output.html')
    
    print("已生成以下文件：")
    print("  - example_output.json")
    print("  - example_output.csv")
    print("  - example_output.html")


def example_7_analyzer():
    """示例7：结果分析"""
    print("\n" + "="*60)
    print("示例7：结果分析")
    print("="*60)
    
    from llmct.core.analyzer import ResultAnalyzer
    
    # 模拟测试结果
    sample_results = [
        {'model': 'gpt-4o', 'success': True, 'response_time': 1.2, 'error_code': '', 'content': 'OK'},
        {'model': 'gpt-3.5', 'success': True, 'response_time': 0.8, 'error_code': '', 'content': 'OK'},
        {'model': 'model-1', 'success': False, 'response_time': 0, 'error_code': 'HTTP_403', 'content': ''},
        {'model': 'model-2', 'success': False, 'response_time': 0, 'error_code': 'HTTP_429', 'content': ''},
        {'model': 'model-3', 'success': True, 'response_time': 2.5, 'error_code': '', 'content': 'OK'},
    ]
    
    analyzer = ResultAnalyzer()
    
    # 1. 健康度评分
    health = analyzer.calculate_health_score(sample_results)
    print(f"\nAPI健康度评分:")
    print(f"  总分: {health['score']}/100")
    print(f"  评级: {health['grade']}")
    print(f"  成功率: {health['details']['success_rate']}%")
    print(f"  平均响应时间: {health['details']['avg_response_time']:.2f}秒")
    
    # 2. 告警检查
    alerts = analyzer.check_alerts(sample_results)
    if alerts:
        print(f"\n[!] 检测到 {len(alerts)} 个告警:")
        for alert in alerts:
            print(f"  [{alert['severity'].upper()}] {alert['message']}")
    else:
        print("\n[OK] 未检测到告警")


def main():
    """运行所有示例"""
    print("\n" + "="*60)
    print("LLMCT v2.0 新功能示例")
    print("="*60)
    
    try:
        example_1_config_usage()
        example_2_logger()
        example_3_retry()
        example_4_classifier()
        example_5_rate_limiter()
        example_6_reporter()
        example_7_analyzer()
        
        print("\n" + "="*60)
        print("[SUCCESS] 所有示例运行完成！")
        print("="*60)
        
    except Exception as e:
        print(f"\n[ERROR] 运行示例时出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
