# LLMCT - 大模型连通性测试工具

> 🚀 大模型API测试工具

[![Python](https://img.shields.io/badge/Python-3.7%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-Passing-brightgreen)](tests/)
[![Code Quality](https://img.shields.io/badge/Code%20Quality-A-brightgreen)]()

## ✨ 特性

### 核心功能
- 🔍 **自动模型发现** - 自动获取并识别所有可用模型
- 🎯 **智能分类** - 支持7种模型类型（语言/视觉/音频/嵌入/图像生成/重排/审核）
- 📊 **多格式报告** - TXT、JSON、CSV、HTML输出
- 📈 **自动分析报告** - 测试完成后自动生成API健康度评分和告警
- 📝 **统一日志** - 完整的日志记录系统
- ⚡ **实时测试** - 专注实时测试，简洁高效

## 🚀 快速开始

### 安装

```bash
git clone <repository>
cd LLMCT
pip install -r requirements.txt
```

### 基础使用

```bash
# 基础测试
python mct.py --api-key sk-xxx --base-url https://api.openai.com

# 保存结果到不同格式
python mct.py --api-key sk-xxx --base-url https://api.openai.com --output results.json
python mct.py --api-key sk-xxx --base-url https://api.openai.com --output results.html
python mct.py --api-key sk-xxx --base-url https://api.openai.com --output results.csv

# 跳过特定类型的模型测试
python mct.py --api-key sk-xxx --base-url https://api.openai.com --skip-vision --skip-audio

# 调整请求延迟以适应API速率限制
python mct.py --api-key sk-xxx --base-url https://api.openai.com --request-delay 1.0
```

### 配置文件

创建 `config.yaml`：

```yaml
api:
  key: ${LLMCT_API_KEY}
  base_url: https://api.openai.com
  timeout: 30

testing:
  message: "hello"
  skip_vision: false
  skip_audio: false

output:
  file: test_results.txt
  format: txt  # txt, json, csv, html

performance:
  retry_times: 3
  retry_delay: 5
```

运行：

```bash
python mct.py  # 自动加载 config.yaml
```

---

---

## 📖 文档

### 快速链接
- 📘 [使用指南](docs/USAGE.md) - 详细教程、示例与最佳实践
- 🚨 [错误信息说明](docs/ERRORS.md) - 常见错误成因与排查建议
- 🔁 [升级指南](docs/UPGRADE.md) - 版本特性与迁移步骤
- 📝 [变更日志](CHANGELOG.md) - 历史更新记录

---

## 💡 使用场景

### API健康检查
```bash
# 快速健康检查
python mct.py --api-key sk-xxx --base-url https://api.openai.com --output health_check.json

# 查看自动生成的分析报告
cat health_check_analysis.json
```

### 问题排查
```bash
# 生成HTML报告便于查看
python mct.py --api-key sk-xxx --base-url https://api.openai.com --output debug.html
```

### 性能基准
```bash
# 生成详细JSON报告
python mct.py --api-key sk-xxx --base-url https://api.openai.com --output benchmark.json
```

---

## 🎯 输出示例

### 控制台输出
```
==================================================================================================================
大模型连通性和可用性测试 [精简版]
Base URL: https://api.openai.com
测试时间: 2025-01-17 10:30:00
==================================================================================================================

共发现 150 个模型

模型名称                          响应时间    错误信息    响应内容
------------------------------------------------------------------------------------------------------------------
gpt-4o                          1.23秒      -           Hello! How can I help you?
gpt-4-turbo                     1.45秒      -           Hi there! I'm ready to assist
test-model                      -           HTTP_403    

测试完成 | 总计: 150 | 成功: 120 | 失败: 30 | 成功率: 80.0%
==================================================================================================================

==================================================================================================================
📊 测试分析报告
==================================================================================================================

🏥 API健康度评分
------------------------------------------------------------------------------------------------------------------
综合评分: 85.5/100 (等级: B)
  - 成功率评分: 90.0/100
  - 响应速度评分: 82.5/100
  - 稳定性评分: 78.0/100
平均响应时间: 1.35秒

✅ 无告警

[信息] 详细分析报告已保存到: test_results_analysis.json
==================================================================================================================
```

### HTML报告

<img src="docs/images/html-report.png" width="600" alt="HTML报告示例">

---

## 🔧 命令参数

### 必需参数
- `--api-key` - API密钥
- `--base-url` - API基础URL

### 测试配置
- `--message TEXT` - 测试消息（默认："hello"）
- `--timeout N` - 超时时间（秒，默认30）
- `--request-delay N` - 请求之间的延迟（秒，默认1.0）
- `--max-retries N` - 429错误最大重试次数（默认3）

### 输出格式
- `--output FILE` - 输出文件路径
  - `.txt` - 文本格式（默认）
  - `.json` - JSON格式
  - `.csv` - CSV格式
  - `.html` - HTML格式

### 模型过滤
- `--skip-vision` - 跳过视觉模型测试
- `--skip-audio` - 跳过音频模型测试
- `--skip-embedding` - 跳过嵌入模型测试
- `--skip-image-gen` - 跳过图像生成模型测试

### 示例
```bash
# 查看所有参数
python mct.py --help

# 完整示例
python mct.py \
  --api-key sk-xxx \
  --base-url https://api.openai.com \
  --message "测试消息" \
  --timeout 60 \
  --request-delay 2.0 \
  --output results.html \
  --skip-vision
```

---

## 🧪 测试

```bash
# 运行单元测试
pytest tests/ -v

# 测试覆盖率
pytest tests/ --cov=llmct --cov-report=html
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

**版本:** v2.3.0 (精简版)
