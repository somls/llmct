"""测试报告生成器 - 支持多种输出格式"""

import json
import csv
import os
from datetime import datetime
from typing import List, Dict
from pathlib import Path


class Reporter:
    """测试报告生成器"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.test_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    def _get_base_url_safe_name(self) -> str:
        """
        获取base_url的安全文件名
        将URL转换为合法的文件名（移除特殊字符）
        """
        import re
        # 移除协议前缀
        safe_name = self.base_url.replace('https://', '').replace('http://', '')
        # 移除或替换特殊字符
        safe_name = re.sub(r'[^\w\-\.]', '_', safe_name)
        # 移除结尾的下划线
        safe_name = safe_name.strip('_')
        return safe_name
    
    def save_report(self, results: List[Dict], output_file: str, format: str = 'txt', available_models: str = None):
        """
        保存测试报告（按base_url分类保存）

        Args:
            results: 测试结果列表
            output_file: 输出文件路径
            format: 输出格式 (txt/json/csv/html)
            available_models: 可用模型列表（逗号分隔）
        """
        format = format.lower()
        
        # 创建按base_url分类的目录结构
        base_url_name = self._get_base_url_safe_name()
        output_path = Path(output_file)
        
        # 创建 test_results/{base_url}/ 目录
        results_dir = Path('test_results') / base_url_name
        results_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成带时间戳的文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_ext = output_path.suffix or f'.{format}'
        new_filename = f"test_{timestamp}{file_ext}"
        new_output_file = results_dir / new_filename
        
        if format == 'json':
            self.save_json(results, str(new_output_file), available_models)
        elif format == 'csv':
            self.save_csv(results, str(new_output_file), available_models)
        elif format == 'html':
            self.save_html(results, str(new_output_file), available_models)
        else:  # 默认txt
            self.save_txt(results, str(new_output_file), available_models)
        
        return str(new_output_file)
    
    def save_txt(self, results: List[Dict], output_file: str, available_models: str = None):
        """保存为TXT格式（表格格式）"""
        from llmct.utils import display_width, pad_string
        from llmct.constants import (
            COL_WIDTH_MODEL, COL_WIDTH_TIME, COL_WIDTH_ERROR, COL_WIDTH_CONTENT,
            TABLE_WIDTH
        )
        
        col_widths = {
            'model': COL_WIDTH_MODEL,
            'time': COL_WIDTH_TIME,
            'error': COL_WIDTH_ERROR,
            'content': COL_WIDTH_CONTENT
        }
        
        total_width = TABLE_WIDTH
        
        from llmct.constants import SEPARATOR_WIDTH
        
        with open(output_file, 'w', encoding='utf-8') as f:
            # 写入文件头
            f.write("="*SEPARATOR_WIDTH + "\n")
            f.write("大模型连通性和可用性测试结果\n")
            f.write(f"Base URL: {self.base_url}\n")
            f.write(f"测试时间: {self.test_time}\n")

            # 添加可用模型列表
            if available_models:
                f.write(f"可用模型: {available_models}\n")

            f.write("="*SEPARATOR_WIDTH + "\n\n")
            
            # 写入表头
            f.write("="*total_width + "\n")
            header = (
                f"{pad_string('模型名称', col_widths['model'], 'left')} | "
                f"{pad_string('响应时间', col_widths['time'], 'center')} | "
                f"{pad_string('错误信息', col_widths['error'], 'center')} | "
                f"{pad_string('响应内容', col_widths['content'], 'left')}"
            )
            f.write(header + "\n")
            f.write("-"*total_width + "\n")
            
            # 写入测试结果
            success_count = 0
            fail_count = 0
            
            for result in results:
                if result['success']:
                    success_count += 1
                else:
                    fail_count += 1
                
                # 格式化行
                model_name = result['model']
                if display_width(model_name) > col_widths['model']:
                    while display_width(model_name) > col_widths['model'] - 3:
                        model_name = model_name[:-1]
                    model_name = model_name + '...'
                
                time_str = f"{result['response_time']:.2f}秒" if result['response_time'] > 0 else '-'
                error_str = result['error_code'] if result['error_code'] else '-'
                content_str = result['content'][:37] + '...' if len(result['content']) > 40 else result['content']
                
                row = (
                    f"{pad_string(model_name, col_widths['model'], 'left')} | "
                    f"{pad_string(time_str, col_widths['time'], 'center')} | "
                    f"{pad_string(error_str, col_widths['error'], 'center')} | "
                    f"{pad_string(content_str, col_widths['content'], 'left')}"
                )
                f.write(row + "\n")
            
            # 写入统计信息
            f.write("="*total_width + "\n")
            success_rate = (success_count/len(results)*100) if results else 0
            f.write(f"测试完成 | 总计: {len(results)} | 成功: {success_count} | 失败: {fail_count} | 成功率: {success_rate:.1f}%\n")
            f.write("="*total_width + "\n")
    
    def save_json(self, results: List[Dict], output_file: str, available_models: str = None):
        """保存为JSON格式"""
        stats = self._generate_statistics(results)
        error_stats = self._generate_error_statistics(results)
        
        data = {
            'metadata': {
                'test_time': self.test_time,
                'base_url': self.base_url,
                'total': len(results),
                'success': stats['success_count'],
                'failed': stats['fail_count'],
                'success_rate': stats['success_rate'],
                'available_models': available_models  # 添加可用模型列表
            },
            'results': results,
            'statistics': {
                'success_count': stats['success_count'],
                'fail_count': stats['fail_count'],
                'success_rate': stats['success_rate'],
                'avg_response_time': stats.get('avg_response_time', 0),
                'error_breakdown': error_stats
            }
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def save_csv(self, results: List[Dict], output_file: str, available_models: str = None):
        """保存为CSV格式"""
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            # 如果有可用模型列表，写入注释行
            if available_models:
                f.write(f"# 可用模型: {available_models}\n")

            fieldnames = ['model', 'success', 'response_time', 'error_code', 'content']
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            writer.writeheader()
            writer.writerows(results)
    
    def save_html(self, results: List[Dict], output_file: str, available_models: str = None):
        """保存为HTML格式"""
        stats = self._generate_statistics(results)
        error_stats = self._generate_error_statistics(results)

        # 生成HTML
        html = self._generate_html_content(results, stats, error_stats, available_models)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
    
    def _generate_statistics(self, results: List[Dict]) -> Dict:
        """生成统计信息"""
        if not results:
            return {
                'success_count': 0,
                'fail_count': 0,
                'success_rate': 0,
                'avg_response_time': 0
            }
        
        success_count = sum(1 for r in results if r['success'])
        fail_count = len(results) - success_count
        success_rate = (success_count / len(results) * 100)
        
        # 计算平均响应时间（只计算成功的）
        success_results = [r for r in results if r['success'] and r['response_time'] > 0]
        avg_response_time = (
            sum(r['response_time'] for r in success_results) / len(success_results)
            if success_results else 0
        )
        
        return {
            'success_count': success_count,
            'fail_count': fail_count,
            'success_rate': success_rate,
            'avg_response_time': avg_response_time
        }
    
    def _generate_error_statistics(self, results: List[Dict]) -> Dict:
        """生成错误统计"""
        error_counts = {}
        
        for result in results:
            if not result['success'] and result['error_code']:
                error_code = result['error_code']
                error_counts[error_code] = error_counts.get(error_code, 0) + 1
        
        # 按数量排序
        sorted_errors = sorted(error_counts.items(), key=lambda x: -x[1])
        
        return dict(sorted_errors)
    
    def _generate_html_content(self, results: List[Dict], stats: Dict, error_stats: Dict, available_models: str = None) -> str:
        """生成HTML内容"""
        # 生成结果表格行
        rows_html = ""
        for result in results:
            status_class = 'success' if result['success'] else 'failed'
            status_text = '✓ 成功' if result['success'] else '✗ 失败'
            response_time = f"{result['response_time']:.2f}秒" if result['response_time'] > 0 else '-'
            error_code = result['error_code'] or '-'
            content = result['content'][:100] + '...' if len(result['content']) > 100 else result['content']
            content = content.replace('<', '&lt;').replace('>', '&gt;')
            
            rows_html += f"""
            <tr>
                <td>{result['model']}</td>
                <td class="{status_class}">{status_text}</td>
                <td>{response_time}</td>
                <td>{error_code}</td>
                <td>{content}</td>
            </tr>
"""
        
        # 生成错误统计表格
        error_rows_html = ""
        for error_code, count in error_stats.items():
            percentage = (count / stats['fail_count'] * 100) if stats['fail_count'] > 0 else 0
            error_rows_html += f"""
            <tr>
                <td>{error_code}</td>
                <td>{count}</td>
                <td>{percentage:.1f}%</td>
            </tr>
"""
        
        # 完整HTML
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>大模型测试报告</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
            background: #f5f7fa;
            padding: 20px;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            padding: 30px;
        }}
        h1 {{
            color: #333;
            margin-bottom: 10px;
            font-size: 28px;
        }}
        .metadata {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            margin: 20px 0;
            font-size: 14px;
            color: #666;
        }}
        .metadata p {{
            margin: 5px 0;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .stat-card.success {{
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        }}
        .stat-card.failed {{
            background: linear-gradient(135deg, #ee0979 0%, #ff6a00 100%);
        }}
        .stat-card .label {{
            font-size: 14px;
            opacity: 0.9;
            margin-bottom: 8px;
        }}
        .stat-card .value {{
            font-size: 32px;
            font-weight: bold;
        }}
        h2 {{
            color: #333;
            margin: 30px 0 15px;
            font-size: 20px;
            border-bottom: 2px solid #667eea;
            padding-bottom: 8px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 14px;
        }}
        th {{
            background: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }}
        td {{
            padding: 10px 12px;
            border-bottom: 1px solid #e9ecef;
        }}
        tr:hover {{
            background: #f8f9fa;
        }}
        .success {{
            color: #28a745;
            font-weight: bold;
        }}
        .failed {{
            color: #dc3545;
            font-weight: bold;
        }}
        .error-table {{
            max-width: 600px;
        }}
        @media print {{
            body {{
                background: white;
                padding: 0;
            }}
            .container {{
                box-shadow: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🧪 大模型连通性测试报告</h1>
        
        <div class="metadata">
            <p><strong>测试时间:</strong> {self.test_time}</p>
            <p><strong>Base URL:</strong> {self.base_url}</p>
            {f'<p><strong>可用模型:</strong> {available_models}</p>' if available_models else ''}
        </div>
        
        <div class="summary">
            <div class="stat-card">
                <div class="label">总测试数</div>
                <div class="value">{len(results)}</div>
            </div>
            <div class="stat-card success">
                <div class="label">成功</div>
                <div class="value">{stats['success_count']}</div>
            </div>
            <div class="stat-card failed">
                <div class="label">失败</div>
                <div class="value">{stats['fail_count']}</div>
            </div>
            <div class="stat-card">
                <div class="label">成功率</div>
                <div class="value">{stats['success_rate']:.1f}%</div>
            </div>
        </div>
        
        <h2>📊 测试结果详情</h2>
        <table>
            <thead>
                <tr>
                    <th>模型名称</th>
                    <th>状态</th>
                    <th>响应时间</th>
                    <th>错误代码</th>
                    <th>响应内容</th>
                </tr>
            </thead>
            <tbody>
{rows_html}
            </tbody>
        </table>
        
        <h2>❌ 错误统计</h2>
        <table class="error-table">
            <thead>
                <tr>
                    <th>错误代码</th>
                    <th>数量</th>
                    <th>占比</th>
                </tr>
            </thead>
            <tbody>
{error_rows_html}
            </tbody>
        </table>
    </div>
</body>
</html>
"""
        return html
