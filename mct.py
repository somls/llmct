#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大模型连通性和可用性测试工具 - 重构版
测试语言模型的响应能力和非语言模型的连通性
使用优化的SQLite缓存和模块化代码
"""

import argparse
import sys
import time
import os
from typing import List, Dict, Tuple
import requests
from datetime import datetime
import unicodedata

# 导入优化模块
from llmct.utils.sqlite_cache import SQLiteCache
from llmct.core.classifier import ModelClassifier
from llmct.core.reporter import Reporter
from llmct.utils.logger import get_logger

logger = get_logger()

# 设置Windows控制台输出编码
if sys.platform == 'win32':
    import codecs
    if hasattr(sys.stdout, 'buffer'):
        # 使用 line_buffering=False 确保立即输出（将在代码中使用 flush）
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


def display_width(text: str) -> int:
    """计算字符串的实际显示宽度（中文字符算2个宽度）"""
    width = 0
    for char in text:
        if unicodedata.east_asian_width(char) in ('F', 'W'):
            width += 2
        else:
            width += 1
    return width


def pad_string(text: str, width: int, align: str = 'left') -> str:
    """根据显示宽度填充字符串"""
    text_width = display_width(text)
    padding = width - text_width
    
    if padding <= 0:
        return text
    
    if align == 'center':
        left_pad = padding // 2
        right_pad = padding - left_pad
        return ' ' * left_pad + text + ' ' * right_pad
    elif align == 'right':
        return ' ' * padding + text
    else:  # left
        return text + ' ' * padding


class ModelTester:
    def __init__(self, api_key: str, base_url: str, timeout: int = 30, 
                 cache_enabled: bool = True, cache_duration: int = 24,
                 request_delay: float = 1.0, max_retries: int = 3):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        
        # 请求头
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        # 使用requests.Session提升性能
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # 使用优化的SQLite缓存（25倍速度提升）
        self.cache = SQLiteCache(
            db_file='test_cache.db',
            cache_duration_hours=cache_duration
        ) if cache_enabled else None
        
        # 使用模型分类器
        self.classifier = ModelClassifier()
        
        # 统计和配置
        self.error_stats = {}  # 错误统计
        self.request_delay = request_delay  # 降低默认延迟到1秒
        self.max_retries = max_retries      # 429错误最大重试次数
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        if self.session:
            self.session.close()
        if self.cache:
            self.cache.flush()  # 刷新缓冲区
    
    def validate_api_credentials(self) -> Tuple[bool, str]:
        """
        预验证API凭证是否有效
        
        Returns:
            (是否有效, 错误消息或成功消息)
        """
        try:
            url = f"{self.base_url}/v1/models"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 401:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', {}).get('message', '认证失败')
                    return False, f"API认证失败: {error_msg}"
                except:
                    return False, "API认证失败: 401 Unauthorized"
            elif response.status_code == 200:
                data = response.json()
                model_count = len(data.get('data', []))
                return True, f"API认证成功，发现 {model_count} 个模型"
            else:
                return False, f"API响应异常: HTTP {response.status_code}"
        except requests.exceptions.Timeout:
            return False, "连接超时，请检查网络或Base URL是否正确"
        except requests.exceptions.ConnectionError:
            return False, "无法连接到API服务器，请检查Base URL"
        except Exception as e:
            return False, f"连接失败: {str(e)}"
    
    def _parse_http_error(self, response: requests.Response) -> Tuple[str, str]:
        """
        解析 HTTP 错误响应
        
        Args:
            response: Response 对象
            
        Returns:
            (错误代码, 错误消息)
        """
        error_code = f'HTTP_{response.status_code}'
        error_msg = ''
        
        try:
            error_data = response.json()
            if 'error' in error_data:
                if isinstance(error_data['error'], dict):
                    error_msg = error_data['error'].get('message', '')
                else:
                    error_msg = str(error_data['error'])
            else:
                error_msg = str(error_data)[:200]
        except:
            error_msg = response.text[:200] if response.text else ''
        
        return error_code, error_msg
    
    def _make_request_with_retry(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        发送HTTP请求，自动处理429错误重试（指数退避）
        
        Args:
            method: HTTP方法 ('GET', 'POST', 等)
            url: 请求URL
            **kwargs: requests库的其他参数
            
        Returns:
            Response对象
            
        Raises:
            requests.exceptions.RequestException: 请求失败
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                # 从 kwargs 中获取 timeout，如果没有则使用默认值
                timeout = kwargs.pop('timeout', self.timeout)
                
                # 发送请求（使用Session连接复用）
                if method.upper() == 'GET':
                    response = self.session.get(url, timeout=timeout, **kwargs)
                elif method.upper() == 'POST':
                    response = self.session.post(url, timeout=timeout, **kwargs)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                # 如果是429错误且还有重试次数，则重试
                if response.status_code == 429 and attempt < self.max_retries:
                    # 指数退避：2^attempt 秒
                    wait_time = 2 ** attempt
                    
                    # 尝试从响应头获取建议的等待时间
                    retry_after = response.headers.get('Retry-After')
                    if retry_after:
                        try:
                            wait_time = int(retry_after)
                        except ValueError:
                            pass
                    
                    logger.warning(f"速率限制: 收到429错误，等待{wait_time}秒后重试 (第{attempt + 1}次重试)")
                    time.sleep(wait_time)
                    logger.info("重试继续")
                    continue
                
                # 其他错误或成功，直接返回
                response.raise_for_status()
                return response
                
            except requests.exceptions.HTTPError as e:
                # 非429的HTTP错误，直接抛出
                if e.response.status_code != 429:
                    raise
                last_exception = e
            except requests.exceptions.RequestException as e:
                last_exception = e
                if attempt < self.max_retries:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                else:
                    raise
        
        # 所有重试都失败了
        if last_exception:
            raise last_exception
        else:
            raise requests.exceptions.RequestException("All retries failed")
    
    def get_models(self) -> List[Dict]:
        """获取模型列表（改进版：先验证凭证）"""
        # 先验证API凭证
        valid, msg = self.validate_api_credentials()
        if not valid:
            logger.error(f"API凭证验证失败: {msg}")
            print(f"\n{'='*110}")
            print(f"[严重错误] {msg}")
            print(f"{'='*110}")
            print("\n可能的原因:")
            print("  1. API密钥已过期")
            print("  2. API密钥格式错误")
            print("  3. Base URL配置错误")
            print("  4. 网络连接问题")
            print("\n请检查您的API配置后重试。")
            print("\n提示: 访问您的API提供商网站获取有效的API密钥")
            print(f"{'='*110}\n")
            sys.exit(1)
        
        logger.info(msg)
        print(f"[信息] {msg}\n")
        sys.stdout.flush()
        
        try:
            url = f"{self.base_url}/v1/models"
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            if 'data' in data:
                return data['data']
            else:
                return []
        except Exception as e:
            logger.error(f"获取模型列表失败: {e}")
            print(f"[错误] 获取模型列表失败: {e}")
            sys.stdout.flush()
            return []
    
    def classify_model(self, model_id: str) -> str:
        """
        分类模型类型（使用ModelClassifier）
        返回: 'language', 'vision', 'audio', 'embedding', 'image_generation', 'moderation', 'other'
        """
        return self.classifier.classify(model_id)
    
    def test_language_model(self, model_id: str, test_message: str = "hello") -> Tuple[bool, float, str, str]:
        """测试语言模型，返回(是否成功, 响应时间, 错误代码, 响应内容)"""
        try:
            url = f"{self.base_url}/v1/chat/completions"
            payload = {
                "model": model_id,
                "messages": [
                    {"role": "user", "content": test_message}
                ],
                "max_tokens": 100,
                "temperature": 0.7
            }
            
            start_time = time.time()
            response = self._make_request_with_retry(
                'POST',
                url, 
                headers=self.headers, 
                json=payload, 
                timeout=self.timeout
            )
            response_time = time.time() - start_time
            
            data = response.json()
            
            if 'choices' in data and len(data['choices']) > 0:
                content = data['choices'][0].get('message', {}).get('content', '')
                return True, response_time, '', content.strip()
            else:
                return False, response_time, 'NO_CONTENT', ''
                
        except requests.exceptions.Timeout:
            return False, self.timeout, 'TIMEOUT', ''
        except requests.exceptions.HTTPError as e:
            if hasattr(e, 'response') and e.response is not None:
                error_code, error_msg = self._parse_http_error(e.response)
                return False, 0, error_code, error_msg
            else:
                return False, 0, 'HTTP_ERROR', str(e)[:200]
        except requests.exceptions.RequestException as e:
            return False, 0, 'REQUEST_FAILED', str(e)[:200]
        except Exception as e:
            logger.error(f"测试时发生未知错误: {type(e).__name__}: {e}")
            return False, 0, 'UNKNOWN_ERROR', str(e)[:200]
    
    def test_vision_model(self, model_id: str, test_message: str = "What's in this image?", 
                          image_url: str = "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/320px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg") -> Tuple[bool, float, str, str]:
        """测试视觉模型，返回(是否成功, 响应时间, 错误代码, 响应内容)"""
        try:
            url = f"{self.base_url}/v1/chat/completions"
            payload = {
                "model": model_id,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": test_message},
                            {"type": "image_url", "image_url": {"url": image_url}}
                        ]
                    }
                ],
                "max_tokens": 100
            }
            
            start_time = time.time()
            response = self._make_request_with_retry(
                'POST',
                url, 
                headers=self.headers, 
                json=payload, 
                timeout=self.timeout
            )
            response_time = time.time() - start_time
            
            data = response.json()
            
            if 'choices' in data and len(data['choices']) > 0:
                content = data['choices'][0].get('message', {}).get('content', '')
                return True, response_time, '', content.strip()
            else:
                return False, response_time, 'NO_CONTENT', ''
                
        except requests.exceptions.Timeout:
            return False, self.timeout, 'TIMEOUT', ''
        except requests.exceptions.HTTPError as e:
            if hasattr(e, 'response') and e.response is not None:
                error_code, error_msg = self._parse_http_error(e.response)
                return False, 0, error_code, error_msg
            else:
                return False, 0, 'HTTP_ERROR', str(e)[:200]
        except requests.exceptions.RequestException as e:
            return False, 0, 'REQUEST_FAILED', str(e)[:200]
        except Exception as e:
            logger.error(f"测试时发生未知错误: {type(e).__name__}: {e}")
            return False, 0, 'UNKNOWN_ERROR', str(e)[:200]
    
    def test_audio_model(self, model_id: str) -> Tuple[bool, float, str, str]:
        """测试音频模型（Whisper/TTS），返回(是否成功, 响应时间, 错误代码, 响应内容)"""
        # 对于音频模型，使用HEAD请求检查端点是否存在
        try:
            # 先尝试ASR端点
            url = f"{self.base_url}/v1/audio/transcriptions"
            start_time = time.time()
            response = requests.options(url, headers=self.headers, timeout=self.timeout)
            response_time = time.time() - start_time
            
            if response.status_code in [200, 405]:  # 405表示方法不允许，但端点存在
                return True, response_time, '', '音频端点可用'
            else:
                # 尝试TTS端点
                url = f"{self.base_url}/v1/audio/speech"
                response = requests.options(url, headers=self.headers, timeout=self.timeout)
                if response.status_code in [200, 405]:
                    return True, response_time, '', 'TTS端点可用'
                return False, response_time, f'HTTP_{response.status_code}', ''
        except requests.exceptions.Timeout:
            return False, self.timeout, 'TIMEOUT', ''
        except requests.exceptions.HTTPError as e:
            if hasattr(e, 'response') and e.response is not None:
                error_code, error_msg = self._parse_http_error(e.response)
                return False, 0, error_code, error_msg
            else:
                return False, 0, 'HTTP_ERROR', str(e)[:200]
        except requests.exceptions.RequestException as e:
            return False, 0, 'CONN_FAILED', str(e)[:200]
        except Exception as e:
            logger.error(f"测试时发生未知错误: {type(e).__name__}: {e}")
            return False, 0, 'UNKNOWN_ERROR', str(e)[:200]
    
    def test_embedding_model(self, model_id: str, test_text: str = "hello world") -> Tuple[bool, float, str, str]:
        """测试Embedding模型，返回(是否成功, 响应时间, 错误代码, 响应内容)"""
        try:
            url = f"{self.base_url}/v1/embeddings"
            payload = {
                "model": model_id,
                "input": test_text
            }
            
            start_time = time.time()
            response = self._make_request_with_retry(
                'POST',
                url, 
                headers=self.headers, 
                json=payload, 
                timeout=self.timeout
            )
            response_time = time.time() - start_time
            
            data = response.json()
            
            if 'data' in data and len(data['data']) > 0:
                embedding_dim = len(data['data'][0].get('embedding', []))
                return True, response_time, '', f'Embedding维度:{embedding_dim}'
            else:
                return False, response_time, 'NO_DATA', ''
                
        except requests.exceptions.Timeout:
            return False, self.timeout, 'TIMEOUT', ''
        except requests.exceptions.HTTPError as e:
            if hasattr(e, 'response') and e.response is not None:
                error_code, error_msg = self._parse_http_error(e.response)
                return False, 0, error_code, error_msg
            else:
                return False, 0, 'HTTP_ERROR', str(e)[:200]
        except requests.exceptions.RequestException as e:
            return False, 0, 'REQUEST_FAILED', str(e)[:200]
        except Exception as e:
            logger.error(f"测试时发生未知错误: {type(e).__name__}: {e}")
            return False, 0, 'UNKNOWN_ERROR', str(e)[:200]
    
    def test_image_generation_model(self, model_id: str, prompt: str = "a white cat") -> Tuple[bool, float, str, str]:
        """测试图像生成模型，返回(是否成功, 响应时间, 错误代码, 响应内容)"""
        try:
            url = f"{self.base_url}/v1/images/generations"
            payload = {
                "model": model_id,
                "prompt": prompt,
                "n": 1,
                "size": "256x256"
            }
            
            start_time = time.time()
            response = self._make_request_with_retry(
                'POST',
                url, 
                headers=self.headers, 
                json=payload, 
                timeout=self.timeout
            )
            response_time = time.time() - start_time
            
            data = response.json()
            
            if 'data' in data and len(data['data']) > 0:
                return True, response_time, '', '图像生成成功'
            else:
                return False, response_time, 'NO_DATA', ''
                
        except requests.exceptions.Timeout:
            return False, self.timeout, 'TIMEOUT', ''
        except requests.exceptions.HTTPError as e:
            if hasattr(e, 'response') and e.response is not None:
                error_code, error_msg = self._parse_http_error(e.response)
                return False, 0, error_code, error_msg
            else:
                return False, 0, 'HTTP_ERROR', str(e)[:200]
        except requests.exceptions.RequestException as e:
            return False, 0, 'REQUEST_FAILED', str(e)[:200]
        except Exception as e:
            logger.error(f"测试时发生未知错误: {type(e).__name__}: {e}")
            return False, 0, 'UNKNOWN_ERROR', str(e)[:200]
    
    def test_connectivity(self, model_id: str) -> Tuple[bool, float, str, str]:
        """测试基础连通性，返回(是否成功, 响应时间, 错误代码, 响应内容)"""
        try:
            url = f"{self.base_url}/v1/models/{model_id}"
            
            start_time = time.time()
            response = self._make_request_with_retry(
                'GET',
                url, 
                headers=self.headers, 
                timeout=self.timeout
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                return True, response_time, '', '连接成功'
            else:
                return False, response_time, f'HTTP_{response.status_code}', ''
                
        except requests.exceptions.Timeout:
            return False, self.timeout, 'TIMEOUT', ''
        except requests.exceptions.HTTPError as e:
            if hasattr(e, 'response') and e.response is not None:
                error_code, error_msg = self._parse_http_error(e.response)
                return False, 0, error_code, error_msg
            else:
                return False, 0, 'HTTP_ERROR', str(e)[:200]
        except requests.exceptions.RequestException as e:
            return False, 0, 'CONN_FAILED', str(e)[:200]
        except Exception as e:
            logger.error(f"测试时发生未知错误: {type(e).__name__}: {e}")
            return False, 0, 'UNKNOWN_ERROR', str(e)[:200]
    
    def categorize_error(self, error_code: str) -> str:
        """错误分类"""
        error_categories = {
            'HTTP_403': '权限拒绝/未授权',
            'HTTP_400': '请求参数错误',
            'HTTP_429': '速率限制',
            'HTTP_404': '模型不存在',
            'HTTP_500': '服务器内部错误',
            'HTTP_503': '服务不可用',
            'HTTP_554': '服务器错误',
            'TIMEOUT': '请求超时',
            'NO_CONTENT': '无响应内容',
            'REQUEST_FAILED': '请求失败',
            'CONN_FAILED': '连接失败',
            'UNKNOWN_ERROR': '未知错误',
            'SKIPPED': '跳过测试(失败次数过多)'
        }
        return error_categories.get(error_code, '其他错误')
    
    def update_error_stats(self, error_code: str):
        """更新错误统计"""
        if error_code:
            category = self.categorize_error(error_code)
            self.error_stats[error_code] = self.error_stats.get(error_code, {
                'count': 0,
                'category': category
            })
            self.error_stats[error_code]['count'] += 1
    
    def print_error_statistics(self, total_models: int, success_count: int):
        """打印错误统计信息"""
        if not self.error_stats:
            return
        
        fail_count = total_models - success_count
        print(f"\n{'='*110}")
        print("错误统计和分析")
        print(f"{'='*110}")
        
        # 按错误数量排序
        sorted_errors = sorted(self.error_stats.items(), key=lambda x: -x[1]['count'])
        
        print(f"\n{'错误类型':<20} {'错误描述':<25} {'数量':<10} {'占失败比例':<15} {'占总数比例':<15}")
        print(f"{'-'*110}")
        
        for error_code, info in sorted_errors:
            count = info['count']
            category = info['category']
            fail_rate = (count / fail_count * 100) if fail_count > 0 else 0
            total_rate = (count / total_models * 100) if total_models > 0 else 0
            print(f"{error_code:<20} {category:<25} {count:<10} {fail_rate:>6.1f}%{' '*8} {total_rate:>6.1f}%")
        
        print(f"\n{'总失败数':<20} {' '*25} {fail_count:<10} {100.0:>6.1f}%{' '*8} {(fail_count/total_models*100):>6.1f}%")
        print(f"{'='*110}\n")
    
    def print_failure_statistics(self, threshold: int = 3):
        """打印持续失败模型统计"""
        if not self.cache:
            return
        
        persistent = self.cache.get_persistent_failures(threshold)
        if not persistent:
            return
        
        print(f"\n{'='*110}")
        print(f"持续失败模型统计 (失败{threshold}次以上)")
        print(f"{'='*110}")
        
        print(f"\n{'模型ID':<50} {'失败次数':<12} {'最后错误':<20} {'最后失败时间':<25}")
        print(f"{'-'*110}")
        
        for item in persistent:
            model_id = item['model_id']
            if len(model_id) > 48:
                model_id = model_id[:45] + '...'
            
            last_failure = item['last_failure']
            try:
                # 格式化时间显示
                dt = datetime.fromisoformat(last_failure)
                last_failure_str = dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                last_failure_str = last_failure[:25] if last_failure else '-'
            
            print(f"{model_id:<50} {item['failure_count']:<12} {item['last_error']:<20} {last_failure_str:<25}")
        
        print(f"\n总计持续失败模型: {len(persistent)}")
        print(f"{'='*110}\n")
    
    def format_row(self, model_name: str, success: bool, response_time: float, 
                   error_code: str, content: str, col_widths: dict) -> str:
        """格式化输出行"""
        # 截断过长的字符串
        if display_width(model_name) > col_widths['model']:
            while display_width(model_name) > col_widths['model'] - 3:
                model_name = model_name[:-1]
            model_name = model_name + '...'
        
        if response_time > 0:
            time_str = f"{response_time:.2f}秒"
        else:
            time_str = '-'
        
        error_str = error_code if error_code else '-'
        if display_width(error_str) > col_widths['error']:
            while display_width(error_str) > col_widths['error'] - 3:
                error_str = error_str[:-1]
            error_str = error_str + '...'
        
        content_str = content if content else '-'
        content_str = content_str.replace('\n', ' ').replace('\r', ' ')
        if display_width(content_str) > col_widths['content']:
            while display_width(content_str) > col_widths['content'] - 3:
                content_str = content_str[:-1]
            content_str = content_str + '...'
        
        # 使用自定义填充函数进行对齐
        row = (
            f"{pad_string(model_name, col_widths['model'], 'left')} | "
            f"{pad_string(time_str, col_widths['time'], 'center')} | "
            f"{pad_string(error_str, col_widths['error'], 'center')} | "
            f"{pad_string(content_str, col_widths['content'], 'left')}"
        )
        return row
    
    def save_results(self, results: List[Dict], output_file: str, test_start_time: str):
        """保存测试结果到文件（使用Reporter）"""
        try:
            # 确定输出格式
            if output_file.endswith('.json'):
                format_type = 'json'
            elif output_file.endswith('.csv'):
                format_type = 'csv'
            elif output_file.endswith('.html'):
                format_type = 'html'
            else:
                format_type = 'txt'
            
            # 准备元数据
            success_count = sum(1 for r in results if r['success'])
            fail_count = len(results) - success_count
            success_rate = (success_count / len(results) * 100) if results else 0
            
            metadata = {
                'base_url': self.base_url,
                'test_start_time': test_start_time,
                'test_end_time': datetime.now().isoformat(),
                'total': len(results),
                'success': success_count,
                'failed': fail_count,
                'success_rate': success_rate
            }
            
            # 使用Reporter生成报告
            reporter = Reporter(self.base_url)
            reporter.save_report(results, output_file, format=format_type)
            
            logger.info(f"测试结果已保存到: {output_file} (格式: {format_type})")
            print(f"[信息] 测试结果已保存到: {output_file}")
        except Exception as e:
            logger.warning(f"保存结果失败: {e}")
            print(f"[警告] 保存结果失败: {e}")
    
    def test_all_models(self, test_message: str = "hello", output_file: str = None, 
                        test_vision: bool = True, test_audio: bool = True, 
                        test_embedding: bool = True, test_image_gen: bool = True,
                        only_failed: bool = False, max_failures: int = 0):
        """
        测试所有模型
        
        Args:
            test_message: 用于语言模型的测试消息
            output_file: 结果输出文件路径
            test_vision: 是否测试视觉模型（需要实际API调用）
            test_audio: 是否测试音频模型（需要实际API调用）
            test_embedding: 是否测试Embedding模型（需要实际API调用）
            test_image_gen: 是否测试图像生成模型（需要实际API调用）
            only_failed: 是否只测试上次失败的模型
            max_failures: 失败次数阈值，超过此值的模型将被跳过(0表示不限制)
        """
        test_start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        header_width = 110
        print(f"\n{'='*header_width}")
        print(f"大模型连通性和可用性测试 [增强版]")
        print(f"Base URL: {self.base_url}")
        print(f"测试时间: {test_start_time}")
        print(f"测试配置: 视觉={test_vision}, 音频={test_audio}, 嵌入={test_embedding}, 图像生成={test_image_gen}")
        
        # 显示缓存状态
        if self.cache:
            cache_stats = self.cache.get_stats()
            cached_models = cache_stats['total']
            valid_cache = cache_stats['success_count']
            cache_hours = int(self.cache.cache_duration.total_seconds() // 3600)
            print(f"缓存状态: 启用 (有效记录: {valid_cache}/{cached_models}, 有效期: {cache_hours}小时)")
        else:
            print(f"缓存状态: 禁用")
        
        print(f"{'='*header_width}\n")
        sys.stdout.flush()
        
        print("正在获取模型列表...")
        sys.stdout.flush()
        all_models = self.get_models()
        
        if not all_models:
            print("[错误] 未获取到任何模型，请检查API配置")
            sys.stdout.flush()
            return
        
        # 过滤模型列表
        if only_failed and self.cache:
            # 只测试上次失败的模型
            failed_model_ids = set(self.cache.get_failed_models())
            models = [m for m in all_models if m.get('id', m.get('model', '')) in failed_model_ids]
            print(f"共发现 {len(all_models)} 个模型，筛选出 {len(models)} 个失败模型进行测试")
            print(f"测试模式: 仅测试失败模型")
            sys.stdout.flush()
            
            # 检查是否有失败模型
            if len(models) == 0:
                print("\n[提示] 没有找到失败的模型！")
                print("可能的原因：")
                print("  1. 这是首次运行，尚未建立测试记录")
                print("  2. 所有模型都测试成功了")
                print("  3. 缓存已被清除")
                print("\n建议：")
                print("  - 先运行一次全量测试：python test_models.py --api-key xxx --base-url xxx")
                print("  - 或者移除 --only-failed 参数")
                return
        else:
            models = all_models
            print(f"共发现 {len(models)} 个模型")
            print(f"测试模式: 全量测试")
            sys.stdout.flush()
        
        if max_failures > 0:
            print(f"失败阈值: 跳过失败{max_failures}次以上的模型")
        
        print()
        
        # 定义列宽（紧凑模式）
        col_widths = {
            'model': 45,
            'time': 9,
            'error': 12,
            'content': 40
        }
        
        total_width = sum(col_widths.values()) + 6  # 6 = 3个分隔符 " | " 的宽度
        
        # 打印表头
        print(f"{'='*total_width}")
        header = (
            f"{pad_string('模型名称', col_widths['model'], 'left')} | "
            f"{pad_string('响应时间', col_widths['time'], 'center')} | "
            f"{pad_string('错误信息', col_widths['error'], 'center')} | "
            f"{pad_string('响应内容', col_widths['content'], 'left')}"
        )
        print(header)
        print(f"{'-'*total_width}")
        sys.stdout.flush()
        
        success_count = 0
        fail_count = 0
        cached_count = 0
        skipped_count = 0
        results = []
        
        # 边测试边输出
        for idx, model in enumerate(models, 1):
            model_id = model.get('id', model.get('model', 'unknown'))
            
            # 检查是否超过失败阈值
            if max_failures > 0 and self.cache:
                failure_count = self.cache.get_failure_count(model_id)
                if failure_count >= max_failures:
                    # 跳过该模型
                    skipped_count += 1
                    results.append({
                        'model': model_id,
                        'success': False,
                        'response_time': 0,
                        'error_code': 'SKIPPED',
                        'content': f'已跳过(失败{failure_count}次)'
                    })
                    # 输出跳过信息
                    row = self.format_row(model_id, False, 0, 'SKIPPED', 
                                         f'已跳过(失败{failure_count}次)', col_widths)
                    print(row)
                    continue
            
            # 检查缓存
            if self.cache and self.cache.is_cached(model_id):
                cached_result = self.cache.get_cached_result(model_id)
                success = cached_result['success']
                response_time = cached_result['response_time']
                error_code = cached_result.get('error_code', '')
                content = f"[缓存] {cached_result['content']}"
                cached_count += 1
            else:
                # 分类模型并使用对应的测试方法
                model_type = self.classify_model(model_id)
                
                if model_type == 'language':
                    success, response_time, error_code, content = self.test_language_model(model_id, test_message)
                elif model_type == 'vision' and test_vision:
                    success, response_time, error_code, content = self.test_vision_model(model_id)
                elif model_type == 'audio' and test_audio:
                    success, response_time, error_code, content = self.test_audio_model(model_id)
                elif model_type == 'embedding' and test_embedding:
                    success, response_time, error_code, content = self.test_embedding_model(model_id)
                elif model_type == 'image_generation' and test_image_gen:
                    success, response_time, error_code, content = self.test_image_generation_model(model_id)
                else:
                    # 跳过或使用基础连通性测试
                    if model_type in ['vision', 'audio', 'embedding', 'image_generation']:
                        # 如果禁用了该类型的测试，使用简单连通性测试
                        success, response_time, error_code, content = self.test_connectivity(model_id)
                        if success:
                            content = f'[{model_type}模型] {content}'
                    else:
                        # 其他类型使用基础连通性测试
                        success, response_time, error_code, content = self.test_connectivity(model_id)
                
                # 更新缓存
                if self.cache:
                    self.cache.update_cache(model_id, success, response_time, error_code, content)
            
            # 更新错误统计（跳过的模型不计入错误统计）
            if not success and error_code != 'SKIPPED':
                self.update_error_stats(error_code)
            
            if success:
                success_count += 1
            else:
                fail_count += 1
            
            # 保存结果到列表
            results.append({
                'model': model_id,
                'success': success,
                'response_time': response_time,
                'error_code': error_code,
                'content': content
            })
            
            # 立即输出当前测试结果
            row = self.format_row(model_id, success, response_time, error_code, content, col_widths)
            print(row)
            sys.stdout.flush()  # 强制刷新输出缓冲区，确保实时显示
            
            # 添加请求之间的延迟，避免触发速率限制
            if idx < len(models) and self.request_delay > 0:
                time.sleep(self.request_delay)
        
        # 打印统计信息
        print(f"{'='*total_width}")
        cache_info = f" | 缓存命中: {cached_count}" if cached_count > 0 else ""
        skip_info = f" | 跳过: {skipped_count}" if skipped_count > 0 else ""
        success_rate = (success_count/len(models)*100) if len(models) > 0 else 0
        print(f"测试完成 | 总计: {len(models)} | 成功: {success_count} | 失败: {fail_count}{cache_info}{skip_info} | 成功率: {success_rate:.1f}%")
        print(f"{'='*total_width}\n")
        sys.stdout.flush()
        
        # 打印错误统计
        self.print_error_statistics(len(models), success_count)
        
        # 打印持续失败模型统计
        if self.cache and not only_failed:
            # 只在全量测试时显示持续失败统计
            self.print_failure_statistics(threshold=3)
        
        # 保存缓存
        if self.cache:
            self.cache.flush()
            failed_models = len(self.cache.get_failed_models())
            persistent_failures = len(self.cache.get_persistent_failures(3))
            cache_stats = self.cache.get_stats()
            logger.info(f"缓存已保存: {cache_stats['total']} 条记录")
            logger.info(f"失败模型: {failed_models} 个，持续失败(≥3次): {persistent_failures} 个")
            print(f"[信息] 缓存已保存 (共 {cache_stats['total']} 条记录)")
            print(f"[信息] 失败模型: {failed_models} 个，持续失败(≥3次): {persistent_failures} 个\n")
        
        # 保存结果到文件
        if output_file:
            self.save_results(results, output_file, test_start_time)


def main():
    parser = argparse.ArgumentParser(
        description='大模型连通性和可用性测试工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 基础测试（全量）
  python mct.py --api-key sk-xxx --base-url https://api.openai.com
  
  # [NEW] 仅测试上次失败的模型
  python mct.py --api-key sk-xxx --base-url https://api.openai.com --only-failed
  
  # [NEW] 跳过失败5次以上的模型
  python mct.py --api-key sk-xxx --base-url https://api.openai.com --max-failures 5
  
  # [NEW] 组合使用：只测试失败模型，跳过失败3次以上的
  python mct.py --api-key sk-xxx --base-url https://api.openai.com --only-failed --max-failures 3
  
  # [NEW] 重置失败计数
  python mct.py --api-key sk-xxx --base-url https://api.openai.com --reset-failures
  
  # 自定义测试消息
  python mct.py --api-key sk-xxx --base-url https://api.openai.com --message "你好"
  
  # 禁用缓存
  python mct.py --api-key sk-xxx --base-url https://api.openai.com --no-cache
  
  # 自定义缓存有效期（48小时）
  python mct.py --api-key sk-xxx --base-url https://api.openai.com --cache-duration 48
  
  # 清除缓存后重新测试
  python mct.py --api-key sk-xxx --base-url https://api.openai.com --clear-cache
  
  # 保存结果到文件
  python mct.py --api-key sk-xxx --base-url https://api.openai.com --output my_results.txt
        """
    )
    
    parser.add_argument(
        '--api-key',
        required=True,
        help='API密钥'
    )
    
    parser.add_argument(
        '--base-url',
        required=True,
        help='API基础URL (例如: https://api.openai.com)'
    )
    
    parser.add_argument(
        '--message',
        default='hello',
        help='用于测试语言模型的消息 (默认: hello)'
    )
    
    parser.add_argument(
        '--timeout',
        type=int,
        default=30,
        help='请求超时时间(秒) (默认: 30)'
    )
    
    parser.add_argument(
        '--request-delay',
        type=float,
        default=10.0,
        help='请求之间的延迟(秒)，避免速率限制 (默认: 10.0)'
    )
    
    parser.add_argument(
        '--max-retries',
        type=int,
        default=3,
        help='遇到429错误时的最大重试次数 (默认: 3)'
    )
    
    parser.add_argument(
        '--output',
        '-o',
        default='test_results.txt',
        help='测试结果输出文件路径 (默认: test_results.txt)'
    )
    
    parser.add_argument(
        '--skip-vision',
        action='store_true',
        help='跳过视觉模型的实际测试（仅连通性测试）'
    )
    
    parser.add_argument(
        '--skip-audio',
        action='store_true',
        help='跳过音频模型的实际测试（仅连通性测试）'
    )
    
    parser.add_argument(
        '--skip-embedding',
        action='store_true',
        help='跳过Embedding模型的实际测试（仅连通性测试）'
    )
    
    parser.add_argument(
        '--skip-image-gen',
        action='store_true',
        help='跳过图像生成模型的实际测试（仅连通性测试）'
    )
    
    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='禁用缓存机制'
    )
    
    parser.add_argument(
        '--cache-duration',
        type=int,
        default=24,
        help='缓存有效期（小时），默认24小时'
    )
    
    parser.add_argument(
        '--clear-cache',
        action='store_true',
        help='清除缓存文件后开始测试'
    )
    
    parser.add_argument(
        '--only-failed',
        action='store_true',
        help='仅测试上次失败的模型'
    )
    
    parser.add_argument(
        '--max-failures',
        type=int,
        default=0,
        help='失败次数阈值，超过此值的模型将被跳过(0表示不限制)'
    )
    
    parser.add_argument(
        '--reset-failures',
        action='store_true',
        help='重置所有失败计数'
    )
    
    args = parser.parse_args()
    
    # 清除缓存
    if args.clear_cache:
        cache_file = 'test_cache.json'
        if os.path.exists(cache_file):
            os.remove(cache_file)
            print(f"[信息] 缓存文件已清除\n")
    
    try:
        tester = ModelTester(
            api_key=args.api_key,
            base_url=args.base_url,
            timeout=args.timeout,
            cache_enabled=not args.no_cache,
            cache_duration=args.cache_duration,
            request_delay=args.request_delay,
            max_retries=args.max_retries
        )
        
        # 重置失败计数
        if args.reset_failures and tester.cache:
            tester.cache.reset_failure_counts()
            tester.cache.flush()
            print(f"[信息] 失败计数已重置\n")
        
        tester.test_all_models(
            test_message=args.message, 
            output_file=args.output,
            test_vision=not args.skip_vision,
            test_audio=not args.skip_audio,
            test_embedding=not args.skip_embedding,
            test_image_gen=not args.skip_image_gen,
            only_failed=args.only_failed,
            max_failures=args.max_failures
        )
    except KeyboardInterrupt:
        print("\n\n测试已取消")
        sys.exit(0)
    except Exception as e:
        print(f"\n[错误] 程序异常: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
