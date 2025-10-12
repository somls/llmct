# 📚 文档索引 (v2.3.0 精简版)

> 完整的LLMCT文档导航

---

## 🚀 快速开始

### 新用户必读
1. **[README.md](README.md)** ⭐⭐⭐⭐⭐  
   项目介绍、安装、快速开始、核心功能（精简版）

2. **[docs/USAGE.md](docs/USAGE.md)** ⭐⭐⭐⭐⭐  
   完整使用指南、自动分析报告、最佳实践

3. **[PROJECT_SIMPLIFICATION.md](PROJECT_SIMPLIFICATION.md)** ⭐⭐⭐  
   v2.3.0精简说明、新功能介绍、迁移指南

---

## 📖 核心文档

### 功能说明
- **[docs/USAGE.md](docs/USAGE.md)** - 详细使用教程（v2.3更新）  
  *内容：* 参数说明、自动分析报告、健康度评分、告警系统  
  *适合：* 所有用户

### v2.3.0 新功能
- **[PROJECT_SIMPLIFICATION.md](PROJECT_SIMPLIFICATION.md)** ⭐  
  *内容：* 精简说明、移除功能列表、新增自动分析报告、迁移建议  
  *适合：* 从旧版本升级的用户  
  *版本：* v2.3.0

### 历史文档（参考）
- **[FINAL_TEST_ANALYSIS.md](FINAL_TEST_ANALYSIS.md)**  
  *内容：* 真实API测试结果（v2.2.x版本）  
  *适合：* 历史参考  
  *注意：* 部分功能已在v2.3.0中移除

### 重构文档 (v2.2.1-v2.3.0) 🏗️
- **[REFACTORING_GUIDE.md](REFACTORING_GUIDE.md)** - 重构指南（v2.2.x）  
  *内容：* 详细重构步骤、代码示例、测试验证  
  *适合：* 想了解重构过程的开发者

- **[REFACTORING_COMPLETE.md](REFACTORING_COMPLETE.md)** - Phase 1报告  
  *内容：* 核心重构成果、性能提升数据  
  *适合：* 了解重构第一阶段成果

- **[REFACTORING_PHASE2.md](REFACTORING_PHASE2.md)** - Phase 2报告  
  *内容：* 功能增强、日志集成、Reporter优化  
  *适合：* 了解重构第二阶段成果

- **[OPTIMIZATION_SUMMARY.md](OPTIMIZATION_SUMMARY.md)** - 优化执行摘要  
  *内容：* 核心问题、关键指标、实施路线  
  *适合：* 快速了解优化全貌

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

#### 📊 使用分析报告
👉 阅读 [docs/USAGE.md](docs/USAGE.md) - 健康度评分和告警系统

#### 🔄 从v2.2升级到v2.3
👉 查看 [PROJECT_SIMPLIFICATION.md](PROJECT_SIMPLIFICATION.md) + [CHANGELOG.md](CHANGELOG.md)

#### 💻 代码集成
👉 查看 [examples/](examples/) 目录

#### 📜 版本历史
👉 查看 [CHANGELOG.md](CHANGELOG.md)

---

## 📂 文档结构

```
LLMCT/ (v2.3.0 精简版)
├── README.md                    # 项目主页（精简版）
├── CHANGELOG.md                 # 版本历史
├── DOCS_INDEX.md               # 本文档
├── PROJECT_SIMPLIFICATION.md   # v2.3.0精简说明 [NEW]
├── FINAL_TEST_ANALYSIS.md      # 实测分析报告 [v2.2.x历史参考]
├── REFACTORING_GUIDE.md        # 重构指南 [v2.2.1]
├── REFACTORING_COMPLETE.md     # Phase 1报告 [v2.2.1]
├── REFACTORING_PHASE2.md       # Phase 2报告 [v2.2.1]
├── OPTIMIZATION_SUMMARY.md     # 优化执行摘要 [v2.2.1]
├── mct.py                       # 主程序（精简版，含自动分析报告）
├── docs/                        # 详细文档
│   ├── USAGE.md                # 使用指南（v2.3更新）
│   └── UPGRADE.md              # 升级指南
├── examples/                    # 代码示例
│   └── example_usage.py        # 使用示例（v2.3更新）
├── llmct/                       # 核心模块
│   ├── core/                   # 核心功能（analyzer, reporter, classifier）
│   ├── utils/                  # 工具模块（logger, config, retry）
│   └── models/                 # 数据模型
└── tests/                       # 单元测试
    └── ...
```

---

## 📘 推荐阅读路径

### 路径 1: 新手入门（v2.3）
1. [README.md](README.md) - 5分钟了解精简版
2. [docs/USAGE.md](docs/USAGE.md) - 15分钟掌握基础和分析报告
3. [examples/example_usage.py](examples/example_usage.py) - 5分钟查看代码示例

**总计：** 25分钟快速上手

---

### 路径 2: 自动分析报告
1. [docs/USAGE.md](docs/USAGE.md) - 15分钟了解健康度评分和告警
2. [PROJECT_SIMPLIFICATION.md](PROJECT_SIMPLIFICATION.md) - 5分钟了解新功能
3. 运行实际测试查看报告

**总计：** 20分钟掌握分析功能

---

### 路径 3: 版本升级（v2.2→v2.3）
1. [PROJECT_SIMPLIFICATION.md](PROJECT_SIMPLIFICATION.md) - 10分钟了解变化
2. [CHANGELOG.md](CHANGELOG.md) - 5分钟查看详细变更
3. [docs/USAGE.md](docs/USAGE.md) - 参考新用法

**总计：** 15分钟完成升级

---

## 🎓 技术文档

### 代码示例
- **[examples/example_usage.py](examples/example_usage.py)** - 功能演示  
  包含7个实用示例

### 测试代码
- **[tests/](tests/)** - 单元测试  
  覆盖率80%+，21个测试用例

- **[scripts/test_optimizations.py](scripts/test_optimizations.py)** - 优化功能测试  
  验证优化功能

---

## 📊 文档统计（v2.3.0）

| 类型 | 数量 | 说明 |
|------|------|------|
| 主文档 | 4个 | README + CHANGELOG + DOCS_INDEX + SIMPLIFICATION |
| 功能文档 | 2个 | docs/目录（精简） |
| 历史文档 | 5个 | 重构和测试分析文档（参考） |
| 代码示例 | 1个 | examples/目录 |
| 测试脚本 | 多个 | tests/目录 |
| **总计** | **12+个** | **精简文档体系** |

**v2.3.0变化：**
- ❌ 移除：缓存、失败追踪、优化指南文档
- ✅ 新增：PROJECT_SIMPLIFICATION.md
- ✅ 更新：README.md, docs/USAGE.md, CHANGELOG.md

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
# 功能示例（v2.3更新）
python examples/example_usage.py

# 快速测试
python scripts/quick_test.py --api-key YOUR_KEY --base-url YOUR_URL

# 主程序测试
python mct.py --api-key YOUR_KEY --base-url YOUR_URL --output results.json

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

**最后更新:** 2025-10-12  
**版本:** v2.3.0（精简版）  
**文档数量:** 12个  
**维护状态:** ✅ 活跃
