#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析实际测试结果并生成优化建议
"""

import json
import sys
from statistics import mean, median, stdev
from collections import Counter

# 设置Windows控制台输出编码
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


def analyze_response_times(results):
    """分析响应时间分布"""
    response_times = []
    for result in results:
        if result.get('success') and result.get('response_time'):
            response_times.append(result['response_time'])
    
    if not response_times:
        return None
    
    return {
        'count': len(response_times),
        'mean': mean(response_times),
        'median': median(response_times),
        'stdev': stdev(response_times) if len(response_times) > 1 else 0,
        'min': min(response_times),
        'max': max(response_times),
        'p95': sorted(response_times)[int(len(response_times) * 0.95)] if len(response_times) > 1 else response_times[0]
    }


def analyze_errors(results):
    """分析错误类型分布"""
    error_codes = []
    for result in results:
        if not result.get('success') and result.get('error_code'):
            error_codes.append(result['error_code'])
    
    return Counter(error_codes)


def categorize_models_by_speed(results):
    """按响应速度分类模型"""
    fast = []      # < 3秒
    medium = []    # 3-5秒
    slow = []      # > 5秒
    
    for result in results:
        if result.get('success') and result.get('response_time'):
            rt = result['response_time']
            model = result['model']
            
            if rt < 3:
                fast.append((model, rt))
            elif rt < 5:
                medium.append((model, rt))
            else:
                slow.append((model, rt))
    
    return {
        'fast': sorted(fast, key=lambda x: x[1]),
        'medium': sorted(medium, key=lambda x: x[1]),
        'slow': sorted(slow, key=lambda x: x[1])
    }


def generate_recommendations(results, response_stats, error_counter, speed_categories):
    """生成优化建议"""
    recommendations = []
    
    # 1. 响应时间建议
    if response_stats:
        avg_time = response_stats['mean']
        if avg_time > 5:
            recommendations.append({
                'priority': 'high',
                'category': '响应时间',
                'issue': f'平均响应时间过高 ({avg_time:.2f}秒)',
                'recommendation': '建议增加并发数或优化提示词长度',
                'expected_improvement': '可能减少30-50%的总测试时间'
            })
        
        if response_stats['max'] > 10:
            recommendations.append({
                'priority': 'medium',
                'category': '响应时间',
                'issue': f'最慢模型响应时间: {response_stats["max"]:.2f}秒',
                'recommendation': f'考虑减少超时时间或跳过慢速模型',
                'expected_improvement': '避免等待超时'
            })
    
    # 2. 错误分析建议
    total_tests = len(results)
    failed_tests = sum(1 for r in results if not r.get('success'))
    
    if failed_tests > 0:
        failure_rate = failed_tests / total_tests * 100
        
        if 'HTTP_400' in error_counter:
            recommendations.append({
                'priority': 'high',
                'category': '错误处理',
                'issue': f'{error_counter["HTTP_400"]}个模型返回HTTP_400',
                'recommendation': '检查API请求参数格式，某些模型可能需要特殊参数',
                'expected_improvement': f'可能修复{error_counter["HTTP_400"]}个模型'
            })
        
        if 'HTTP_404' in error_counter:
            recommendations.append({
                'priority': 'low',
                'category': '模型可用性',
                'issue': f'{error_counter["HTTP_404"]}个模型不存在',
                'recommendation': '使用--max-failures 3跳过持续失败的模型',
                'expected_improvement': '节省测试时间'
            })
        
        if 'UNKNOWN_ERROR' in error_counter:
            recommendations.append({
                'priority': 'medium',
                'category': '错误处理',
                'issue': f'{error_counter["UNKNOWN_ERROR"]}个未知错误',
                'recommendation': '增加错误日志详细程度，分析具体原因',
                'expected_improvement': '提高调试效率'
            })
    
    # 3. 性能优化建议
    if speed_categories:
        fast_count = len(speed_categories['fast'])
        total_success = fast_count + len(speed_categories['medium']) + len(speed_categories['slow'])
        
        if fast_count / total_success > 0.5:
            recommendations.append({
                'priority': 'low',
                'category': '性能优化',
                'issue': f'{fast_count}个模型响应时间<3秒',
                'recommendation': '优先测试快速模型，可以设置更短的超时时间',
                'expected_improvement': '提升用户体验'
            })
    
    # 4. 并发建议
    if response_stats and response_stats['mean'] < 5:
        recommendations.append({
            'priority': 'medium',
            'category': '并发优化',
            'issue': '平均响应时间较快',
            'recommendation': '可以考虑增加并发数到15-20',
            'expected_improvement': '可能减少40-60%的总测试时间'
        })
    
    return recommendations


def print_analysis(results):
    """打印分析报告"""
    print("=" * 100)
    print("LLMCT 实际测试结果分析报告")
    print("=" * 100)
    print()
    
    # 基本统计
    total = len(results)
    success = sum(1 for r in results if r.get('success'))
    failed = total - success
    success_rate = success / total * 100 if total > 0 else 0
    
    print("📊 基本统计")
    print("-" * 100)
    print(f"  总测试数: {total}")
    print(f"  成功: {success} ({success_rate:.1f}%)")
    print(f"  失败: {failed} ({100-success_rate:.1f}%)")
    print()
    
    # 响应时间分析
    response_stats = analyze_response_times(results)
    if response_stats:
        print("⏱️  响应时间分析")
        print("-" * 100)
        print(f"  平均响应时间: {response_stats['mean']:.2f}秒")
        print(f"  中位数: {response_stats['median']:.2f}秒")
        print(f"  标准差: {response_stats['stdev']:.2f}秒")
        print(f"  最快: {response_stats['min']:.2f}秒")
        print(f"  最慢: {response_stats['max']:.2f}秒")
        print(f"  95分位: {response_stats['p95']:.2f}秒")
        print()
    
    # 速度分类
    speed_categories = categorize_models_by_speed(results)
    if speed_categories:
        print("🚀 模型速度分类")
        print("-" * 100)
        
        if speed_categories['fast']:
            print(f"  快速模型 (<3秒): {len(speed_categories['fast'])}个")
            for model, time in speed_categories['fast'][:5]:
                print(f"    • {model}: {time:.2f}秒")
        
        if speed_categories['medium']:
            print(f"  中速模型 (3-5秒): {len(speed_categories['medium'])}个")
            for model, time in speed_categories['medium'][:3]:
                print(f"    • {model}: {time:.2f}秒")
        
        if speed_categories['slow']:
            print(f"  慢速模型 (>5秒): {len(speed_categories['slow'])}个")
            for model, time in speed_categories['slow']:
                print(f"    • {model}: {time:.2f}秒")
        print()
    
    # 错误分析
    error_counter = analyze_errors(results)
    if error_counter:
        print("❌ 错误分析")
        print("-" * 100)
        for error_code, count in error_counter.most_common():
            percentage = count / failed * 100 if failed > 0 else 0
            print(f"  {error_code}: {count}次 ({percentage:.1f}%)")
        print()
    
    # 生成建议
    recommendations = generate_recommendations(results, response_stats, error_counter, speed_categories)
    
    if recommendations:
        print("💡 优化建议")
        print("=" * 100)
        
        # 按优先级排序
        priority_order = {'high': 1, 'medium': 2, 'low': 3}
        recommendations.sort(key=lambda x: priority_order.get(x['priority'], 4))
        
        for i, rec in enumerate(recommendations, 1):
            priority_icon = {
                'high': '🔴',
                'medium': '🟡',
                'low': '🟢'
            }.get(rec['priority'], '⚪')
            
            print(f"\n{i}. {priority_icon} [{rec['priority'].upper()}] {rec['category']}")
            print(f"   问题: {rec['issue']}")
            print(f"   建议: {rec['recommendation']}")
            print(f"   预期效果: {rec['expected_improvement']}")
    
    print()
    print("=" * 100)


def main():
    """主函数"""
    try:
        with open('test_results.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 提取测试结果
        results = []
        for line in data.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            parts = line.split('|')
            if len(parts) >= 4:
                model = parts[0].strip()
                response_time_str = parts[1].strip()
                error_code = parts[2].strip()
                content = parts[3].strip()
                
                # 解析响应时间
                response_time = None
                if '秒' in response_time_str:
                    try:
                        response_time = float(response_time_str.replace('秒', '').strip())
                    except:
                        pass
                
                # 判断是否成功
                success = response_time is not None and error_code == '-'
                
                results.append({
                    'model': model,
                    'success': success,
                    'response_time': response_time,
                    'error_code': error_code if error_code != '-' else None,
                    'content': content
                })
        
        if results:
            print_analysis(results)
        else:
            print("未找到测试结果，请先运行测试")
    
    except FileNotFoundError:
        print("错误: 未找到test_results.json文件")
        print("请先运行测试: python mct.py --api-key ... --base-url ... --output test_results.json")
        return 1
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
