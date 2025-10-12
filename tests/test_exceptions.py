"""测试异常类"""

import pytest
from llmct.core.exceptions import (
    LLMCTError,
    APIConnectionError,
    AuthenticationError,
    RateLimitError,
    ModelNotFoundError,
    InvalidResponseError
)


def test_base_exception():
    """测试基础异常"""
    with pytest.raises(LLMCTError):
        raise LLMCTError("Test error")


def test_api_connection_error():
    """测试API连接错误"""
    error = APIConnectionError("Connection failed", url="https://api.test.com")
    
    assert str(error) == "Connection failed"
    assert error.url == "https://api.test.com"


def test_authentication_error():
    """测试认证错误"""
    error = AuthenticationError("Invalid API key", api_key_prefix="sk-123")
    
    assert str(error) == "Invalid API key"
    assert error.api_key_prefix == "sk-123"


def test_rate_limit_error():
    """测试速率限制错误"""
    error = RateLimitError("Too many requests", retry_after=120)
    
    assert str(error) == "Too many requests"
    assert error.retry_after == 120


def test_rate_limit_error_default():
    """测试速率限制错误默认值"""
    error = RateLimitError("Too many requests")
    
    assert error.retry_after == 60  # 默认值


def test_model_not_found_error():
    """测试模型不存在错误"""
    error = ModelNotFoundError("gpt-5")
    
    assert "gpt-5" in str(error)
    assert error.model_id == "gpt-5"


def test_invalid_response_error():
    """测试无效响应错误"""
    with pytest.raises(InvalidResponseError):
        raise InvalidResponseError("Invalid JSON response")
