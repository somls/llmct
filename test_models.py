#!/usr/bin/env python3
"""
大模型连通性和可用性测试工具
测试语言模型的响应能力和非语言模型的连通性
"""

import argparse
import json
import sys
import time
from typing import List, Dict, Tuple
import requests
from datetime import datetime
import unicodedata


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
    def __init__(self, api_key: str, base_url: str, timeout: int = 30):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
    
    def get_models(self) -> List[Dict]:
        """获取模型列表"""
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
            print(f"[错误] 获取模型列表失败: {e}")
            return []
    
    def is_language_model(self, model_id: str) -> bool:
        """判断是否为语言模型"""
        non_language_keywords = [
            'embedding', 'whisper', 'tts', 'dall-e', 'vision',
            'image', 'audio', 'speech', 'moderation'
        ]
        model_lower = model_id.lower()
        return not any(keyword in model_lower for keyword in non_language_keywords)
    
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
            response = requests.post(
                url, 
                headers=self.headers, 
                json=payload, 
                timeout=self.timeout
            )
            response_time = time.time() - start_time
            
            response.raise_for_status()
            data = response.json()
            
            if 'choices' in data and len(data['choices']) > 0:
                content = data['choices'][0].get('message', {}).get('content', '')
                return True, response_time, '', content.strip()
            else:
                return False, response_time, 'NO_CONTENT', ''
                
        except requests.exceptions.Timeout:
            return False, self.timeout, 'TIMEOUT', ''
        except requests.exceptions.HTTPError as e:
            error_code = f'HTTP_{e.response.status_code}' if hasattr(e, 'response') else 'HTTP_ERROR'
            return False, 0, error_code, ''
        except requests.exceptions.RequestException:
            return False, 0, 'REQUEST_FAILED', ''
        except Exception:
            return False, 0, 'UNKNOWN_ERROR', ''
    
    def test_connectivity(self, model_id: str) -> Tuple[bool, float, str, str]:
        """测试非语言模型的连通性，返回(是否成功, 响应时间, 错误代码, 响应内容)"""
        try:
            url = f"{self.base_url}/v1/models/{model_id}"
            
            start_time = time.time()
            response = requests.get(
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
            error_code = f'HTTP_{e.response.status_code}' if hasattr(e, 'response') else 'HTTP_ERROR'
            return False, 0, error_code, ''
        except requests.exceptions.RequestException:
            return False, 0, 'CONN_FAILED', ''
        except Exception:
            return False, 0, 'UNKNOWN_ERROR', ''
    
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
    
    def test_all_models(self, test_message: str = "hello"):
        """测试所有模型"""
        header_width = 110  # 紧凑模式的总宽度
        print(f"\n{'='*header_width}")
        print(f"大模型连通性和可用性测试")
        print(f"Base URL: {self.base_url}")
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*header_width}\n")
        
        print("正在获取模型列表...")
        models = self.get_models()
        
        if not models:
            print("[错误] 未获取到任何模型，请检查API配置")
            return
        
        print(f"共发现 {len(models)} 个模型\n")
        
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
        
        success_count = 0
        fail_count = 0
        
        # 边测试边输出
        for idx, model in enumerate(models, 1):
            model_id = model.get('id', model.get('model', 'unknown'))
            
            is_language = self.is_language_model(model_id)
            
            if is_language:
                success, response_time, error_code, content = self.test_language_model(model_id, test_message)
            else:
                success, response_time, error_code, content = self.test_connectivity(model_id)
            
            if success:
                success_count += 1
            else:
                fail_count += 1
            
            # 立即输出当前测试结果
            row = self.format_row(model_id, success, response_time, error_code, content, col_widths)
            print(row)
        
        # 打印统计信息
        print(f"{'='*total_width}")
        print(f"测试完成 | 总计: {len(models)} | 成功: {success_count} | 失败: {fail_count} | 成功率: {(success_count/len(models)*100):.1f}%")
        print(f"{'='*total_width}\n")


def main():
    parser = argparse.ArgumentParser(
        description='大模型连通性和可用性测试工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python test_models.py --api-key sk-xxx --base-url https://api.openai.com
  python test_models.py --api-key sk-xxx --base-url https://api.openai.com --message "你好"
  python test_models.py --api-key sk-xxx --base-url https://api.openai.com --timeout 60
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
    
    args = parser.parse_args()
    
    try:
        tester = ModelTester(
            api_key=args.api_key,
            base_url=args.base_url,
            timeout=args.timeout
        )
        tester.test_all_models(test_message=args.message)
    except KeyboardInterrupt:
        print("\n\n测试已取消")
        sys.exit(0)
    except Exception as e:
        print(f"\n[错误] 程序异常: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
