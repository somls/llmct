"""pytest配置文件"""

import pytest
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def temp_config_file(tmp_path):
    """创建临时配置文件"""
    config_file = tmp_path / "config.yaml"
    config_content = """
api:
  key: test-api-key
  base_url: https://api.test.com
  timeout: 30

testing:
  message: "hello"
  skip_vision: false
  only_failed: false
  max_failures: 0

cache:
  enabled: true
  duration_hours: 24
  file: test_cache.json
"""
    config_file.write_text(config_content, encoding='utf-8')
    return str(config_file)


@pytest.fixture
def temp_cache_file(tmp_path):
    """创建临时缓存文件"""
    cache_file = tmp_path / "test_cache.json"
    return str(cache_file)


@pytest.fixture
def sample_models():
    """示例模型列表"""
    return [
        {'id': 'gpt-4o', 'model': 'gpt-4o'},
        {'id': 'gpt-3.5-turbo', 'model': 'gpt-3.5-turbo'},
        {'id': 'whisper-1', 'model': 'whisper-1'},
        {'id': 'dall-e-3', 'model': 'dall-e-3'},
    ]
