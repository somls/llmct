# 📚 文档索引

> 完整的LLMCT文档导航

---

## 🚀 快速开始

### 新用户必读
1. **[README.md](README.md)** ⭐⭐⭐⭐⭐  
   项目介绍、安装、快速开始、核心功能

2. **[docs/USAGE.md](docs/USAGE.md)** ⭐⭐⭐⭐⭐  
   完整使用指南、参数说明、最佳实践

---

## 📖 核心文档

### 功能说明
- **[docs/USAGE.md](docs/USAGE.md)** - 详细使用教程  
  *内容：* 参数说明、使用场景、最佳实践、高级技巧  
  *适合：* 所有用户

- **[docs/FAILURE_TRACKING.md](docs/FAILURE_TRACKING.md)** - 失败追踪机制  
  *内容：* 失败追踪原理、使用方法、性能对比  
  *适合：* 想优化测试效率的用户

- **[docs/ERRORS.md](docs/ERRORS.md)** - 错误说明  
  *内容：* 13种错误类型、原因分析、解决方案  
  *适合：* 遇到测试错误的用户

### 性能优化
- **[docs/OPTIMIZATION.md](docs/OPTIMIZATION.md)** ⭐ NEW  
  *内容：* 优化功能说明、使用指南、性能对比、故障排查  
  *适合：* 需要高性能测试的用户  
  *版本：* v2.1.0+

### 版本升级
- **[docs/UPGRADE.md](docs/UPGRADE.md)** - 升级指南  
  *内容：* 版本升级步骤、兼容性说明、迁移指南  
  *适合：* v1.0用户升级到v2.x

- **[CHANGELOG.md](CHANGELOG.md)** - 版本历史  
  *内容：* 所有版本的变更记录、新功能、修复  
  *适合：* 了解项目演进

---

## 🔍 按需查找

### 我想...

#### 🎯 开始使用
👉 阅读 [README.md](README.md) → [docs/USAGE.md](docs/USAGE.md)

#### 🚀 提升性能
👉 阅读 [docs/OPTIMIZATION.md](docs/OPTIMIZATION.md)

#### ❌ 解决错误
👉 查看 [docs/ERRORS.md](docs/ERRORS.md)

#### 📈 优化测试策略
👉 阅读 [docs/FAILURE_TRACKING.md](docs/FAILURE_TRACKING.md)

#### 🔄 版本升级
👉 查看 [docs/UPGRADE.md](docs/UPGRADE.md) + [CHANGELOG.md](CHANGELOG.md)

#### 💻 代码集成
👉 查看 [examples/](examples/) 目录

---

## 📂 文档结构

```
LLMCT/
├── README.md                    # 项目主页
├── CHANGELOG.md                 # 版本历史
├── DOCS_INDEX.md               # 本文档
├── docs/                        # 详细文档
│   ├── USAGE.md                # 使用指南
│   ├── OPTIMIZATION.md         # 优化指南 [NEW]
│   ├── UPGRADE.md              # 升级指南
│   ├── ERRORS.md               # 错误说明
│   └── FAILURE_TRACKING.md     # 失败追踪
├── examples/                    # 代码示例
│   └── example_usage.py        # 使用示例
└── tests/                       # 单元测试
    └── ...
```

---

## 📘 推荐阅读路径

### 路径 1: 新手入门
1. [README.md](README.md) - 5分钟了解项目
2. [docs/USAGE.md](docs/USAGE.md) - 15分钟掌握基础
3. [docs/FAILURE_TRACKING.md](docs/FAILURE_TRACKING.md) - 10分钟学习核心功能

**总计：** 30分钟快速上手

---

### 路径 2: 性能优化
1. [docs/OPTIMIZATION.md](docs/OPTIMIZATION.md) - 20分钟了解优化功能
2. [docs/USAGE.md](docs/USAGE.md) - 参考高级用法
3. [CHANGELOG.md](CHANGELOG.md) - 查看优化细节

**总计：** 30分钟掌握性能优化

---

### 路径 3: 问题解决
1. [docs/ERRORS.md](docs/ERRORS.md) - 查找错误解决方案
2. [docs/FAILURE_TRACKING.md](docs/FAILURE_TRACKING.md) - 理解失败机制
3. [docs/USAGE.md](docs/USAGE.md) - 参考使用场景

**总计：** 15分钟解决问题

---

### 路径 4: 版本升级
1. [CHANGELOG.md](CHANGELOG.md) - 查看版本变更
2. [docs/UPGRADE.md](docs/UPGRADE.md) - 按步骤升级
3. [docs/OPTIMIZATION.md](docs/OPTIMIZATION.md) - 了解新功能

**总计：** 20分钟完成升级

---

## 🎓 技术文档

### 代码示例
- **[examples/example_usage.py](examples/example_usage.py)** - 功能演示  
  包含7个实用示例

### 测试代码
- **[tests/](tests/)** - 单元测试  
  覆盖率80%+，21个测试用例

- **[test_optimizations.py](test_optimizations.py)** - 优化功能测试  
  验证v2.1.0优化功能

---

## 📊 文档统计

| 类型 | 数量 | 说明 |
|------|------|------|
| 主文档 | 2个 | README + CHANGELOG |
| 详细文档 | 5个 | docs/目录 |
| 代码示例 | 1个 | examples/目录 |
| 测试脚本 | 2个 | 测试相关 |
| **总计** | **10个** | **完整文档体系** |

---

## ⚡ 快速命令

### 查看文档
```bash
# 主文档
cat README.md
cat CHANGELOG.md

# 详细文档
cat docs/USAGE.md
cat docs/OPTIMIZATION.md
cat docs/ERRORS.md

# 查看所有文档
ls -la docs/
```

### 运行示例
```bash
# 功能示例
python examples/example_usage.py

# 优化测试
python test_optimizations.py

# 单元测试
pytest tests/ -v
```

---

## 🔗 外部资源

- **GitHub Repository**: [链接]
- **Issues**: [链接]
- **Discussions**: [链接]

---

## 📝 文档维护

### 更新周期
- **主文档**: 每个版本更新
- **详细文档**: 功能变更时更新
- **CHANGELOG**: 每次发布更新

### 贡献指南
欢迎改进文档！请提交PR到文档相关文件。

---

## ❓ 常见问题

### Q: 文档在哪里？
**A:** 所有文档都在项目根目录和docs/目录中。

### Q: 如何找到特定功能的文档？
**A:** 使用本文档的"按需查找"部分快速定位。

### Q: 文档有多个版本吗？
**A:** 文档随代码版本同步，查看CHANGELOG了解各版本变更。

### Q: 如何离线查看文档？
**A:** 所有文档都是Markdown格式，可离线查看。

---

<p align="center">
  <strong>📖 需要帮助？从 <a href="README.md">README.md</a> 开始！</strong>
</p>

---

**文档版本:** v2.1.0  
**最后更新:** 2025-01-16  
**文档数量:** 10个  
**维护状态:** ✅ 活跃
