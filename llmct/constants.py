"""常量配置文件 - 集中管理所有魔法数字和字符串"""

# ============================================
# 显示和格式化常量
# ============================================

# 表格列宽
COL_WIDTH_API_NAME = 12  # API名称列宽（用于多API并发模式）
COL_WIDTH_MODEL = 38     # 模型名称列宽（多API模式下减少以容纳API名称）
COL_WIDTH_TIME = 9
COL_WIDTH_ERROR = 12
COL_WIDTH_CONTENT = 35   # 响应内容列宽（多API模式下减少以容纳API名称）

# 表格总宽度（用于分隔线）
# 单API模式：45 + 9 + 12 + 40 + 6 = 112
# 多API模式：12 + 38 + 9 + 12 + 35 + 8 = 114
TABLE_WIDTH = COL_WIDTH_MODEL + COL_WIDTH_TIME + COL_WIDTH_ERROR + COL_WIDTH_CONTENT + 6  # 6个分隔符空格
TABLE_WIDTH_MULTI_API = COL_WIDTH_API_NAME + COL_WIDTH_MODEL + COL_WIDTH_TIME + COL_WIDTH_ERROR + COL_WIDTH_CONTENT + 8  # 8个分隔符空格

# 通用分隔线宽度
SEPARATOR_WIDTH = 110
SEPARATOR_WIDTH_MULTI_API = 114  # 多API模式分隔线宽度

# ============================================
# 测试默认值
# ============================================

# 默认测试消息
DEFAULT_TEST_MESSAGE = "hello"

# 默认超时时间（秒）
DEFAULT_TIMEOUT = 30

# 默认请求延迟（秒）- 避免触发速率限制
DEFAULT_REQUEST_DELAY = 3.0

# 默认最大重试次数（429错误）
DEFAULT_MAX_RETRIES = 3

# 默认输出文件
DEFAULT_OUTPUT_FILE = "test_results.txt"

# ============================================
# 测试资源URL
# ============================================

# 默认测试图片URL（用于视觉模型测试）
DEFAULT_TEST_IMAGE_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/320px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg"

# 默认视觉模型测试消息
DEFAULT_VISION_MESSAGE = "What's in this image?"

# 默认图像生成提示词
DEFAULT_IMAGE_GEN_PROMPT = "a white cat"

# 默认嵌入测试文本
DEFAULT_EMBEDDING_TEXT = "hello world"

# ============================================
# API端点
# ============================================

API_ENDPOINT_MODELS = "/v1/models"
API_ENDPOINT_CHAT = "/v1/chat/completions"
API_ENDPOINT_EMBEDDINGS = "/v1/embeddings"
API_ENDPOINT_IMAGES = "/v1/images/generations"
API_ENDPOINT_AUDIO_TRANSCRIPTIONS = "/v1/audio/transcriptions"
API_ENDPOINT_AUDIO_SPEECH = "/v1/audio/speech"

# ============================================
# 错误分类
# ============================================

ERROR_CATEGORIES = {
    'HTTP_403': '权限拒绝/未授权',
    'HTTP_400': '请求参数错误',
    'HTTP_429': '速率限制',
    'HTTP_404': '模型不存在',
    'HTTP_500': '服务器内部错误',
    'HTTP_503': '服务不可用',
    'HTTP_554': '服务器错误',
    'TIMEOUT': '请求超时',
    'NO_CONTENT': '无响应内容',
    'NO_DATA': '无响应数据',
    'REQUEST_FAILED': '请求失败',
    'CONN_FAILED': '连接失败',
    'UNKNOWN_ERROR': '未知错误',
    'SKIPPED': '跳过测试(失败次数过多)',
    'HTTP_ERROR': 'HTTP错误'
}

# ============================================
# 分析和评分常量
# ============================================

# 健康度评分等级
GRADE_A_THRESHOLD = 90
GRADE_B_THRESHOLD = 80
GRADE_C_THRESHOLD = 70
GRADE_D_THRESHOLD = 60

# 健康度评分权重
HEALTH_SCORE_WEIGHTS = {
    'success_rate': 0.5,
    'response_speed': 0.3,
    'stability': 0.2
}

# 告警阈值
DEFAULT_ALERT_THRESHOLDS = {
    'min_success_rate': 0.5,  # 最低成功率50%
    'max_avg_response_time': 5.0,  # 最大平均响应时间5秒
    'max_429_errors': 50,  # 最多429错误50个
    'max_403_errors': 100,  # 最多403错误100个
    'max_timeout_errors': 20  # 最多超时错误20个
}

# ============================================
# 性能常量
# ============================================

# 日志文件最大大小（字节）
LOG_FILE_MAX_BYTES = 10 * 1024 * 1024  # 10MB

# 日志文件备份数量
LOG_FILE_BACKUP_COUNT = 5

# 速率限制默认值
DEFAULT_RPM = 60  # 每分钟请求数
MIN_RPM = 10
MAX_RPM = 120

# 重试相关
RETRY_BACKOFF_FACTOR = 2.0
RETRY_DEFAULT_DELAY = 1.0

# 并发测试默认值
DEFAULT_API_CONCURRENT = 1  # 默认不并发测试多个API（顺序测试）

# ============================================
# 模型类型
# ============================================

MODEL_TYPE_LANGUAGE = 'language'
MODEL_TYPE_VISION = 'vision'
MODEL_TYPE_AUDIO = 'audio'
MODEL_TYPE_EMBEDDING = 'embedding'
MODEL_TYPE_IMAGE_GENERATION = 'image_generation'
MODEL_TYPE_RERANKER = 'reranker'
MODEL_TYPE_MODERATION = 'moderation'
MODEL_TYPE_OTHER = 'other'

# ============================================
# HTTP状态码
# ============================================

HTTP_OK = 200
HTTP_BAD_REQUEST = 400
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_METHOD_NOT_ALLOWED = 405
HTTP_TOO_MANY_REQUESTS = 429
HTTP_INTERNAL_ERROR = 500
HTTP_SERVICE_UNAVAILABLE = 503
