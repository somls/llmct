"""类型定义模块 - 使用dataclass标准化数据结构"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum


class ModelType(Enum):
    """模型类型枚举"""
    LANGUAGE = "language"
    VISION = "vision"
    AUDIO = "audio"
    EMBEDDING = "embedding"
    IMAGE_GENERATION = "image_generation"
    RERANKER = "reranker"
    MODERATION = "moderation"
    OTHER = "other"


class ErrorCode(Enum):
    """错误代码枚举"""
    HTTP_403 = "HTTP_403"
    HTTP_400 = "HTTP_400"
    HTTP_429 = "HTTP_429"
    HTTP_404 = "HTTP_404"
    HTTP_500 = "HTTP_500"
    HTTP_503 = "HTTP_503"
    TIMEOUT = "TIMEOUT"
    NO_CONTENT = "NO_CONTENT"
    NO_DATA = "NO_DATA"
    REQUEST_FAILED = "REQUEST_FAILED"
    CONN_FAILED = "CONN_FAILED"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"
    SKIPPED = "SKIPPED"


@dataclass
class TestResult:
    """
    标准化测试结果
    
    使用dataclass提供:
    - 类型安全
    - 自动生成__init__/__repr__
    - IDE自动补全
    """
    model: str
    success: bool
    response_time: float
    error_code: str = ""
    content: str = ""
    timestamp: Optional[str] = None
    model_type: Optional[str] = None
    
    def __post_init__(self):
        """初始化后处理"""
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'model': self.model,
            'success': self.success,
            'response_time': self.response_time,
            'error_code': self.error_code,
            'content': self.content,
            'timestamp': self.timestamp,
            'model_type': self.model_type
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'TestResult':
        """从字典创建"""
        return cls(
            model=data['model'],
            success=data['success'],
            response_time=data['response_time'],
            error_code=data.get('error_code', ''),
            content=data.get('content', ''),
            timestamp=data.get('timestamp'),
            model_type=data.get('model_type')
        )


@dataclass
class ModelInfo:
    """模型信息"""
    id: str
    name: Optional[str] = None
    model_type: Optional[ModelType] = None
    created: Optional[int] = None
    owned_by: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.model_type.value if self.model_type else None,
            'created': self.created,
            'owned_by': self.owned_by
        }


@dataclass
class CacheEntry:
    """缓存条目"""
    model_id: str
    success: bool
    response_time: float
    error_code: str
    content: str
    timestamp: str
    failure_count: int = 0
    last_failure: str = ""
    failure_history: List[Dict] = field(default_factory=list)
    
    def is_expired(self, max_age_hours: int = 24) -> bool:
        """检查是否过期"""
        try:
            cache_time = datetime.fromisoformat(self.timestamp)
            age = datetime.now() - cache_time
            return age.total_seconds() > max_age_hours * 3600
        except:
            return True


@dataclass
class TestConfig:
    """测试配置"""
    api_key: str
    base_url: str
    timeout: int = 30
    message: str = "hello"
    skip_vision: bool = False
    skip_audio: bool = False
    skip_embedding: bool = False
    skip_image_gen: bool = False
    only_failed: bool = False
    max_failures: int = 0
    max_concurrent: int = 10
    cache_enabled: bool = True
    cache_duration_hours: int = 24
    output_file: str = "test_results.txt"
    output_format: str = "txt"


@dataclass
class TestStatistics:
    """测试统计"""
    total: int
    success: int
    failed: int
    skipped: int = 0
    cached: int = 0
    success_rate: float = 0.0
    avg_response_time: float = 0.0
    error_breakdown: Dict[str, int] = field(default_factory=dict)
    
    def __post_init__(self):
        """计算成功率"""
        if self.total > 0:
            self.success_rate = (self.success / self.total) * 100


@dataclass
class PerformanceMetrics:
    """性能指标"""
    total_time: float
    models_tested: int
    requests_per_second: float = 0.0
    avg_response_time: float = 0.0
    min_response_time: float = 0.0
    max_response_time: float = 0.0
    p50_response_time: float = 0.0
    p95_response_time: float = 0.0
    p99_response_time: float = 0.0
    
    def __post_init__(self):
        """计算每秒请求数"""
        if self.total_time > 0:
            self.requests_per_second = self.models_tested / self.total_time
