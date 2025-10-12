# LLMCT - 大模型连通性测试工具

> 🚀 高性能、模块化的大语言模型API测试工具

[![Python](https://img.shields.io/badge/Python-3.7%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-Passing-brightgreen)](tests/)
[![Code Quality](https://img.shields.io/badge/Code%20Quality-A-brightgreen)]()

## ✨ 特性

### 核心功能
- 🔍 **自动模型发现** - 自动获取并识别所有可用模型
- 🎯 **智能分类** - 支持7种模型类型（语言/视觉/音频/嵌入/图像生成/重排/审核）
- 💾 **高性能缓存** - SQLite批量缓存，查询速度提升25倍
- 🔄 **失败追踪** - 智能跳过持续失败的模型，节省时间
- 📊 **多格式报告** - TXT、JSON、CSV、HTML输出
- 📝 **统一日志** - 完整的日志记录系统

---

## 🚀 快速开始

### 安装

```bash
git clone <repository>
cd LLMCT
pip install -r requirements.txt
```

### 基础使用

#### 同步测试（推荐用于大多数场景）

```bash
# 全量测试
python mct.py --api-key sk-xxx --base-url https://api.openai.com

# 仅测试失败模型（推荐）
python mct.py --api-key sk-xxx --base-url https://api.openai.com --only-failed

# 跳过持续失败的模型
python mct.py --api-key sk-xxx --base-url https://api.openai.com --max-failures 3

# 调整请求延迟以适应API速率限制
python mct.py --api-key sk-xxx --base-url https://api.openai.com --request-delay 1.0
```

#### 异步测试（适合大规模测试）⚡

```bash
# 异步并发测试（自动调整并发数）
python mct_async.py --api-key sk-xxx --base-url https://api.openai.com --concurrency 5

# 仅测试失败模型（异步）
python mct_async.py --api-key sk-xxx --base-url https://api.openai.com --only-failed

# 低并发模式（适合严格速率限制的API）
python mct_async.py --api-key sk-xxx --base-url https://api.openai.com --concurrency 1
```

### 配置文件

创建 `config.yaml`：

```yaml
api:
  key: ${LLMCT_API_KEY}
  base_url: https://api.openai.com
  timeout: 30

testing:
  only_failed: true
  max_failures: 3

cache:
  enabled: true
  duration_hours: 24

output:
  format: html
```

运行：

```bash
python mct.py  # 自动加载 config.yaml
```

---

---

## 📖 文档

### 快速链接
- 📘 [完整使用指南](docs/USAGE.md) - 详细教程和最佳实践
- ⚡ [性能优化指南](docs/OPTIMIZATION.md) - 优化功能说明
- 🧪 [实测分析报告](FINAL_TEST_ANALYSIS.md) - 真实API测试结果与建议
- 🔧 [升级指南](docs/UPGRADE.md) - 版本升级说明
- ❌ [错误说明](docs/ERRORS.md) - 错误类型和解决方案
- 📋 [失败追踪](docs/FAILURE_TRACKING.md) - 失败追踪机制
- 📝 [变更日志](CHANGELOG.md) - 版本历史

### 重构文档 (v2.2.0+)
- 🔍 [项目深度分析](PROJECT_ANALYSIS.md) - 完整的代码和架构分析
- 📖 [重构指南](REFACTORING_GUIDE.md) - 详细的重构步骤
- ✅ [重构完成报告](REFACTORING_COMPLETE.md) - Phase 1成果
- 🎯 [Phase 2报告](REFACTORING_PHASE2.md) - Phase 2成果
- 📊 [优化总结](OPTIMIZATION_SUMMARY.md) - 执行摘要

### 文档索引
- [完整文档列表](DOCS_INDEX.md)

---

## 💡 使用场景

### 日常监控
```bash
# 周一：全量测试建立基线
python mct.py --reset-failures

# 周二-周五：智能增量测试
python mct.py --only-failed --max-failures 3
```

### 问题排查
```bash
# 专注于可恢复的模型
python mct.py --only-failed --max-failures 3 --output debug.html
```

### 性能基准
```bash
# 生成详细报告
python mct.py --output benchmark.json
```

---

## 🎯 输出示例

### 控制台输出
```
============================================================
大模型连通性和可用性测试
============================================================

共发现 1132 个模型，筛选出 867 个失败模型进行测试
测试模式: 仅测试失败模型
失败阈值: 跳过失败3次以上的模型

模型名称                          响应时间    错误信息
----------------------------------------------------------
gpt-4o                          1.23秒      -
gpt-4-turbo                     1.45秒      -
claude-3-opus                   -           SKIPPED
test-model                      -           HTTP_403

测试完成 | 总计: 867 | 成功: 567 | 失败: 200 | 跳过: 100
成功率: 65.4%
```

### HTML报告

<img src="docs/images/html-report.png" width="600" alt="HTML报告示例">

---

## 🔧 命令参数

### mct.py（同步测试）

#### 必需参数
- `--api-key` - API密钥
- `--base-url` - API基础URL

#### 测试策略
- `--only-failed` - 仅测试失败模型
- `--max-failures N` - 跳过失败N次以上的模型
- `--reset-failures` - 重置失败计数
- `--request-delay N` - 请求之间的延迟（秒，默认10.0）

#### 缓存控制
- `--no-cache` - 禁用缓存
- `--cache-duration N` - 缓存有效期（小时）
- `--clear-cache` - 清除缓存

#### 输出格式
- `--output FILE` - 输出文件
- `--format txt|json|csv|html` - 输出格式

#### 其他
- `--timeout N` - 超时时间（秒）
- `--message TEXT` - 测试消息
- `--skip-vision` - 跳过视觉模型
- `--skip-audio` - 跳过音频模型
- `--max-retries N` - 429错误最大重试次数（默认3）

### mct_async.py（异步测试）⚡

#### 必需参数
- `--api-key` - API密钥
- `--base-url` - API基础URL

#### 特有参数
- `--concurrency N` - 初始并发数（默认10，会自动调整）
- `--only-failed` - 仅测试失败模型
- `--max-failures N` - 跳过失败N次以上的模型
- `--no-cache` - 禁用缓存

完整参数列表：
- `python mct.py --help`
- `python mct_async.py --help`

---

## 🧪 测试

```bash
# 运行单元测试
pytest tests/ -v

# 测试覆盖率
pytest tests/ --cov=llmct --cov-report=html

# 验证优化功能
python test_optimizations.py
```

---

## 🤝 贡献

欢迎贡献！请遵循以下步骤：

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 编写测试并确保通过
4. 提交更改 (`git commit -m 'Add AmazingFeature'`)
5. 推送到分支 (`git push origin feature/AmazingFeature`)
6. 开启 Pull Request

---

## 📜 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

感谢所有贡献者和用户的支持！

---

## 📞 支持

- 📖 查看 [文档](docs/)
- 🐛 提交 [Issue](https://github.com/your-repo/issues)
- 💬 加入讨论

---

<p align="center">
  <strong>⭐ 如果这个项目对你有帮助，请给一个 Star！</strong>
</p>

---

**Python版本:** 3.7+
