#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
按 Base URL 分析功能示例

演示如何使用新的按 base_url 分类保存和统计分析功能
"""

import json
from pathlib import Path
from datetime import datetime

from llmct.core.reporter import Reporter
from llmct.core.analyzer import ResultAnalyzer


def example_1_save_with_base_url():
    """示例1：按 base_url 保存测试结果"""
    print("="*80)
    print("示例1：按 base_url 保存测试结果")
    print("="*80)
    
    # 模拟测试结果
    test_results = [
        {
            'model': 'gpt-4o',
            'success': True,
            'response_time': 1.2,
            'error_code': '',
            'content': 'Hello! How can I help you today?'
        },
        {
            'model': 'gpt-4o-mini',
            'success': True,
            'response_time': 0.8,
            'error_code': '',
            'content': 'Hi there!'
        },
        {
            'model': 'gpt-3.5-turbo',
            'success': False,
            'response_time': 0,
            'error_code': 'HTTP_403',
            'content': ''
        }
    ]
    
    # 创建 Reporter
    base_url = 'https://api.openai.com'
    reporter = Reporter(base_url)
    
    # 保存结果（自动创建目录结构）
    output_file = reporter.save_report(
        test_results,
        'test_results.json',
        format='json'
    )
    
    print(f"\n✓ 测试结果已保存到: {output_file}")
    print(f"  目录结构: test_results/{reporter._get_base_url_safe_name()}/")
    print()


def example_2_analyze_history():
    """示例2：分析历史测试结果"""
    print("="*80)
    print("示例2：分析历史测试结果")
    print("="*80)
    
    # 假设我们有一个包含多次测试结果的目录
    base_url_dir = 'test_results/api.openai.com'
    
    if not Path(base_url_dir).exists():
        print(f"\n⚠ 目录不存在: {base_url_dir}")
        print("  请先运行一些测试以生成测试结果")
        print()
        return
    
    # 创建分析器
    analyzer = ResultAnalyzer()
    
    # 分析所有历史测试
    print(f"\n正在分析 {base_url_dir} ...")
    analysis = analyzer.analyze_by_base_url(base_url_dir)
    
    if 'error' in analysis:
        print(f"\n✗ 分析失败: {analysis['error']}")
        return
    
    # 打印总体统计
    summary = analysis['summary']
    print(f"\n📊 总体统计:")
    print(f"  测试文件数: {summary['total_test_files']}")
    print(f"  模型总数: {summary['total_models']}")
    print(f"  分析时间: {summary['analysis_time']}")
    
    # 打印前5个模型的统计
    model_stats = analysis['model_statistics']
    print(f"\n📈 模型统计（前5个）:")
    for i, (model_name, stats) in enumerate(list(model_stats.items())[:5], 1):
        print(f"\n  {i}. {model_name}")
        print(f"     总测试: {stats['total_tests']} | 成功: {stats['success_tests']} | 失败: {stats['failed_tests']}")
        print(f"     成功率: {stats['success_rate']:.1f}% | 平均响应时间: {stats['avg_response_time']:.2f}秒")
        if stats['error_codes']:
            print(f"     错误分布: {stats['error_codes']}")
    
    print()


def example_3_get_success_rates():
    """示例3：获取模型成功率排名"""
    print("="*80)
    print("示例3：获取模型成功率排名")
    print("="*80)
    
    base_url_dir = 'test_results/api.openai.com'
    
    if not Path(base_url_dir).exists():
        print(f"\n⚠ 目录不存在: {base_url_dir}")
        print()
        return
    
    # 创建分析器
    analyzer = ResultAnalyzer()
    
    # 获取成功率排名（至少测试过2次的模型）
    print(f"\n正在计算成功率排名...")
    ranked_models = analyzer.get_model_success_rates(base_url_dir, min_tests=1)
    
    if not ranked_models:
        print("✗ 未找到测试数据")
        return
    
    # 打印排名表格
    print(f"\n🏆 模型成功率排名 (Top 10):")
    print(f"\n{'排名':<6} {'模型名称':<40} {'测试次数':<10} {'成功率':<10} {'平均响应时间':<12}")
    print("-" * 80)
    
    for rank, model in enumerate(ranked_models[:10], 1):
        model_name = model['model']
        if len(model_name) > 37:
            model_name = model_name[:34] + '...'
        
        print(f"{rank:<6} {model_name:<40} {model['total_tests']:<10} "
              f"{model['success_rate']:>6.1f}%    {model['avg_response_time']:>8.2f}秒")
    
    print()


def example_4_save_analysis_report():
    """示例4：保存详细分析报告"""
    print("="*80)
    print("示例4：保存详细分析报告")
    print("="*80)
    
    base_url_dir = 'test_results/api.openai.com'
    
    if not Path(base_url_dir).exists():
        print(f"\n⚠ 目录不存在: {base_url_dir}")
        print()
        return
    
    # 创建分析器
    analyzer = ResultAnalyzer()
    
    # 保存分析报告
    print(f"\n正在生成分析报告...")
    output_file = analyzer.save_base_url_analysis(base_url_dir)
    
    if output_file:
        print(f"✓ 分析报告已保存: {output_file}")
        
        # 读取并显示部分内容
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"\n报告包含:")
        print(f"  - 总体统计信息")
        print(f"  - {len(data['model_statistics'])} 个模型的详细统计")
        print(f"  - 每个模型的测试历史记录")
    
    print()


def example_5_create_mock_data():
    """示例5：创建模拟数据用于演示"""
    print("="*80)
    print("示例5：创建模拟数据用于演示")
    print("="*80)
    
    # 创建模拟的测试结果目录
    base_url = 'https://api.example.com'
    reporter = Reporter(base_url)
    safe_name = reporter._get_base_url_safe_name()
    
    results_dir = Path('test_results') / safe_name
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成3次模拟测试结果
    for day in range(1, 4):
        test_results = [
            {
                'model': 'model-a',
                'success': True,
                'response_time': 1.0 + day * 0.1,
                'error_code': '',
                'content': 'Response from model-a'
            },
            {
                'model': 'model-b',
                'success': day != 2,  # 第2天失败
                'response_time': 0.5 if day != 2 else 0,
                'error_code': '' if day != 2 else 'TIMEOUT',
                'content': 'Response from model-b' if day != 2 else ''
            },
            {
                'model': 'model-c',
                'success': False,
                'response_time': 0,
                'error_code': 'HTTP_403',
                'content': ''
            }
        ]
        
        # 保存测试结果
        test_file = results_dir / f'test_2025010{day}_120000.json'
        data = {
            'metadata': {
                'base_url': base_url,
                'test_start_time': f'2025-01-0{day} 12:00:00',
                'total': len(test_results),
                'success': sum(1 for r in test_results if r['success']),
                'failed': sum(1 for r in test_results if not r['success'])
            },
            'results': test_results
        }
        
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"✓ 创建模拟测试结果: {test_file}")
    
    print(f"\n✓ 模拟数据创建完成！")
    print(f"  目录: {results_dir}")
    print(f"\n现在可以运行分析命令:")
    print(f"  python mct.py --analyze {results_dir}")
    print()


def main():
    """主函数"""
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*20 + "按 Base URL 分析功能示例" + " "*33 + "║")
    print("╚" + "="*78 + "╝")
    print()
    
    while True:
        print("请选择要运行的示例:")
        print("  1. 按 base_url 保存测试结果")
        print("  2. 分析历史测试结果")
        print("  3. 获取模型成功率排名")
        print("  4. 保存详细分析报告")
        print("  5. 创建模拟数据用于演示")
        print("  0. 退出")
        print()
        
        choice = input("请输入选项 (0-5): ").strip()
        print()
        
        if choice == '1':
            example_1_save_with_base_url()
        elif choice == '2':
            example_2_analyze_history()
        elif choice == '3':
            example_3_get_success_rates()
        elif choice == '4':
            example_4_save_analysis_report()
        elif choice == '5':
            example_5_create_mock_data()
        elif choice == '0':
            print("再见！")
            break
        else:
            print("⚠ 无效选项，请重试\n")
        
        input("按 Enter 继续...")
        print("\n" * 2)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n程序已中断")
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()
