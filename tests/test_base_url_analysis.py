#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试按base_url分析功能"""

import unittest
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from llmct.core.reporter import Reporter
from llmct.core.analyzer import ResultAnalyzer


class TestBaseUrlAnalysis(unittest.TestCase):
    """测试base_url分析功能"""
    
    def setUp(self):
        """设置测试环境"""
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp()
        self.test_results_dir = Path(self.temp_dir)
        
        # 模拟测试结果
        self.test_results_1 = [
            {
                'model': 'gpt-4o',
                'success': True,
                'response_time': 1.2,
                'error_code': '',
                'content': 'Hello!'
            },
            {
                'model': 'gpt-4o-mini',
                'success': True,
                'response_time': 0.8,
                'error_code': '',
                'content': 'Hi!'
            },
            {
                'model': 'gpt-3.5-turbo',
                'success': False,
                'response_time': 0,
                'error_code': 'HTTP_403',
                'content': ''
            }
        ]
        
        self.test_results_2 = [
            {
                'model': 'gpt-4o',
                'success': True,
                'response_time': 1.3,
                'error_code': '',
                'content': 'Hello again!'
            },
            {
                'model': 'gpt-4o-mini',
                'success': False,
                'response_time': 0,
                'error_code': 'TIMEOUT',
                'content': ''
            },
            {
                'model': 'gpt-3.5-turbo',
                'success': True,
                'response_time': 1.1,
                'error_code': '',
                'content': 'Working now!'
            }
        ]
    
    def tearDown(self):
        """清理测试环境"""
        shutil.rmtree(self.temp_dir)
    
    def test_reporter_safe_name(self):
        """测试URL转安全文件名"""
        reporter = Reporter('https://api.openai.com/v1')
        safe_name = reporter._get_base_url_safe_name()
        
        # 不应该包含特殊字符
        self.assertNotIn('/', safe_name)
        self.assertNotIn(':', safe_name)
        self.assertNotIn('https', safe_name)
        
        # 应该包含域名
        self.assertIn('api.openai.com', safe_name)
    
    def test_save_report_creates_directory(self):
        """测试保存报告时创建目录结构"""
        # 切换到临时目录
        import os
        old_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        try:
            reporter = Reporter('https://api.example.com')
            output_file = reporter.save_report(
                self.test_results_1,
                'test_results.json',
                format='json'
            )
            
            # 检查文件是否创建
            self.assertTrue(Path(output_file).exists())
            
            # 检查目录结构
            self.assertTrue(Path('test_results/api.example.com').exists())
            
            # 检查文件名格式（应该包含时间戳）
            self.assertIn('test_', Path(output_file).name)
            self.assertTrue(Path(output_file).name.endswith('.json'))
            
        finally:
            os.chdir(old_cwd)
    
    def test_analyzer_by_base_url(self):
        """测试按base_url分析功能"""
        # 创建测试目录和文件
        base_url_dir = self.test_results_dir / 'api.test.com'
        base_url_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存两次测试结果
        for i, results in enumerate([self.test_results_1, self.test_results_2], 1):
            test_file = base_url_dir / f'test_2025010{i}_120000.json'
            data = {
                'metadata': {
                    'test_start_time': f'2025-01-0{i} 12:00:00',
                    'base_url': 'https://api.test.com'
                },
                'results': results
            }
            with open(test_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        
        # 分析
        analyzer = ResultAnalyzer()
        analysis = analyzer.analyze_by_base_url(str(base_url_dir))
        
        # 验证结果
        self.assertIn('summary', analysis)
        self.assertIn('model_statistics', analysis)
        
        # 验证总体统计
        self.assertEqual(analysis['summary']['total_test_files'], 2)
        self.assertEqual(analysis['summary']['total_models'], 3)
        
        # 验证模型统计
        model_stats = analysis['model_statistics']
        self.assertIn('gpt-4o', model_stats)
        self.assertIn('gpt-4o-mini', model_stats)
        self.assertIn('gpt-3.5-turbo', model_stats)
        
        # 验证 gpt-4o 的统计（两次都成功）
        gpt4o_stats = model_stats['gpt-4o']
        self.assertEqual(gpt4o_stats['total_tests'], 2)
        self.assertEqual(gpt4o_stats['success_tests'], 2)
        self.assertEqual(gpt4o_stats['failed_tests'], 0)
        self.assertEqual(gpt4o_stats['success_rate'], 100.0)
        
        # 验证 gpt-4o-mini 的统计（1成功1失败）
        gpt4o_mini_stats = model_stats['gpt-4o-mini']
        self.assertEqual(gpt4o_mini_stats['total_tests'], 2)
        self.assertEqual(gpt4o_mini_stats['success_tests'], 1)
        self.assertEqual(gpt4o_mini_stats['failed_tests'], 1)
        self.assertEqual(gpt4o_mini_stats['success_rate'], 50.0)
        
        # 验证 gpt-3.5-turbo 的统计（1失败1成功）
        gpt35_stats = model_stats['gpt-3.5-turbo']
        self.assertEqual(gpt35_stats['total_tests'], 2)
        self.assertEqual(gpt35_stats['success_tests'], 1)
        self.assertEqual(gpt35_stats['failed_tests'], 1)
        self.assertEqual(gpt35_stats['success_rate'], 50.0)
    
    def test_get_model_success_rates(self):
        """测试获取模型成功率排名"""
        # 创建测试目录和文件
        base_url_dir = self.test_results_dir / 'api.test.com'
        base_url_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存测试结果
        for i, results in enumerate([self.test_results_1, self.test_results_2], 1):
            test_file = base_url_dir / f'test_2025010{i}_120000.json'
            data = {
                'metadata': {
                    'test_start_time': f'2025-01-0{i} 12:00:00'
                },
                'results': results
            }
            with open(test_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        
        # 获取排名
        analyzer = ResultAnalyzer()
        ranked = analyzer.get_model_success_rates(str(base_url_dir), min_tests=2)
        
        # 验证结果
        self.assertEqual(len(ranked), 3)
        
        # 验证排序（成功率降序）
        self.assertEqual(ranked[0]['model'], 'gpt-4o')
        self.assertEqual(ranked[0]['success_rate'], 100.0)
        
        # 后两个成功率相同（50%），应该按平均响应时间排序
        self.assertTrue(ranked[1]['success_rate'] == 50.0)
        self.assertTrue(ranked[2]['success_rate'] == 50.0)
    
    def test_save_base_url_analysis(self):
        """测试保存分析报告"""
        # 创建测试目录和文件
        base_url_dir = self.test_results_dir / 'api.test.com'
        base_url_dir.mkdir(parents=True, exist_ok=True)
        
        test_file = base_url_dir / 'test_20250101_120000.json'
        data = {
            'metadata': {'test_start_time': '2025-01-01 12:00:00'},
            'results': self.test_results_1
        }
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # 保存分析报告
        analyzer = ResultAnalyzer()
        output_file = analyzer.save_base_url_analysis(str(base_url_dir))
        
        # 验证文件存在
        self.assertTrue(Path(output_file).exists())
        self.assertTrue(output_file.startswith(str(base_url_dir)))
        self.assertIn('analysis_', output_file)
        
        # 验证内容
        with open(output_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        self.assertIn('summary', saved_data)
        self.assertIn('model_statistics', saved_data)


if __name__ == '__main__':
    unittest.main()
