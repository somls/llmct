#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v2.4.0 功能演示脚本

演示新增的按 base_url 分类保存和统计分析功能
"""

import json
import os
import sys
import shutil
from pathlib import Path
from datetime import datetime

# 设置 Windows 控制台编码
if sys.platform == 'win32':
    import codecs
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from llmct.core.reporter import Reporter
from llmct.core.analyzer import ResultAnalyzer


def print_section(title):
    """打印章节标题"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")


def demo_step_1_create_mock_data():
    """步骤1: 创建模拟测试数据"""
    print_section("步骤 1: 创建模拟测试数据")
    
    # 清理旧数据
    demo_dir = Path('demo_test_results')
    if demo_dir.exists():
        shutil.rmtree(demo_dir)
        print("✓ 清理旧的演示数据")
    
    # 修改工作目录以使用 demo_test_results
    os.makedirs(demo_dir, exist_ok=True)
    os.chdir(demo_dir)
    
    # 创建3次模拟测试
    base_url = 'https://api.demo.com'
    reporter = Reporter(base_url)
    
    print(f"模拟 API: {base_url}")
    print(f"生成 3 次测试结果...\n")
    
    test_files = []
    
    for day in range(1, 4):
        # 模拟测试结果（逐渐改善）
        results = [
            {
                'model': 'gpt-4',
                'success': True,
                'response_time': 1.2 - day * 0.1,  # 逐渐变快
                'error_code': '',
                'content': f'Response from gpt-4 (test {day})'
            },
            {
                'model': 'gpt-3.5-turbo',
                'success': day >= 2,  # 第1天失败，后面成功
                'response_time': 0.8 if day >= 2 else 0,
                'error_code': '' if day >= 2 else 'HTTP_403',
                'content': f'Response from gpt-3.5-turbo' if day >= 2 else ''
            },
            {
                'model': 'text-embedding-ada-002',
                'success': True,
                'response_time': 0.4,
                'error_code': '',
                'content': 'Embedding generated'
            }
        ]
        
        # 保存测试结果
        output_file = reporter.save_report(
            results,
            f'demo_test_{day}.json',
            format='json'
        )
        test_files.append(output_file)
        
        print(f"  第 {day} 次测试: {output_file}")
    
    print(f"\n✓ 成功生成 {len(test_files)} 个测试结果文件")
    
    # 返回上级目录
    os.chdir('..')
    
    return test_files


def demo_step_2_analyze_results():
    """步骤2: 分析测试结果"""
    print_section("步骤 2: 分析测试结果")
    
    base_url_dir = 'demo_test_results/test_results/api.demo.com'
    
    if not Path(base_url_dir).exists():
        print("✗ 测试结果目录不存在")
        return
    
    analyzer = ResultAnalyzer()
    
    print(f"正在分析: {base_url_dir}\n")
    
    # 执行分析
    analysis = analyzer.analyze_by_base_url(base_url_dir)
    
    if 'error' in analysis:
        print(f"✗ 分析失败: {analysis['error']}")
        return
    
    # 打印总体统计
    summary = analysis['summary']
    print("📊 总体统计:")
    print(f"  测试文件数: {summary['total_test_files']}")
    print(f"  模型总数: {summary['total_models']}")
    
    # 打印模型统计
    print("\n📈 模型统计:")
    model_stats = analysis['model_statistics']
    
    for model_name, stats in model_stats.items():
        print(f"\n  {model_name}:")
        print(f"    总测试: {stats['total_tests']} | 成功: {stats['success_tests']} | 失败: {stats['failed_tests']}")
        print(f"    成功率: {stats['success_rate']:.1f}%")
        print(f"    平均响应时间: {stats['avg_response_time']:.2f}秒")
        
        if stats['error_codes']:
            print(f"    错误分布: {stats['error_codes']}")
    
    print("\n✓ 分析完成")
    
    return analysis


def demo_step_3_get_rankings():
    """步骤3: 获取成功率排名"""
    print_section("步骤 3: 获取成功率排名")
    
    base_url_dir = 'demo_test_results/test_results/api.demo.com'
    
    analyzer = ResultAnalyzer()
    
    print(f"计算模型成功率排名...\n")
    
    ranked = analyzer.get_model_success_rates(base_url_dir, min_tests=1)
    
    if not ranked:
        print("✗ 未找到测试数据")
        return
    
    # 打印排名表格
    print("🏆 模型成功率排名:")
    print()
    print(f"{'排名':<6} {'模型名称':<30} {'测试次数':<10} {'成功率':<10} {'平均响应时间':<12}")
    print("-" * 80)
    
    for rank, model in enumerate(ranked, 1):
        print(f"{rank:<6} {model['model']:<30} {model['total_tests']:<10} "
              f"{model['success_rate']:>6.1f}%    {model['avg_response_time']:>8.2f}秒")
    
    print("\n✓ 排名计算完成")
    
    return ranked


def demo_step_4_save_report():
    """步骤4: 保存分析报告"""
    print_section("步骤 4: 保存分析报告")
    
    base_url_dir = 'demo_test_results/test_results/api.demo.com'
    
    analyzer = ResultAnalyzer()
    
    print(f"生成分析报告...\n")
    
    output_file = analyzer.save_base_url_analysis(base_url_dir)
    
    if output_file:
        print(f"✓ 分析报告已保存: {output_file}")
        
        # 读取并显示部分内容
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"\n报告内容预览:")
        print(f"  - 测试文件数: {data['summary']['total_test_files']}")
        print(f"  - 模型总数: {data['summary']['total_models']}")
        print(f"  - 包含详细的模型统计和测试历史")
    
    return output_file


def demo_step_5_show_insights():
    """步骤5: 展示分析洞察"""
    print_section("步骤 5: 分析洞察")
    
    base_url_dir = 'demo_test_results/test_results/api.demo.com'
    
    analyzer = ResultAnalyzer()
    analysis = analyzer.analyze_by_base_url(base_url_dir)
    
    if 'error' in analysis:
        print("✗ 无法生成洞察")
        return
    
    model_stats = analysis['model_statistics']
    
    print("💡 关键发现:\n")
    
    # 1. 最稳定的模型
    most_stable = max(model_stats.items(), key=lambda x: x[1]['success_rate'])
    print(f"1. 最稳定的模型:")
    print(f"   {most_stable[0]} (成功率: {most_stable[1]['success_rate']:.1f}%)")
    
    # 2. 最快的模型
    successful_models = {k: v for k, v in model_stats.items() if v['avg_response_time'] > 0}
    if successful_models:
        fastest = min(successful_models.items(), key=lambda x: x[1]['avg_response_time'])
        print(f"\n2. 响应最快的模型:")
        print(f"   {fastest[0]} (平均响应: {fastest[1]['avg_response_time']:.2f}秒)")
    
    # 3. 改善趋势
    for model_name, stats in model_stats.items():
        if stats['success_rate'] > 0 and stats['success_rate'] < 100:
            history = stats['test_history']
            if len(history) >= 2:
                recent_success = history[-1]['success']
                early_success = history[0]['success']
                if recent_success and not early_success:
                    print(f"\n3. 改善趋势:")
                    print(f"   {model_name} 从失败变为成功")
    
    print("\n✓ 洞察分析完成")


def cleanup_demo():
    """清理演示数据"""
    print_section("清理演示数据")
    
    demo_dir = Path('demo_test_results')
    if demo_dir.exists():
        shutil.rmtree(demo_dir)
        print("✓ 已清理所有演示数据")
    else:
        print("✓ 无需清理")


def main():
    """主函数"""
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*25 + "v2.4.0 功能演示" + " "*38 + "║")
    print("╚" + "="*78 + "╝")
    
    try:
        # 执行演示步骤
        demo_step_1_create_mock_data()
        demo_step_2_analyze_results()
        demo_step_3_get_rankings()
        demo_step_4_save_report()
        demo_step_5_show_insights()
        
        # 总结
        print_section("演示总结")
        print("✅ 所有功能演示完成！")
        print()
        print("新功能亮点:")
        print("  1. ✅ 测试结果自动按 base_url 分类保存")
        print("  2. ✅ 统计同一模型多次测试的成功率")
        print("  3. ✅ 自动计算平均响应时间和错误分布")
        print("  4. ✅ 生成详细的分析报告")
        print("  5. ✅ 提供成功率排名和性能洞察")
        print()
        
        # 询问是否清理
        print("演示数据位于 demo_test_results/ 目录")
        response = input("\n是否清理演示数据? (y/n): ").strip().lower()
        
        if response == 'y':
            cleanup_demo()
        else:
            print("\n✓ 演示数据已保留，您可以手动查看")
        
    except Exception as e:
        print(f"\n✗ 演示过程中出错: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n感谢使用！\n")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n演示已取消")
        cleanup_demo()
