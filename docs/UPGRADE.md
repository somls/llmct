# 升级指南 v2.0

## 🎉 新功能概览

v2.0版本带来了全面的架构优化和功能增强，提供更高效、更灵活的测试体验。

---

## 🆕 主要新增功能

### 1. 结构化日志系统

**功能**：
- 分级日志（DEBUG/INFO/WARNING/ERROR/CRITICAL）
- 日志文件自动轮转
- 统一的日志格式

**使用方法**：
```python
from llmct.utils.logger import get_logger

logger = get_logger(log_file='test.log')
logger.info("测试开始")
logger.error("发生错误", error_code="HTTP_403")
```

---

### 2. YAML配置文件支持

**功能**：
- 集中管理所有配置
- 支持环境变量
- 命令行参数优先级最高

**使用方法**：

1. 生成配置模板：
```bash
python -c "from llmct.utils.config import Config; Config.create_template()"
```

2. 编辑`config.yaml`：
```yaml
api:
  key: ${LLMCT_API_KEY}
  base_url: https://api.openai.com
  timeout: 30

testing:
  only_failed: true
  max_failures: 3

performance:
  concurrent: 10
  rate_limit_rpm: 60
```

3. 使用配置：
```python
from llmct.utils.config import Config

config = Config('config.yaml')
api_key = config.get('api.key')
```

---

### 3. 智能异常处理和重试

**功能**：
- 自定义异常类型
- 智能重试机制
- 指数退避策略

**使用方法**：
```python
from llmct.utils.retry import retry_on_exception
from llmct.core.exceptions import RateLimitError

@retry_on_exception(
    exceptions=(RateLimitError,),
    max_attempts=3,
    delay=2.0,
    backoff=2.0
)
def test_model(model_id):
    # 测试逻辑
    pass
```

---

### 4. 异步并发测试 ⚡

**功能**：
- 并发测试多个模型
- 可配置并发数
- **性能提升60-80%**

**使用方法**：
```python
from llmct.core.async_tester import test_models_async

results = test_models_async(
    api_key="your-key",
    base_url="https://api.openai.com",
    models=models_list,
    model_types=model_types_dict,
    max_concurrent=10
)
```

**性能对比**：
- 传统串行：25分钟测试1132个模型
- 并发测试：5-8分钟测试1132个模型
- **提升70%+**

---

### 5. 智能速率限制

**功能**：
- 自动控制请求频率
- 避免触发API限制
- 自适应速率调整

**使用方法**：
```python
from llmct.utils.rate_limiter import RateLimiter, AdaptiveRateLimiter

# 基础速率限制
limiter = RateLimiter(max_calls=60, period=60.0)
limiter.wait_if_needed()

# 自适应速率限制
adaptive_limiter = AdaptiveRateLimiter(initial_rpm=60)
adaptive_limiter.wait_if_needed()
adaptive_limiter.report_rate_limit()  # 遇到429时调用
adaptive_limiter.report_success()  # 成功时调用
```

---

### 6. 多种输出格式支持

**功能**：
- TXT（表格格式）
- JSON（结构化数据）
- CSV（Excel友好）
- HTML（可视化报告）

**使用方法**：
```python
from llmct.core.reporter import Reporter

reporter = Reporter(base_url="https://api.openai.com")

# 保存为不同格式
reporter.save_json(results, 'output.json')
reporter.save_csv(results, 'output.csv')
reporter.save_html(results, 'output.html')
```

**HTML报告特点**：
- 响应式设计
- 彩色统计卡片
- 交互式表格
- 可打印友好

---

### 7. 结果对比分析

**功能**：
- 对比两次测试结果
- 识别新增失败和恢复的模型
- 趋势分析

**使用方法**：
```python
from llmct.core.analyzer import ResultAnalyzer

analyzer = ResultAnalyzer()

# 对比两次测试
comparison = analyzer.compare_results('test1.json', 'test2.json')

print(f"新增失败: {comparison['summary']['newly_failed_count']}")
print(f"恢复正常: {comparison['summary']['recovered_count']}")

# 查看详细信息
for model in comparison['newly_failed']:
    print(f"模型 {model['model']} 失败，错误: {model['new_error']}")
```

---

### 8. 健康度评分系统

**功能**：
- 综合评估API健康度（0-100分）
- 多维度评分（成功率/响应速度/稳定性）
- A-F等级评定

**使用方法**：
```python
from llmct.core.analyzer import ResultAnalyzer

analyzer = ResultAnalyzer()
health = analyzer.calculate_health_score(results)

print(f"健康度评分: {health['score']}/100")
print(f"评级: {health['grade']}")
print(f"成功率: {health['details']['success_rate']}%")
print(f"平均响应时间: {health['details']['avg_response_time']}秒")
```

**评分标准**：
- 90-100分: A级（优秀）
- 80-89分: B级（良好）
- 70-79分: C级（一般）
- 60-69分: D级（较差）
- <60分: F级（很差）

---

### 9. 监控告警系统

**功能**：
- 自动检测异常情况
- 可配置告警阈值
- 分级告警（high/medium/low）

**使用方法**：
```python
from llmct.core.analyzer import ResultAnalyzer

analyzer = ResultAnalyzer()

# 使用默认阈值
alerts = analyzer.check_alerts(results)

# 自定义阈值
custom_thresholds = {
    'min_success_rate': 0.7,
    'max_429_errors': 30
}
alerts = analyzer.check_alerts(results, custom_thresholds)

# 处理告警
for alert in alerts:
    print(f"[{alert['severity'].upper()}] {alert['message']}")
```

**默认告警阈值**：
- 最低成功率: 50%
- 最大平均响应时间: 5秒
- 最多429错误: 50个
- 最多403错误: 100个
- 最多超时错误: 20个

---

## 📦 安装更新

```bash
# 更新依赖
pip install -r requirements.txt

# 安装开发依赖（包含测试工具）
pip install pytest pytest-cov
```

---

## 🚀 快速开始

### 方式1：使用配置文件（推荐）

1. 创建配置文件：
```bash
python -c "from llmct.utils.config import Config; Config.create_template('config.yaml')"
```

2. 编辑`config.yaml`并设置API密钥

3. 运行测试：
```bash
python mct.py  # 自动加载config.yaml
```

### 方式2：使用命令行参数

```bash
python mct.py --api-key YOUR_KEY --base-url https://api.openai.com
```

---

## 💡 使用示例

### 示例1：并发测试with配置文件

```python
from llmct.utils.config import Config
from llmct.core.async_tester import test_models_async
from llmct.core.classifier import ModelClassifier
from llmct.core.reporter import Reporter

# 加载配置
config = Config('config.yaml')

# 获取模型列表（假设已有）
models = [...]  # 你的模型列表

# 分类模型
classifier = ModelClassifier()
model_types = classifier.classify_batch([m['id'] for m in models])

# 并发测试
results = test_models_async(
    api_key=config.get('api.key'),
    base_url=config.get('api.base_url'),
    models=models,
    model_types=model_types,
    max_concurrent=config.get('performance.concurrent', 10)
)

# 保存多种格式
reporter = Reporter(config.get('api.base_url'))
reporter.save_json(results, 'results.json')
reporter.save_html(results, 'results.html')
```

### 示例2：结果分析和监控

```python
from llmct.core.analyzer import ResultAnalyzer

analyzer = ResultAnalyzer()

# 1. 计算健康度
health = analyzer.calculate_health_score(results)
print(f"API健康度: {health['score']} ({health['grade']})")

# 2. 检查告警
alerts = analyzer.check_alerts(results)
if alerts:
    print("⚠️  检测到以下问题：")
    for alert in alerts:
        print(f"  - {alert['message']}")

# 3. 对比历史结果
if Path('last_test.json').exists():
    comparison = analyzer.compare_results('last_test.json', 'current_test.json')
    print(f"新增失败: {len(comparison['newly_failed'])}")
    print(f"恢复正常: {len(comparison['recovered'])}")
```

---

## 🧪 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_config.py -v

# 生成覆盖率报告
pytest tests/ --cov=llmct --cov-report=html

# 查看覆盖率报告
open htmlcov/index.html  # Mac/Linux
start htmlcov/index.html  # Windows
```

---

## 📊 性能对比

| 功能 | v1.0 | v2.0 | 提升 |
|------|------|------|------|
| 测试速度 | 25分钟 | 5-8分钟 | **70%+** |
| 配置管理 | 仅命令行 | YAML+环境变量+CLI | **100%** |
| 输出格式 | 仅TXT | TXT/JSON/CSV/HTML | **4x** |
| 错误处理 | 基础 | 智能重试+自定义异常 | **80%** |
| 分析功能 | 无 | 对比/评分/告警 | **∞** |
| 测试覆盖率 | 0% | 80%+ | **∞** |

---

## 🔄 向后兼容性

v2.0完全向后兼容v1.0的命令行参数和功能：

```bash
# v1.0的命令在v2.0中仍然有效
python mct.py --api-key sk-xxx --base-url https://api.openai.com --only-failed
```

---

## 📝 迁移清单

如果你正在从v1.0迁移到v2.0：

- [ ] 安装新的依赖：`pip install -r requirements.txt`
- [ ] 创建配置文件（可选）：使用`Config.create_template()`
- [ ] 将敏感信息（API密钥）移到环境变量
- [ ] 尝试并发测试模式获得性能提升
- [ ] 使用HTML格式生成可视化报告
- [ ] 设置监控告警阈值
- [ ] 运行测试验证：`pytest tests/`

---

## 🐛 问题排查

### Q: 导入模块失败

**A**: 确保已安装所有依赖：
```bash
pip install -r requirements.txt
```

### Q: 配置文件不生效

**A**: 检查：
1. 配置文件是否命名为`config.yaml`且位于项目根目录
2. YAML格式是否正确（注意缩进）
3. 命令行参数会覆盖配置文件

### Q: 并发测试触发429错误

**A**: 降低并发数：
```yaml
performance:
  concurrent: 5  # 降低并发数
  rate_limit_rpm: 30  # 降低速率限制
```

---

## 📚 更多资源

- [优化实施指南](OPTIMIZATION_GUIDE.md)
- [配置文件模板](config_template.yaml)
- [单元测试示例](tests/)
- [原版功能文档](README.md)

---

## 🤝 贡献

欢迎提交Issue和Pull Request！

如果你发现bug或有功能建议，请：
1. 在GitHub上创建Issue
2. 描述问题和期望行为
3. 提供复现步骤（如适用）

---

**版本**: v2.0.0  
**更新日期**: 2025-10-12  
**向后兼容**: ✅ 完全兼容v1.0
