# 按 Base URL 统计分析功能

## 功能概述

从 v2.4.0 开始，LLMCT 支持按 `base_url` 自动分类保存测试结果，并提供多次测试的成功率统计功能。

## 主要特性

### 1. 自动按 Base URL 分类保存

测试结果会自动保存到 `test_results/{base_url}/` 目录下，每次测试会生成一个带时间戳的文件。

**目录结构示例：**
```
test_results/
├── api.openai.com/
│   ├── test_20250103_143022.json
│   ├── test_20250103_150315.json
│   └── test_20250103_162045.json
├── api.anthropic.com/
│   ├── test_20250103_144530.json
│   └── test_20250103_155820.json
└── api.example.com_v1/
    └── test_20250103_120000.json
```

### 2. 多次测试成功率统计

系统会自动统计同一 base_url 下每个模型的：
- 总测试次数
- 成功次数
- 失败次数
- 成功率（百分比）
- 平均响应时间
- 错误代码分布

### 3. 历史测试结果分析

通过 `--analyze` 参数可以查看某个 base_url 的历史统计数据。

## 使用方法

### 执行测试（自动按 base_url 保存）

```bash
# 基础测试
python mct.py --api-key sk-xxx --base-url https://api.openai.com

# 测试结果会自动保存到：test_results/api.openai.com/test_YYYYMMDD_HHMMSS.json
```

### 查看历史统计

```bash
# 分析某个 base_url 的所有历史测试
python mct.py --analyze test_results/api.openai.com
```

**输出示例：**
```
==================================================================================================================
分析 test_results/api.openai.com 目录下的历史测试结果
==================================================================================================================

模型名称                                            | 测试次数     | 成功次数     | 失败次数     | 成功率      | 平均响应时间
------------------------------------------------------------------------------------------------------------------
gpt-4o                                              | 5          | 5          | 0          | 100.0%    |     1.23秒
gpt-4o-mini                                         | 5          | 5          | 0          | 100.0%    |     0.98秒
gpt-3.5-turbo                                       | 5          | 4          | 1          |  80.0%    |     1.15秒
text-embedding-ada-002                              | 5          | 5          | 0          | 100.0%    |     0.45秒
dall-e-3                                            | 5          | 3          | 2          |  60.0%    |     8.23秒

==================================================================================================================
总计: 5 个模型
==================================================================================================================

分析报告已保存: test_results/api.openai.com/analysis_20250103_163022.json
```

### 分析报告详情

分析报告会以 JSON 格式保存，包含详细的统计信息：

```json
{
  "summary": {
    "base_url_dir": "test_results/api.openai.com",
    "total_test_files": 5,
    "total_models": 25,
    "analysis_time": "2025-01-03T16:30:22.123456"
  },
  "model_statistics": {
    "gpt-4o": {
      "total_tests": 5,
      "success_tests": 5,
      "failed_tests": 0,
      "success_rate": 100.0,
      "avg_response_time": 1.23,
      "response_times": [1.20, 1.25, 1.22, 1.24, 1.23],
      "error_codes": {},
      "test_history": [
        {
          "test_time": "2025-01-03 14:30:22",
          "success": true,
          "response_time": 1.20,
          "error_code": ""
        },
        ...
      ]
    },
    ...
  }
}
```

## 应用场景

### 1. 监控 API 稳定性

定期运行测试，积累历史数据：

```bash
# 每小时运行一次测试
python mct.py --api-key sk-xxx --base-url https://api.openai.com
```

然后分析趋势：

```bash
# 查看累计统计
python mct.py --analyze test_results/api.openai.com
```

### 2. 对比不同 API 提供商

```bash
# 测试提供商 A
python mct.py --api-key key-a --base-url https://api.provider-a.com

# 测试提供商 B
python mct.py --api-key key-b --base-url https://api.provider-b.com

# 对比分析
python mct.py --analyze test_results/api.provider-a.com
python mct.py --analyze test_results/api.provider-b.com
```

### 3. 模型性能评估

通过多次测试识别：
- 最稳定的模型（成功率最高）
- 最快的模型（平均响应时间最短）
- 常见错误类型

## 注意事项

1. **时间戳格式**：文件名使用 `YYYYMMDD_HHMMSS` 格式确保唯一性
2. **目录命名**：URL 中的特殊字符会被转换为下划线
3. **最小测试次数**：默认只统计至少测试过 1 次的模型
4. **JSON 格式**：分析功能需要 JSON 格式的测试结果

## 高级用法

### 编程方式使用分析器

```python
from llmct.core.analyzer import ResultAnalyzer

analyzer = ResultAnalyzer()

# 分析某个 base_url
analysis = analyzer.analyze_by_base_url('test_results/api.openai.com')

# 获取成功率排名（至少测试 3 次）
ranked = analyzer.get_model_success_rates(
    'test_results/api.openai.com',
    min_tests=3
)

# 保存分析报告
analyzer.save_base_url_analysis(
    'test_results/api.openai.com',
    output_file='custom_analysis.json'
)
```

## 常见问题

### Q: 如何清理旧的测试结果？

直接删除对应目录下的旧文件：

```bash
# 仅保留最近 7 天的测试结果
find test_results/api.openai.com -name "test_*.json" -mtime +7 -delete
```

### Q: 能否合并多个 base_url 的统计？

当前版本不支持，每个 base_url 独立统计。如需合并，可以手动解析 JSON 文件。

### Q: 如何导出统计报告为 Excel？

可以使用 Python 脚本读取 JSON 并转换：

```python
import json
import pandas as pd

with open('test_results/api.openai.com/analysis_xxx.json') as f:
    data = json.load(f)

df = pd.DataFrame.from_dict(data['model_statistics'], orient='index')
df.to_excel('analysis_report.xlsx')
```

## 版本历史

- **v2.4.0** (2025-01-03)
  - 新增按 base_url 分类保存功能
  - 新增多次测试成功率统计
  - 新增 `--analyze` 命令行参数
  - 新增 `ResultAnalyzer` 类的 base_url 分析方法
