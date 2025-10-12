"""测试配置管理功能"""

import pytest
from llmct.utils.config import Config


def test_default_config():
    """测试默认配置"""
    config = Config()
    
    assert config.get('api.timeout') == 30
    assert config.get('testing.message') == 'hello'
    assert config.get('cache.enabled') is True
    assert config.get('cache.duration_hours') == 24


def test_load_from_file(temp_config_file):
    """测试从文件加载配置"""
    config = Config(config_file=temp_config_file)
    
    assert config.get('api.key') == 'test-api-key'
    assert config.get('api.base_url') == 'https://api.test.com'
    assert config.get('api.timeout') == 30


def test_get_nested_config(temp_config_file):
    """测试获取嵌套配置"""
    config = Config(config_file=temp_config_file)
    
    assert config.get('api.key') == 'test-api-key'
    assert config.get('testing.message') == 'hello'
    assert config.get('nonexistent.key', 'default') == 'default'


def test_set_config():
    """测试设置配置"""
    config = Config()
    
    config.set('api.key', 'new-key')
    assert config.get('api.key') == 'new-key'
    
    config.set('new.nested.key', 'value')
    assert config.get('new.nested.key') == 'value'


def test_override_from_args():
    """测试从命令行参数覆盖配置"""
    config = Config()
    
    class Args:
        api_key = 'override-key'
        base_url = 'https://override.com'
        timeout = 60
        message = 'test'
        output = 'output.txt'
        skip_vision = True
        skip_audio = False
        skip_embedding = False
        skip_image_gen = False
        only_failed = True
        max_failures = 5
        no_cache = True
        cache_duration = 48
    
    args = Args()
    config.override_from_args(args)
    
    assert config.get('api.key') == 'override-key'
    assert config.get('testing.only_failed') is True
    assert config.get('testing.max_failures') == 5
    assert config.get('cache.enabled') is False


def test_to_dict():
    """测试导出为字典"""
    config = Config()
    config.set('api.key', 'test-key')
    
    config_dict = config.to_dict()
    
    assert isinstance(config_dict, dict)
    assert config_dict['api']['key'] == 'test-key'
    
    # 确保是深拷贝
    config_dict['api']['key'] = 'modified'
    assert config.get('api.key') == 'test-key'


def test_env_variables(monkeypatch):
    """测试环境变量加载"""
    monkeypatch.setenv('LLMCT_API_KEY', 'env-key')
    monkeypatch.setenv('LLMCT_BASE_URL', 'https://env.com')
    
    config = Config()
    
    assert config.get('api.key') == 'env-key'
    assert config.get('api.base_url') == 'https://env.com'
