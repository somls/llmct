"""配置管理模块"""

import os
import yaml
import re
from pathlib import Path
from typing import Any, Dict, List


class Config:
    """配置管理器"""
    
    DEFAULT_CONFIG = {
        'api': {
            'key': '',
            'base_url': '',
            'timeout': 30
        },
        'testing': {
            'message': 'hello',
            'skip_vision': False,
            'skip_audio': False,
            'skip_embedding': False,
            'skip_image_gen': False
        },
        'output': {
            'file': 'test_results.txt',
            'format': 'txt'
        },
        'performance': {
            'concurrent': 10,
            'rate_limit_rpm': 60,
            'retry_times': 3,
            'retry_delay': 5,
            'request_delay': 3.0
        },
        'logging': {
            'level': 'INFO',
            'file': None
        }
    }
    
    def __init__(self, config_file=None):
        self.config = self._deep_copy(self.DEFAULT_CONFIG)
        
        # 加载配置文件
        if config_file and Path(config_file).exists():
            self._load_from_file(config_file)
        elif Path('config.yaml').exists():
            self._load_from_file('config.yaml')
        
        # 从环境变量加载
        self._load_from_env()
    
    def _deep_copy(self, d):
        """深拷贝字典"""
        if isinstance(d, dict):
            return {k: self._deep_copy(v) for k, v in d.items()}
        elif isinstance(d, list):
            return [self._deep_copy(item) for item in d]
        else:
            return d
    
    def _load_from_file(self, file_path):
        """从YAML文件加载配置"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # 替换环境变量
                content = self._expand_env_vars(content)
                user_config = yaml.safe_load(content)
                if user_config:
                    self._deep_update(self.config, user_config)
        except Exception as e:
            print(f"[警告] 加载配置文件失败: {e}")
    
    def _expand_env_vars(self, content: str) -> str:
        """展开环境变量 ${VAR_NAME}"""
        def replace_env_var(match):
            var_name = match.group(1)
            return os.environ.get(var_name, match.group(0))
        
        return re.sub(r'\$\{([A-Za-z_][A-Za-z0-9_]*)\}', replace_env_var, content)
    
    def _load_from_env(self):
        """从环境变量加载配置"""
        if 'LLMCT_API_KEY' in os.environ:
            self.config['api']['key'] = os.environ['LLMCT_API_KEY']
        if 'LLMCT_BASE_URL' in os.environ:
            self.config['api']['base_url'] = os.environ['LLMCT_BASE_URL']
    
    def _deep_update(self, base_dict, update_dict):
        """深度更新字典"""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def get(self, key_path: str, default=None) -> Any:
        """
        获取配置值
        
        Args:
            key_path: 配置路径，如 'api.key' 或 'testing.message'
            default: 默认值
        """
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value: Any):
        """设置配置值"""
        keys = key_path.split('.')
        config = self.config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
    
    def override_from_args(self, args):
        """从命令行参数覆盖配置"""
        if hasattr(args, 'api_key') and args.api_key:
            self.set('api.key', args.api_key)
        if hasattr(args, 'base_url') and args.base_url:
            self.set('api.base_url', args.base_url)
        if hasattr(args, 'timeout') and args.timeout:
            self.set('api.timeout', args.timeout)
        if hasattr(args, 'message') and args.message:
            self.set('testing.message', args.message)
        if hasattr(args, 'output') and args.output:
            self.set('output.file', args.output)
        if hasattr(args, 'skip_vision'):
            self.set('testing.skip_vision', args.skip_vision)
        if hasattr(args, 'skip_audio'):
            self.set('testing.skip_audio', args.skip_audio)
        if hasattr(args, 'skip_embedding'):
            self.set('testing.skip_embedding', args.skip_embedding)
        if hasattr(args, 'skip_image_gen'):
            self.set('testing.skip_image_gen', args.skip_image_gen)

    
    def to_dict(self) -> Dict:
        """导出为字典"""
        return self._deep_copy(self.config)
    
    def get_apis(self) -> List[Dict]:
        """
        获取API配置列表
        
        Returns:
            API配置列表。如果配置了 apis 列表，返回启用的API；
            否则返回包含单个API配置的列表
        """
        # 检查是否配置了多API
        if 'apis' in self.config and self.config['apis']:
            # 返回所有启用的API
            enabled_apis = []
            for api_config in self.config['apis']:
                if api_config.get('enabled', True):  # 默认启用
                    # 合并全局配置和API特定配置
                    merged = self._merge_api_config(api_config)
                    enabled_apis.append(merged)
            return enabled_apis
        else:
            # 返回单API配置
            return [{
                'name': 'Default',
                'key': self.config['api']['key'],
                'base_url': self.config['api']['base_url'],
                'timeout': self.config['api']['timeout'],
                'request_delay': self.config['performance']['request_delay'],
                'testing': self.config['testing'],
                'output': self.config['output'],
                'performance': self.config['performance'],
                'logging': self.config['logging']
            }]
    
    def _merge_api_config(self, api_config: Dict) -> Dict:
        """合并全局配置和API特定配置"""
        merged = {
            'name': api_config.get('name', 'Unknown'),
            'key': api_config.get('key', ''),
            'base_url': api_config.get('base_url', ''),
            'timeout': api_config.get('timeout', self.config['api']['timeout']),
            'request_delay': api_config.get('request_delay', self.config['performance']['request_delay']),
        }
        
        # 合并测试配置
        if 'testing' in api_config:
            merged['testing'] = {**self.config['testing'], **api_config['testing']}
        else:
            merged['testing'] = self.config['testing'].copy()
        
        # 使用全局输出和性能配置
        merged['output'] = self.config['output'].copy()
        merged['performance'] = self.config['performance'].copy()
        merged['logging'] = self.config['logging'].copy()
        
        return merged
    
    @staticmethod
    def create_template(file_path='config_example.yaml'):
        """创建配置模板文件"""
        template = """# 大模型连通性测试工具 - 配置文件示例

# API配置
api:
  key: ${LLMCT_API_KEY}  # API密钥（支持环境变量）
  base_url: https://api.openai.com  # API基础URL
  timeout: 30  # 请求超时时间（秒）

# 测试配置
testing:
  message: "hello"  # 测试消息
  skip_vision: false  # 跳过视觉模型测试
  skip_audio: false  # 跳过音频模型测试
  skip_embedding: false  # 跳过嵌入模型测试
  skip_image_gen: false  # 跳过图像生成测试

# 输出配置
output:
  file: test_results.txt  # 输出文件
  format: txt  # 输出格式：txt, json, csv, html

# 性能配置
performance:
  concurrent: 10  # 并发数
  rate_limit_rpm: 60  # 速率限制（每分钟请求数）
  retry_times: 3  # 重试次数
  retry_delay: 5  # 重试延迟（秒）
  request_delay: 3.0  # 请求之间的延迟（秒），避免速率限制

# 日志配置
logging:
  level: INFO  # 日志级别：DEBUG, INFO, WARNING, ERROR, CRITICAL
  file: null  # 日志文件（null=不输出到文件）
"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(template)
        print(f"配置模板已创建: {file_path}")
