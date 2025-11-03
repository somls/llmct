#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大模型连通性和可用性测试工具
测试语言模型的响应能力和非语言模型的连通性
移除缓存功能，专注于实时测试和自动分析
"""

import argparse
import sys
import time
import os
from typing import List, Dict, Tuple
import requests
from datetime import datetime

# 导入优化模块
from llmct.core.classifier import ModelClassifier
from llmct.core.reporter import Reporter
from llmct.core.analyzer import ResultAnalyzer
from llmct.utils.logger import get_logger
from llmct.utils import display_width, pad_string, truncate_string
from llmct.constants import (
    COL_WIDTH_MODEL, COL_WIDTH_TIME, COL_WIDTH_ERROR, COL_WIDTH_CONTENT,
    COL_WIDTH_API_NAME, TABLE_WIDTH, TABLE_WIDTH_MULTI_API,
    SEPARATOR_WIDTH, SEPARATOR_WIDTH_MULTI_API,
    DEFAULT_TEST_MESSAGE, DEFAULT_TIMEOUT, DEFAULT_REQUEST_DELAY,
    DEFAULT_MAX_RETRIES, DEFAULT_OUTPUT_FILE, DEFAULT_API_CONCURRENT,
    DEFAULT_TEST_IMAGE_URL, DEFAULT_VISION_MESSAGE,
    DEFAULT_IMAGE_GEN_PROMPT, DEFAULT_EMBEDDING_TEXT,
    API_ENDPOINT_MODELS, API_ENDPOINT_CHAT, API_ENDPOINT_EMBEDDINGS,
    API_ENDPOINT_IMAGES, API_ENDPOINT_AUDIO_TRANSCRIPTIONS, API_ENDPOINT_AUDIO_SPEECH,
    ERROR_CATEGORIES, HTTP_OK, HTTP_UNAUTHORIZED, HTTP_TOO_MANY_REQUESTS, HTTP_METHOD_NOT_ALLOWED
)

logger = get_logger()

# 设置Windows控制台输出编码
if sys.platform == 'win32':
    import codecs
    if hasattr(sys.stdout, 'buffer'):
        # 使用 line_buffering=False 确保立即输出（将在代码中使用 flush）
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


# display_width 和 pad_string 已移至 llmct.utils.text_utils
# 直接从 llmct.utils 导入使用


class ModelTester:
    def __init__(self, api_key: str, base_url: str, timeout: int = 30, 
                 request_delay: float = 1.0, max_retries: int = 3,
                 concurrent: int = 1, rate_limit_rpm: int = 60, api_name: str = None):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.api_name = api_name or base_url  # API名称用于显示
        self.timeout = timeout
        
        # 请求头
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        # 使用requests.Session提升性能
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # 使用模型分类器
        self.classifier = ModelClassifier()
        
        # 统计和配置
        self.error_stats = {}  # 错误统计
        self.request_delay = request_delay  # 降低默认延迟到1秒
        self.max_retries = max_retries      # 429错误最大重试次数
        
        # 并发和速率限制配置
        self.concurrent = max(1, concurrent)  # 并发数，至少为1
        self.rate_limit_rpm = max(1, rate_limit_rpm)  # 每分钟请求数，至少为1
        self.min_interval = 60.0 / self.rate_limit_rpm  # 最小请求间隔（秒）
        self.last_request_time = 0  # 上次请求时间
        
        # 线程安全锁（用于速率限制）
        import threading
        self.rate_lock = threading.Lock()
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        if self.session:
            self.session.close()
    
    def validate_api_credentials(self) -> Tuple[bool, str]:
        """
        预验证API凭证是否有效
        
        Returns:
            (是否有效, 错误消息或成功消息)
        """
        try:
            url = f"{self.base_url}{API_ENDPOINT_MODELS}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == HTTP_UNAUTHORIZED:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', {}).get('message', '认证失败')
                    return False, f"API认证失败: {error_msg}"
                except:
                    return False, "API认证失败: 401 Unauthorized"
            elif response.status_code == HTTP_OK:
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
    
    def _wait_for_rate_limit(self):
        """根据速率限制等待适当的时间"""
        with self.rate_lock:
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            
            if time_since_last < self.min_interval:
                sleep_time = self.min_interval - time_since_last
                time.sleep(sleep_time)
            
            self.last_request_time = time.time()
    
    def _make_request_with_retry(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        发送HTTP请求，自动处理429错误重试（指数退避）并应用速率限制
        
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
                # 应用速率限制
                self._wait_for_rate_limit()
                
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
            url = f"{self.base_url}{API_ENDPOINT_CHAT}"
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
    
    def test_vision_model(self, model_id: str, test_message: str = DEFAULT_VISION_MESSAGE, 
                          image_url: str = DEFAULT_TEST_IMAGE_URL) -> Tuple[bool, float, str, str]:
        """测试视觉模型，返回(是否成功, 响应时间, 错误代码, 响应内容)"""
        try:
            url = f"{self.base_url}{API_ENDPOINT_CHAT}"
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
            url = f"{self.base_url}{API_ENDPOINT_AUDIO_TRANSCRIPTIONS}"
            start_time = time.time()
            response = requests.options(url, headers=self.headers, timeout=self.timeout)
            response_time = time.time() - start_time
            
            if response.status_code in [200, 405]:  # 405表示方法不允许，但端点存在
                return True, response_time, '', '音频端点可用'
            else:
                # 尝试TTS端点
                url = f"{self.base_url}{API_ENDPOINT_AUDIO_SPEECH}"
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
    
    def test_embedding_model(self, model_id: str, test_text: str = DEFAULT_EMBEDDING_TEXT) -> Tuple[bool, float, str, str]:
        """测试Embedding模型，返回(是否成功, 响应时间, 错误代码, 响应内容)"""
        try:
            url = f"{self.base_url}{API_ENDPOINT_EMBEDDINGS}"
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
    
    def test_image_generation_model(self, model_id: str, prompt: str = DEFAULT_IMAGE_GEN_PROMPT) -> Tuple[bool, float, str, str]:
        """测试图像生成模型，返回(是否成功, 响应时间, 错误代码, 响应内容)"""
        try:
            url = f"{self.base_url}{API_ENDPOINT_IMAGES}"
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
    
    def _test_single_model(self, model: Dict, test_message: str, test_vision: bool,
                          test_audio: bool, test_embedding: bool, test_image_gen: bool) -> Dict:
        """测试单个模型（可被并发调用）"""
        model_id = model.get('id', model.get('model', 'unknown'))
        model_type = self.classify_model(model_id)
        
        # 根据模型类型选择测试方法
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
                success, response_time, error_code, content = self.test_connectivity(model_id)
                if success:
                    content = f'[{model_type}模型] {content}'
            else:
                success, response_time, error_code, content = self.test_connectivity(model_id)
        
        # 更新错误统计
        if not success:
            self.update_error_stats(error_code)
        
        return {
            'model': model_id,
            'success': success,
            'response_time': response_time,
            'error_code': error_code,
            'content': content
        }
    
    def _test_models_sequential(self, models: List[Dict], test_message: str, test_vision: bool,
                                test_audio: bool, test_embedding: bool, test_image_gen: bool,
                                api_name: str = None) -> List[Dict]:
        """顺序测试模型（原有逻辑）"""
        results = []
        
        col_widths = {
            'model': COL_WIDTH_MODEL,
            'time': COL_WIDTH_TIME,
            'error': COL_WIDTH_ERROR,
            'content': COL_WIDTH_CONTENT
        }
        
        # 如果是多API模式，添加API名称列
        if api_name:
            col_widths['api_name'] = COL_WIDTH_API_NAME
        
        for idx, model in enumerate(models, 1):
            result = self._test_single_model(model, test_message, test_vision, 
                                            test_audio, test_embedding, test_image_gen)
            results.append(result)
            
            # 立即输出当前测试结果
            row = self.format_row(result['model'], result['success'], result['response_time'],
                                 result['error_code'], result['content'], col_widths, api_name)
            print(row)
            sys.stdout.flush()
            
            # 添加请求之间的延迟
            if idx < len(models) and self.request_delay > 0:
                time.sleep(self.request_delay)
        
        return results
    
    def _test_models_concurrent(self, models: List[Dict], test_message: str, test_vision: bool,
                                test_audio: bool, test_embedding: bool, test_image_gen: bool,
                                api_name: str = None) -> List[Dict]:
        """并发测试模型"""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import threading
        
        results = []
        results_lock = threading.Lock()
        
        col_widths = {
            'model': COL_WIDTH_MODEL,
            'time': COL_WIDTH_TIME,
            'error': COL_WIDTH_ERROR,
            'content': COL_WIDTH_CONTENT
        }
        
        # 如果是多API模式，添加API名称列
        if api_name:
            col_widths['api_name'] = COL_WIDTH_API_NAME
        
        print(f"[信息] 使用并发测试模式（并发数: {self.concurrent}，速率限制: {self.rate_limit_rpm} RPM）\n")
        sys.stdout.flush()
        
        with ThreadPoolExecutor(max_workers=self.concurrent) as executor:
            # 提交所有测试任务
            future_to_model = {
                executor.submit(self._test_single_model, model, test_message, 
                              test_vision, test_audio, test_embedding, test_image_gen): model
                for model in models
            }
            
            # 按完成顺序处理结果
            for future in as_completed(future_to_model):
                try:
                    result = future.result()
                    
                    with results_lock:
                        results.append(result)
                        
                        # 立即输出测试结果
                        row = self.format_row(result['model'], result['success'], result['response_time'],
                                             result['error_code'], result['content'], col_widths, api_name)
                        print(row)
                        sys.stdout.flush()
                        
                except Exception as e:
                    model = future_to_model[future]
                    model_id = model.get('id', model.get('model', 'unknown'))
                    logger.error(f"测试模型 {model_id} 时发生异常: {e}")
                    results.append({
                        'model': model_id,
                        'success': False,
                        'response_time': 0,
                        'error_code': 'EXCEPTION',
                        'content': str(e)[:200]
                    })
        
        return results
    
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
    

    
    def format_row(self, model_name: str, success: bool, response_time: float, 
                   error_code: str, content: str, col_widths: dict, api_name: str = None) -> str:
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
        if api_name:  # 多API模式
            # 截断API名称
            api_display = api_name
            if display_width(api_display) > col_widths.get('api_name', COL_WIDTH_API_NAME):
                while display_width(api_display) > col_widths.get('api_name', COL_WIDTH_API_NAME) - 2:
                    api_display = api_display[:-1]
                api_display = api_display + '..'
            
            row = (
                f"{pad_string(api_display, col_widths.get('api_name', COL_WIDTH_API_NAME), 'left')} | "
                f"{pad_string(model_name, col_widths['model'], 'left')} | "
                f"{pad_string(time_str, col_widths['time'], 'center')} | "
                f"{pad_string(error_str, col_widths['error'], 'center')} | "
                f"{pad_string(content_str, col_widths['content'], 'left')}"
            )
        else:  # 单API模式
            row = (
                f"{pad_string(model_name, col_widths['model'], 'left')} | "
                f"{pad_string(time_str, col_widths['time'], 'center')} | "
                f"{pad_string(error_str, col_widths['error'], 'center')} | "
                f"{pad_string(content_str, col_widths['content'], 'left')}"
            )
        return row
    
    def save_results(self, results: List[Dict], output_file: str, test_start_time: str):
        """保存测试结果到文件（使用Reporter，按base_url分类保存）"""
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
            
            # 使用Reporter生成报告（自动按base_url分类保存）
            reporter = Reporter(self.base_url)
            actual_output_file = reporter.save_report(results, output_file, format=format_type)
            
            logger.info(f"测试结果已保存到: {actual_output_file} (格式: {format_type})")
            print(f"[信息] 测试结果已保存到: {actual_output_file}")
            
            return actual_output_file
        except Exception as e:
            logger.warning(f"保存结果失败: {e}")
            print(f"[警告] 保存结果失败: {e}")
            return None
    
    def generate_analysis_report(self, results: List[Dict], output_file: str = None):
        """
        自动生成分析报告
        
        Args:
            results: 测试结果列表
            output_file: 输出文件路径（用于确定分析报告文件名）
        """
        if not results:
            return
        
        try:
            print(f"\n{'='*110}")
            print("📊 测试分析报告")
            print(f"{'='*110}\n")
            
            analyzer = ResultAnalyzer()
            
            # 1. 健康度评分
            health_score = analyzer.calculate_health_score(results)
            print(f"🏥 API健康度评分")
            print(f"{'-'*110}")
            print(f"综合评分: {health_score['score']}/100 (等级: {health_score['grade']})")
            print(f"  - 成功率评分: {health_score['details']['success_score']:.1f}/100")
            print(f"  - 响应速度评分: {health_score['details']['speed_score']:.1f}/100")
            print(f"  - 稳定性评分: {health_score['details']['stability_score']:.1f}/100")
            print(f"平均响应时间: {health_score['details']['avg_response_time']:.2f}秒")
            print()
            
            # 2. 告警检查
            alerts = analyzer.check_alerts(results)
            if alerts:
                print(f"⚠️  告警信息")
                print(f"{'-'*110}")
                for alert in alerts:
                    severity_icon = "🔴" if alert['severity'] == 'high' else "🟡"
                    print(f"{severity_icon} [{alert['severity'].upper()}] {alert['message']}")
                print()
            else:
                print(f"✅ 无告警\n")
            
            # 3. 保存详细分析报告到JSON
            if output_file:
                # 生成分析报告文件名
                base_name = os.path.splitext(output_file)[0]
                analysis_file = f"{base_name}_analysis.json"
                
                import json
                analysis_data = {
                    'health_score': health_score,
                    'alerts': alerts,
                    'timestamp': datetime.now().isoformat()
                }
                
                with open(analysis_file, 'w', encoding='utf-8') as f:
                    json.dump(analysis_data, f, ensure_ascii=False, indent=2)
                
                logger.info(f"分析报告已保存到: {analysis_file}")
                print(f"[信息] 详细分析报告已保存到: {analysis_file}")
            
            print(f"{'='*110}\n")
            sys.stdout.flush()
            
        except Exception as e:
            logger.warning(f"生成分析报告失败: {e}")
            print(f"[警告] 生成分析报告失败: {e}")
    
    def test_all_models(self, test_message: str = "hello", output_file: str = None, 
                        test_vision: bool = True, test_audio: bool = True, 
                        test_embedding: bool = True, test_image_gen: bool = True,
                        show_api_name: bool = False):
        """
        测试所有模型
        
        Args:
            test_message: 用于语言模型的测试消息
            output_file: 结果输出文件路径
            test_vision: 是否测试视觉模型（需要实际API调用）
            test_audio: 是否测试音频模型（需要实际API调用）
            test_embedding: 是否测试Embedding模型（需要实际API调用）
            test_image_gen: 是否测试图像生成模型（需要实际API调用）
            show_api_name: 是否在输出中显示API名称（多API并发模式）
        """
        test_start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"\n{'='*SEPARATOR_WIDTH}")
        print(f"大模型连通性和可用性测试")
        print(f"Base URL: {self.base_url}")
        print(f"测试时间: {test_start_time}")
        print(f"测试配置: 视觉={test_vision}, 音频={test_audio}, 嵌入={test_embedding}, 图像生成={test_image_gen}")
        print(f"{'='*SEPARATOR_WIDTH}\n")
        sys.stdout.flush()
        
        print("正在获取模型列表...")
        sys.stdout.flush()
        models = self.get_models()
        
        if not models:
            print("[错误] 未获取到任何模型，请检查API配置")
            sys.stdout.flush()
            return
        
        print(f"共发现 {len(models)} 个模型\n")
        sys.stdout.flush()
        
        # 定义列宽（使用常量）
        col_widths = {
            'model': COL_WIDTH_MODEL,
            'time': COL_WIDTH_TIME,
            'error': COL_WIDTH_ERROR,
            'content': COL_WIDTH_CONTENT
        }
        
        # 如果需要显示API名称，调整列宽和表格宽度
        if show_api_name:
            col_widths['api_name'] = COL_WIDTH_API_NAME
            total_width = TABLE_WIDTH_MULTI_API
        else:
            total_width = TABLE_WIDTH
        
        # 打印表头
        print(f"{'='*total_width}")
        if show_api_name:
            header = (
                f"{pad_string('API名称', col_widths['api_name'], 'left')} | "
                f"{pad_string('模型名称', col_widths['model'], 'left')} | "
                f"{pad_string('响应时间', col_widths['time'], 'center')} | "
                f"{pad_string('错误信息', col_widths['error'], 'center')} | "
                f"{pad_string('响应内容', col_widths['content'], 'left')}"
            )
        else:
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
        results = []
        
        # 传递API名称（如果需要显示）
        api_name_for_display = self.api_name if show_api_name else None
        
        # 根据并发数选择测试方式
        if self.concurrent > 1:
            # 并发测试
            results = self._test_models_concurrent(models, test_message, test_vision, 
                                                   test_audio, test_embedding, test_image_gen, api_name_for_display)
        else:
            # 顺序测试（原有逻辑）
            results = self._test_models_sequential(models, test_message, test_vision,
                                                   test_audio, test_embedding, test_image_gen, api_name_for_display)
        
        # 统计结果
        success_count = sum(1 for r in results if r['success'])
        fail_count = len(results) - success_count
        
        # 打印统计信息
        print(f"{'='*total_width}")
        success_rate = (success_count/len(models)*100) if len(models) > 0 else 0
        print(f"测试完成 | 总计: {len(models)} | 成功: {success_count} | 失败: {fail_count} | 成功率: {success_rate:.1f}%")
        print(f"{'='*total_width}\n")
        sys.stdout.flush()
        
        # 打印错误统计
        self.print_error_statistics(len(models), success_count)
        
        # 保存结果到文件
        actual_output_file = None
        if output_file:
            actual_output_file = self.save_results(results, output_file, test_start_time)
        
        # 自动生成分析报告
        self.generate_analysis_report(results, actual_output_file)
        
        # 打印按base_url的统计提示
        if actual_output_file:
            from pathlib import Path
            base_url_dir = Path(actual_output_file).parent
            print(f"\n[提示] 查看该base_url的历史统计，请运行:")
            print(f"  python mct.py --analyze {base_url_dir}")
            print()


def test_single_api(api_config: Dict, show_api_name: bool = False, print_lock = None) -> Dict:
    """
    测试单个API（用于并发测试）
    
    Args:
        api_config: API配置字典
        show_api_name: 是否显示API名称
        print_lock: 线程锁，用于保护打印输出
        
    Returns:
        包含测试结果的字典
    """
    import threading
    
    api_name = api_config.get('name', 'Unknown')
    api_key = api_config.get('key')
    base_url = api_config.get('base_url')
    
    # 获取API特定的配置
    timeout = api_config.get('timeout', DEFAULT_TIMEOUT)
    request_delay = api_config.get('request_delay', DEFAULT_REQUEST_DELAY)
    
    # 性能配置
    performance_config = api_config.get('performance', {})
    max_retries = performance_config.get('retry_times', DEFAULT_MAX_RETRIES)
    concurrent = performance_config.get('concurrent', 1)
    rate_limit_rpm = performance_config.get('rate_limit_rpm', 60)
    
    # 测试配置
    testing_config = api_config.get('testing', {})
    message = testing_config.get('message', DEFAULT_TEST_MESSAGE)
    skip_vision = testing_config.get('skip_vision', False)
    skip_audio = testing_config.get('skip_audio', False)
    skip_embedding = testing_config.get('skip_embedding', False)
    skip_image_gen = testing_config.get('skip_image_gen', False)
    
    # 输出配置
    output_config = api_config.get('output', {})
    output_file = output_config.get('file', DEFAULT_OUTPUT_FILE)
    
    # 创建测试器
    tester = ModelTester(
        api_key=api_key,
        base_url=base_url,
        timeout=timeout,
        request_delay=request_delay,
        max_retries=max_retries,
        concurrent=concurrent,
        rate_limit_rpm=rate_limit_rpm,
        api_name=api_name
    )
    
    # 执行测试
    tester.test_all_models(
        test_message=message, 
        output_file=output_file,
        test_vision=not skip_vision,
        test_audio=not skip_audio,
        test_embedding=not skip_embedding,
        test_image_gen=not skip_image_gen,
        show_api_name=show_api_name
    )
    
    return {
        'api_name': api_name,
        'base_url': base_url,
        'status': 'completed'
    }


def main():
    parser = argparse.ArgumentParser(
        description='大模型连通性和可用性测试工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 基础测试
  python mct.py --api-key sk-xxx --base-url https://api.openai.com
  
  # 自定义测试消息
  python mct.py --api-key sk-xxx --base-url https://api.openai.com --message "你好"
  
  # 保存结果到不同格式
  python mct.py --api-key sk-xxx --base-url https://api.openai.com --output results.json
  python mct.py --api-key sk-xxx --base-url https://api.openai.com --output results.html
  python mct.py --api-key sk-xxx --base-url https://api.openai.com --output results.csv
  
  # 跳过特定类型的模型测试
  python mct.py --api-key sk-xxx --base-url https://api.openai.com --skip-vision --skip-audio
  
  # 查看某个base_url的历史统计
  python mct.py --analyze test_results/api.openai.com
        """
    )
    
    parser.add_argument(
        '--analyze',
        metavar='DIR',
        help='分析指定base_url目录的历史测试结果（例如: test_results/api.openai.com）'
    )
    
    parser.add_argument(
        '--config',
        default='config.yaml',
        help='配置文件路径 (默认: config.yaml)'
    )
    
    parser.add_argument(
        '--api-key',
        required=False,
        help='API密钥 (覆盖配置文件)'
    )
    
    parser.add_argument(
        '--base-url',
        required=False,
        help='API基础URL (覆盖配置文件，例如: https://api.openai.com)'
    )
    
    parser.add_argument(
        '--message',
        default=DEFAULT_TEST_MESSAGE,
        help=f'用于测试语言模型的消息 (默认: {DEFAULT_TEST_MESSAGE})'
    )
    
    parser.add_argument(
        '--timeout',
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f'请求超时时间(秒) (默认: {DEFAULT_TIMEOUT})'
    )
    
    parser.add_argument(
        '--request-delay',
        type=float,
        default=DEFAULT_REQUEST_DELAY,
        help=f'请求之间的延迟(秒)，避免速率限制 (默认: {DEFAULT_REQUEST_DELAY})'
    )
    
    parser.add_argument(
        '--max-retries',
        type=int,
        default=DEFAULT_MAX_RETRIES,
        help=f'遇到429错误时的最大重试次数 (默认: {DEFAULT_MAX_RETRIES})'
    )
    
    parser.add_argument(
        '--output',
        '-o',
        default=DEFAULT_OUTPUT_FILE,
        help=f'测试结果输出文件路径 (默认: {DEFAULT_OUTPUT_FILE})'
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
        '--api-concurrent',
        type=int,
        default=DEFAULT_API_CONCURRENT,
        help=f'多API并发测试数（默认: {DEFAULT_API_CONCURRENT}，1=顺序测试，>1=并发测试多个API）'
    )
    
    args = parser.parse_args()
    
    # 如果是分析模式
    if args.analyze:
        try:
            from llmct.core.analyzer import ResultAnalyzer
            from llmct.utils import pad_string
            
            analyzer = ResultAnalyzer()
            
            print(f"\n{'='*110}")
            print(f"分析 {args.analyze} 目录下的历史测试结果")
            print(f"{'='*110}\n")
            
            # 获取模型成功率排名
            ranked_models = analyzer.get_model_success_rates(args.analyze, min_tests=1)
            
            if not ranked_models:
                print(f"[错误] 未找到测试结果或分析失败")
                sys.exit(1)
            
            # 打印统计表格
            print(f"{'模型名称':<50} | {'测试次数':<10} | {'成功次数':<10} | {'失败次数':<10} | {'成功率':<10} | {'平均响应时间':<12}")
            print("-" * 110)
            
            for model in ranked_models:
                model_name = model['model'][:47] + '...' if len(model['model']) > 50 else model['model']
                print(f"{model_name:<50} | {model['total_tests']:<10} | {model['success_tests']:<10} | "
                      f"{model['failed_tests']:<10} | {model['success_rate']:>6.1f}%    | {model['avg_response_time']:>8.2f}秒")
            
            print(f"\n{'='*110}")
            print(f"总计: {len(ranked_models)} 个模型")
            print(f"{'='*110}\n")
            
            # 保存详细分析报告
            analyzer.save_base_url_analysis(args.analyze)
            
        except Exception as e:
            print(f"\n[错误] 分析失败: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
        
        sys.exit(0)
    
    # 正常测试模式
    # 加载配置文件
    from llmct.utils.config import Config
    
    # 如果指定了config文件且存在，则加载；否则尝试加载默认的config.yaml
    if os.path.exists(args.config):
        config = Config(args.config)
        print(f"[信息] 已加载配置文件: {args.config}\n")
    elif os.path.exists('config.yaml'):
        config = Config('config.yaml')
        print(f"[信息] 已加载配置文件: config.yaml\n")
    else:
        config = Config()
    
    # 从命令行参数覆盖配置（仅对单API模式生效）
    config.override_from_args(args)
    
    # 获取API配置列表（支持多API批量测试）
    apis = config.get_apis()
    
    if not apis:
        parser.error("需要API密钥和Base URL。请通过以下方式之一提供:\n"
                     "  1. 使用 --api-key 和 --base-url 参数\n"
                     "  2. 在 config.yaml 文件中配置 api 部分\n"
                     "  3. 在 config.yaml 文件中配置 apis 列表（支持多API批量测试）\n"
                     "  4. 设置环境变量 LLMCT_API_KEY 和 LLMCT_BASE_URL")
    
    # 检查是否有有效的API配置
    valid_apis = [api for api in apis if api.get('key') and api.get('base_url')]
    if not valid_apis:
        parser.error("未找到有效的API配置（需要同时配置 key 和 base_url）")
    
    # 如果配置了多个API，显示批量测试信息
    if len(valid_apis) > 1:
        # 检查是否启用多API并发测试
        api_concurrent = args.api_concurrent if hasattr(args, 'api_concurrent') else DEFAULT_API_CONCURRENT
        
        if api_concurrent > 1:
            print(f"[信息] 检测到多API配置，将并发测试 {len(valid_apis)} 个API提供商（并发数: {api_concurrent}）:\n")
        else:
            print(f"[信息] 检测到多API配置，将依次测试 {len(valid_apis)} 个API提供商:\n")
        
        for idx, api in enumerate(valid_apis, 1):
            print(f"  {idx}. {api.get('name', 'Unknown')} - {api.get('base_url')}")
        print()
    
    try:
        # 获取API并发配置（优先级：命令行参数 > 配置文件 > 默认值）
        if hasattr(args, 'api_concurrent') and args.api_concurrent != DEFAULT_API_CONCURRENT:
            # 命令行参数优先
            api_concurrent = args.api_concurrent
        else:
            # 从配置文件读取
            performance_config = config.config.get('performance', {})
            api_concurrent = performance_config.get('api_concurrent', DEFAULT_API_CONCURRENT)
        
        # 如果多个API且启用并发
        if len(valid_apis) > 1 and api_concurrent > 1:
            from concurrent.futures import ThreadPoolExecutor, as_completed
            import threading
            
            # 打印多API并发表头
            print(f"{'='*SEPARATOR_WIDTH_MULTI_API}")
            print("多API并发测试模式")
            print(f"{'='*SEPARATOR_WIDTH_MULTI_API}")
            print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"并发API数: {min(api_concurrent, len(valid_apis))}")
            print(f"{'='*SEPARATOR_WIDTH_MULTI_API}\n")
            sys.stdout.flush()
            
            # 打印统一表头
            from llmct.utils import pad_string  # 导入pad_string函数
            
            col_widths = {
                'api_name': COL_WIDTH_API_NAME,
                'model': COL_WIDTH_MODEL,
                'time': COL_WIDTH_TIME,
                'error': COL_WIDTH_ERROR,
                'content': COL_WIDTH_CONTENT
            }
            
            print(f"{'='*TABLE_WIDTH_MULTI_API}")
            header = (
                f"{pad_string('API名称', col_widths['api_name'], 'left')} | "
                f"{pad_string('模型名称', col_widths['model'], 'left')} | "
                f"{pad_string('响应时间', col_widths['time'], 'center')} | "
                f"{pad_string('错误信息', col_widths['error'], 'center')} | "
                f"{pad_string('响应内容', col_widths['content'], 'left')}"
            )
            print(header)
            print(f"{'-'*TABLE_WIDTH_MULTI_API}")
            sys.stdout.flush()
            
            # 创建线程池并发测试
            print_lock = threading.Lock()
            completed_apis = []
            
            with ThreadPoolExecutor(max_workers=min(api_concurrent, len(valid_apis))) as executor:
                # 提交所有API测试任务
                future_to_api = {
                    executor.submit(test_single_api, api_config, True, print_lock): api_config
                    for api_config in valid_apis
                }
                
                # 等待所有任务完成
                for future in as_completed(future_to_api):
                    try:
                        result = future.result()
                        completed_apis.append(result)
                        
                        # 打印完成通知
                        with print_lock:
                            print(f"\n{'='*TABLE_WIDTH_MULTI_API}")
                            print(f"[{result['api_name']}] 测试完成")
                            print(f"{'='*TABLE_WIDTH_MULTI_API}\n")
                            sys.stdout.flush()
                    except Exception as e:
                        api_config = future_to_api[future]
                        api_name = api_config.get('name', 'Unknown')
                        logger.error(f"测试API {api_name} 时发生异常: {e}")
                        with print_lock:
                            print(f"\n[错误] {api_name} 测试失败: {e}\n")
                            sys.stdout.flush()
            
            # 打印总结
            print(f"\n{'='*SEPARATOR_WIDTH_MULTI_API}")
            print(f"批量测试完成！共测试了 {len(completed_apis)} 个API提供商")
            print(f"{'='*SEPARATOR_WIDTH_MULTI_API}\n")
            print("各API测试结果已保存到对应的目录：")
            for api_config in valid_apis:
                from urllib.parse import urlparse
                parsed = urlparse(api_config.get('base_url', ''))
                domain = parsed.netloc or 'unknown'
                print(f"  - {api_config.get('name')}: test_results/{domain}/")
            print()
        
        else:
            # 顺序测试所有API（原有逻辑）
            for api_idx, api_config in enumerate(valid_apis, 1):
                api_name = api_config.get('name', 'Unknown')
                api_key = api_config.get('key')
                base_url = api_config.get('base_url')
                
                # 如果是多API模式，显示当前测试的API
                if len(valid_apis) > 1:
                    print(f"\n{'='*110}")
                    print(f"[{api_idx}/{len(valid_apis)}] 开始测试: {api_name}")
                    print(f"{'='*110}\n")
                
                # 获取API特定的配置
                timeout = api_config.get('timeout', DEFAULT_TIMEOUT)
                request_delay = api_config.get('request_delay', DEFAULT_REQUEST_DELAY)
                
                # 性能配置
                performance_config = api_config.get('performance', {})
                max_retries = performance_config.get('retry_times', DEFAULT_MAX_RETRIES)
                concurrent = performance_config.get('concurrent', 1)
                rate_limit_rpm = performance_config.get('rate_limit_rpm', 60)
                
                # 测试配置
                testing_config = api_config.get('testing', {})
                message = testing_config.get('message', DEFAULT_TEST_MESSAGE)
                skip_vision = testing_config.get('skip_vision', False)
                skip_audio = testing_config.get('skip_audio', False)
                skip_embedding = testing_config.get('skip_embedding', False)
                skip_image_gen = testing_config.get('skip_image_gen', False)
                
                # 输出配置
                output_config = api_config.get('output', {})
                output_file = output_config.get('file', DEFAULT_OUTPUT_FILE)
                
                # 创建测试器
                tester = ModelTester(
                    api_key=api_key,
                    base_url=base_url,
                    timeout=timeout,
                    request_delay=request_delay,
                    max_retries=max_retries,
                    concurrent=concurrent,
                    rate_limit_rpm=rate_limit_rpm,
                    api_name=api_name
                )
                
                # 执行测试
                tester.test_all_models(
                    test_message=message, 
                    output_file=output_file,
                    test_vision=not skip_vision,
                    test_audio=not skip_audio,
                    test_embedding=not skip_embedding,
                    test_image_gen=not skip_image_gen
                )
                
                # 如果是多API模式且不是最后一个，添加分隔和延迟
                if len(valid_apis) > 1 and api_idx < len(valid_apis):
                    print(f"\n{'='*110}")
                    print(f"[{api_idx}/{len(valid_apis)}] {api_name} 测试完成，准备测试下一个API...")
                    print(f"{'='*110}\n")
                    time.sleep(2)  # 短暂延迟，避免过快切换
            
            # 多API测试完成总结
            if len(valid_apis) > 1:
                print(f"\n{'='*110}")
                print(f"批量测试完成！共测试了 {len(valid_apis)} 个API提供商")
                print(f"{'='*110}\n")
                print("各API测试结果已保存到对应的目录：")
                for api in valid_apis:
                    from urllib.parse import urlparse
                    parsed = urlparse(api.get('base_url', ''))
                    domain = parsed.netloc or 'unknown'
                    print(f"  - {api.get('name')}: test_results/{domain}/")
                print()
    except KeyboardInterrupt:
        print("\n\n测试已取消")
        sys.exit(0)
    except Exception as e:
        print(f"\n[错误] 程序异常: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
