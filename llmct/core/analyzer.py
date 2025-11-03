"""测试结果分析器"""

import json
import os
from typing import Dict, List, Tuple
from datetime import datetime
from pathlib import Path
from collections import defaultdict


class ResultAnalyzer:
    """测试结果分析器 - 提供对比、评分、趋势分析功能"""
    
    def __init__(self):
        pass
    
    def analyze_by_base_url(self, base_url_dir: str) -> Dict:
        """
        分析指定base_url目录下的所有测试结果
        统计每个模型在多次测试中的成功率
        
        Args:
            base_url_dir: base_url对应的结果目录路径 (例如: test_results/api.openai.com)
            
        Returns:
            分析结果字典，包含每个模型的统计信息
        """
        base_path = Path(base_url_dir)
        if not base_path.exists():
            return {'error': f'目录不存在: {base_url_dir}'}
        
        # 收集所有JSON测试结果文件
        json_files = sorted(base_path.glob('test_*.json'))
        if not json_files:
            return {'error': f'未找到测试结果文件: {base_url_dir}'}
        
        # 按模型统计多次测试的结果
        model_stats = defaultdict(lambda: {
            'total_tests': 0,
            'success_tests': 0,
            'failed_tests': 0,
            'success_rate': 0.0,
            'avg_response_time': 0.0,
            'response_times': [],
            'error_codes': defaultdict(int),
            'test_history': []
        })
        
        # 遍历所有测试文件
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    test_time = data.get('metadata', {}).get('test_start_time', 'unknown')
                    results = data.get('results', [])
                    
                    # 统计每个模型的结果
                    for result in results:
                        model_name = result['model']
                        model_stats[model_name]['total_tests'] += 1
                        
                        if result['success']:
                            model_stats[model_name]['success_tests'] += 1
                            if result['response_time'] > 0:
                                model_stats[model_name]['response_times'].append(result['response_time'])
                        else:
                            model_stats[model_name]['failed_tests'] += 1
                            if result['error_code']:
                                model_stats[model_name]['error_codes'][result['error_code']] += 1
                        
                        # 记录测试历史
                        model_stats[model_name]['test_history'].append({
                            'test_time': test_time,
                            'success': result['success'],
                            'response_time': result.get('response_time', 0),
                            'error_code': result.get('error_code', '')
                        })
            except Exception as e:
                print(f"处理文件失败 {json_file}: {e}")
                continue
        
        # 计算每个模型的统计指标
        for model_name, stats in model_stats.items():
            stats['success_rate'] = (stats['success_tests'] / stats['total_tests'] * 100) if stats['total_tests'] > 0 else 0
            if stats['response_times']:
                stats['avg_response_time'] = sum(stats['response_times']) / len(stats['response_times'])
            
            # 转换 defaultdict 为普通 dict
            stats['error_codes'] = dict(stats['error_codes'])
        
        # 生成总体统计
        total_tests = len(json_files)
        all_models = list(model_stats.keys())
        
        summary = {
            'base_url_dir': str(base_url_dir),
            'total_test_files': total_tests,
            'total_models': len(all_models),
            'analysis_time': datetime.now().isoformat()
        }
        
        return {
            'summary': summary,
            'model_statistics': dict(model_stats)
        }
    
    def get_model_success_rates(self, base_url_dir: str, min_tests: int = 2) -> List[Dict]:
        """
        获取指定base_url下所有模型的成功率排名
        
        Args:
            base_url_dir: base_url对应的结果目录路径
            min_tests: 最小测试次数（只统计测试次数>=此值的模型）
            
        Returns:
            按成功率排序的模型列表
        """
        analysis = self.analyze_by_base_url(base_url_dir)
        if 'error' in analysis:
            return []
        
        model_stats = analysis['model_statistics']
        
        # 筛选并排序
        ranked_models = []
        for model_name, stats in model_stats.items():
            if stats['total_tests'] >= min_tests:
                ranked_models.append({
                    'model': model_name,
                    'total_tests': stats['total_tests'],
                    'success_tests': stats['success_tests'],
                    'failed_tests': stats['failed_tests'],
                    'success_rate': stats['success_rate'],
                    'avg_response_time': stats['avg_response_time']
                })
        
        # 按成功率降序排序
        ranked_models.sort(key=lambda x: (-x['success_rate'], x['avg_response_time']))
        
        return ranked_models
    
    def save_base_url_analysis(self, base_url_dir: str, output_file: str = None):
        """
        保存base_url的分析报告
        
        Args:
            base_url_dir: base_url对应的结果目录路径
            output_file: 输出文件路径（可选，默认保存在base_url_dir下）
        """
        analysis = self.analyze_by_base_url(base_url_dir)
        if 'error' in analysis:
            print(f"分析失败: {analysis['error']}")
            return
        
        # 默认输出文件名
        if output_file is None:
            base_path = Path(base_url_dir)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = base_path / f'analysis_{timestamp}.json'
        
        # 保存分析结果
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)
        
        print(f"分析报告已保存: {output_file}")
        return str(output_file)
    
    def compare_results(self, file1: str, file2: str) -> Dict:
        """
        对比两次测试结果
        
        Args:
            file1: 第一次测试结果文件（JSON格式）
            file2: 第二次测试结果文件（JSON格式）
            
        Returns:
            对比结果字典
        """
        results1 = self._load_json_results(file1)
        results2 = self._load_json_results(file2)
        
        if not results1 or not results2:
            return {'error': '无法加载测试结果文件'}
        
        # 创建模型状态映射
        status1 = {r['model']: r for r in results1}
        status2 = {r['model']: r for r in results2}
        
        # 分析变化
        all_models = set(status1.keys()) | set(status2.keys())
        
        newly_failed = []  # 新增失败
        recovered = []  # 恢复正常
        still_failed = []  # 持续失败
        still_success = []  # 持续成功
        new_models = []  # 新增模型
        removed_models = []  # 移除的模型
        
        for model in all_models:
            if model in status1 and model in status2:
                s1 = status1[model]['success']
                s2 = status2[model]['success']
                
                if s1 and not s2:
                    newly_failed.append({
                        'model': model,
                        'old_time': status1[model]['response_time'],
                        'new_error': status2[model]['error_code']
                    })
                elif not s1 and s2:
                    recovered.append({
                        'model': model,
                        'old_error': status1[model]['error_code'],
                        'new_time': status2[model]['response_time']
                    })
                elif not s1 and not s2:
                    still_failed.append(model)
                else:
                    still_success.append(model)
            elif model in status2 and model not in status1:
                new_models.append(model)
            else:
                removed_models.append(model)
        
        return {
            'newly_failed': newly_failed,
            'recovered': recovered,
            'still_failed': still_failed,
            'still_success': still_success,
            'new_models': new_models,
            'removed_models': removed_models,
            'summary': {
                'newly_failed_count': len(newly_failed),
                'recovered_count': len(recovered),
                'still_failed_count': len(still_failed),
                'still_success_count': len(still_success)
            }
        }
    
    def calculate_health_score(self, results: List[Dict], weights: Dict = None) -> Dict:
        """
        计算API健康度评分（0-100）
        
        评分维度：
        - 成功率（50%权重）
        - 响应速度（30%权重）
        - 稳定性（20%权重）
        
        Args:
            results: 测试结果列表
            weights: 自定义权重
            
        Returns:
            评分结果字典
        """
        if not results:
            return {'score': 0, 'grade': 'F', 'details': {}}
        
        # 默认权重
        default_weights = {
            'success_rate': 0.5,
            'response_speed': 0.3,
            'stability': 0.2
        }
        weights = weights or default_weights
        
        # 1. 成功率评分（0-100）
        success_count = sum(1 for r in results if r['success'])
        success_rate = success_count / len(results)
        success_score = success_rate * 100
        
        # 2. 响应速度评分（0-100）
        # 目标：< 2秒满分，每增加1秒扣10分
        success_results = [r for r in results if r['success'] and r['response_time'] > 0]
        if success_results:
            avg_response_time = sum(r['response_time'] for r in success_results) / len(success_results)
            speed_score = max(0, 100 - (avg_response_time - 2) * 10)
        else:
            speed_score = 0
        
        # 3. 稳定性评分（0-100）
        # 基于错误分布的均匀程度，错误类型越集中说明问题越明确
        failed_results = [r for r in results if not r['success']]
        if failed_results:
            error_types = {}
            for r in failed_results:
                error_code = r.get('error_code', 'UNKNOWN')
                error_types[error_code] = error_types.get(error_code, 0) + 1
            
            # 如果只有一种错误类型，说明问题明确（较高分）
            # 如果错误类型很多，说明不稳定（较低分）
            max_error_ratio = max(error_types.values()) / len(failed_results)
            stability_score = max_error_ratio * 100
        else:
            stability_score = 100  # 没有失败即完全稳定
        
        # 计算总分
        total_score = (
            success_score * weights['success_rate'] +
            speed_score * weights['response_speed'] +
            stability_score * weights['stability']
        )
        
        # 评级
        if total_score >= 90:
            grade = 'A'
        elif total_score >= 80:
            grade = 'B'
        elif total_score >= 70:
            grade = 'C'
        elif total_score >= 60:
            grade = 'D'
        else:
            grade = 'F'
        
        return {
            'score': round(total_score, 2),
            'grade': grade,
            'details': {
                'success_score': round(success_score, 2),
                'speed_score': round(speed_score, 2),
                'stability_score': round(stability_score, 2),
                'success_rate': round(success_rate * 100, 2),
                'avg_response_time': round(avg_response_time, 2) if success_results else 0,
                'total_models': len(results),
                'success_count': success_count,
                'failed_count': len(results) - success_count
            }
        }
    
    def check_alerts(self, results: List[Dict], thresholds: Dict = None) -> List[Dict]:
        """
        检查是否触发告警
        
        Args:
            results: 测试结果列表
            thresholds: 告警阈值配置
            
        Returns:
            告警列表
        """
        # 默认阈值
        default_thresholds = {
            'min_success_rate': 0.5,  # 最低成功率50%
            'max_avg_response_time': 5.0,  # 最大平均响应时间5秒
            'max_429_errors': 50,  # 最多429错误50个
            'max_403_errors': 100,  # 最多403错误100个
            'max_timeout_errors': 20  # 最多超时错误20个
        }
        thresholds = thresholds or default_thresholds
        
        alerts = []
        
        if not results:
            return alerts
        
        # 1. 检查成功率
        success_count = sum(1 for r in results if r['success'])
        success_rate = success_count / len(results)
        
        if success_rate < thresholds['min_success_rate']:
            alerts.append({
                'type': 'LOW_SUCCESS_RATE',
                'severity': 'high',
                'message': f"成功率过低: {success_rate:.1%} (阈值: {thresholds['min_success_rate']:.1%})",
                'value': success_rate,
                'threshold': thresholds['min_success_rate']
            })
        
        # 2. 检查平均响应时间
        success_results = [r for r in results if r['success'] and r['response_time'] > 0]
        if success_results:
            avg_response_time = sum(r['response_time'] for r in success_results) / len(success_results)
            
            if avg_response_time > thresholds['max_avg_response_time']:
                alerts.append({
                    'type': 'SLOW_RESPONSE',
                    'severity': 'medium',
                    'message': f"平均响应时间过慢: {avg_response_time:.2f}秒 (阈值: {thresholds['max_avg_response_time']}秒)",
                    'value': avg_response_time,
                    'threshold': thresholds['max_avg_response_time']
                })
        
        # 3. 检查特定错误数量
        error_counts = {}
        for r in results:
            if not r['success'] and r['error_code']:
                error_code = r['error_code']
                error_counts[error_code] = error_counts.get(error_code, 0) + 1
        
        # HTTP_429 速率限制
        if error_counts.get('HTTP_429', 0) > thresholds['max_429_errors']:
            alerts.append({
                'type': 'RATE_LIMIT',
                'severity': 'high',
                'message': f"速率限制错误过多: {error_counts['HTTP_429']}次 (阈值: {thresholds['max_429_errors']})",
                'value': error_counts['HTTP_429'],
                'threshold': thresholds['max_429_errors']
            })
        
        # HTTP_403 权限错误
        if error_counts.get('HTTP_403', 0) > thresholds['max_403_errors']:
            alerts.append({
                'type': 'PERMISSION_DENIED',
                'severity': 'high',
                'message': f"权限错误过多: {error_counts['HTTP_403']}次 (阈值: {thresholds['max_403_errors']})",
                'value': error_counts['HTTP_403'],
                'threshold': thresholds['max_403_errors']
            })
        
        # TIMEOUT 超时错误
        if error_counts.get('TIMEOUT', 0) > thresholds['max_timeout_errors']:
            alerts.append({
                'type': 'TIMEOUT',
                'severity': 'medium',
                'message': f"超时错误过多: {error_counts['TIMEOUT']}次 (阈值: {thresholds['max_timeout_errors']})",
                'value': error_counts['TIMEOUT'],
                'threshold': thresholds['max_timeout_errors']
            })
        
        return alerts
    
    def _load_json_results(self, file_path: str) -> List[Dict]:
        """加载JSON格式的测试结果"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('results', [])
        except Exception as e:
            print(f"加载结果文件失败 {file_path}: {e}")
            return []
    
    def generate_trend_report(self, result_files: List[str]) -> Dict:
        """
        生成趋势报告
        
        Args:
            result_files: 多个测试结果文件路径（按时间顺序）
            
        Returns:
            趋势报告字典
        """
        trends = []
        
        for file_path in result_files:
            results = self._load_json_results(file_path)
            if not results:
                continue
            
            # 计算该次测试的指标
            success_count = sum(1 for r in results if r['success'])
            success_rate = success_count / len(results) if results else 0
            
            success_results = [r for r in results if r['success'] and r['response_time'] > 0]
            avg_response_time = (
                sum(r['response_time'] for r in success_results) / len(success_results)
                if success_results else 0
            )
            
            trends.append({
                'file': Path(file_path).name,
                'total': len(results),
                'success': success_count,
                'failed': len(results) - success_count,
                'success_rate': round(success_rate * 100, 2),
                'avg_response_time': round(avg_response_time, 2)
            })
        
        return {
            'trends': trends,
            'summary': {
                'test_count': len(trends),
                'latest_success_rate': trends[-1]['success_rate'] if trends else 0,
                'avg_success_rate': sum(t['success_rate'] for t in trends) / len(trends) if trends else 0
            }
        }
