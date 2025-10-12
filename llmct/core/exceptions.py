"""自定义异常类"""


class LLMCTError(Exception):
    """基础异常类"""
    pass


class APIConnectionError(LLMCTError):
    """API连接错误"""
    def __init__(self, message, url=None):
        self.url = url
        super().__init__(message)


class AuthenticationError(LLMCTError):
    """认证错误"""
    def __init__(self, message, api_key_prefix=None):
        self.api_key_prefix = api_key_prefix
        super().__init__(message)


class RateLimitError(LLMCTError):
    """速率限制错误"""
    def __init__(self, message, retry_after=None):
        self.retry_after = retry_after or 60
        super().__init__(message)


class ModelNotFoundError(LLMCTError):
    """模型不存在"""
    def __init__(self, model_id):
        self.model_id = model_id
        super().__init__(f"Model not found: {model_id}")


class InvalidResponseError(LLMCTError):
    """无效响应"""
    pass


class TimeoutError(LLMCTError):
    """请求超时"""
    pass
