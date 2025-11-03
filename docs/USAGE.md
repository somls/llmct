# 使用指南

## 快速开始

### 基础测试
```bash
python mct.py \
  --api-key your-api-key \
  --base-url https://your-api-endpoint.com \
  --output test_results.txt
```

**预期结果：**
- 实时测试所有可用模型
- 生成详细的错误统计报告
- 自动生成API健康度评分和告警
- 保存详细分析报告到 `test_results_analysis.json`

### 生成不同格式的报告
```bash
# HTML格式（便于浏览器查看）
python mct.py \
  --api-key your-api-key \
  --base-url https://your-api-endpoint.com \
  --output report.html

# JSON格式（便于程序处理）
python mct.py \
  --api-key your-api-key \
  --base-url https://your-api-endpoint.com \
  --output report.json

# CSV格式（便于Excel分析）
python mct.py \
  --api-key your-api-key \
  --base-url https://your-api-endpoint.com \
  --output report.csv
```

## 核心功能演示

### 1. 错误分类统计

每次测试结束后，自动显示详细的错误统计：

```
==================================================================================================================
错误统计和分析
==================================================================================================================

错误类型               错误描述                       数量         占失败比例        占总数比例     
--------------------------------------------------------------------------------------------------------------
HTTP_403             权限拒绝/未授权                 25            50.0%          16.7%
HTTP_400             请求参数错误                    15            30.0%          10.0%
HTTP_429             速率限制                        10            20.0%           6.7%

总失败数                                              50           100.0%          33.3%
==================================================================================================================
```

**用途：**
- 快速定位主要问题（如权限配置）
- 了解API限制情况
- 评估模型可用性

### 2. 自动分析报告

每次测试完成后，自动生成分析报告：

#### 控制台输出
```
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

⚠️  告警信息
------------------------------------------------------------------------------------------------------------------
🟡 [MEDIUM] SLOW_RESPONSE: 平均响应时间过慢: 5.2秒 (阈值: 5.0秒)

[信息] 详细分析报告已保存到: test_results_analysis.json
==================================================================================================================
```

#### 分析报告文件（JSON）
自动生成 `*_analysis.json` 文件，包含：
- 完整的健康度评分详情
- 所有触发的告警列表
- 生成时间戳

```json
{
  "health_score": {
    "score": 85.5,
    "grade": "B",
    "details": {
      "success_score": 90.0,
      "speed_score": 82.5,
      "stability_score": 78.0,
      "success_rate": 90.0,
      "avg_response_time": 1.35
    }
  },
  "alerts": [],
  "timestamp": "2025-01-17T10:30:00"
}
```

## 实用场景

### 场景1：API健康检查
**目标：** 快速检查API整体健康状况

```bash
# 运行测试并生成分析报告
python mct.py \
  --api-key $API_KEY \
  --base-url $API_URL \
  --output health_check.json

# 查看健康度评分
cat health_check_analysis.json
```

**效果：**
- 获取API健康度评分（0-100分）
- 自动识别告警问题
- 了解成功率、响应速度、稳定性

### 场景2：问题排查
**目标：** 排查API访问问题

```bash
# 生成HTML报告便于查看
python mct.py \
  --api-key $API_KEY \
  --base-url $API_URL \
  --output debug.html

# 在浏览器中打开 debug.html 查看详细结果
```

**效果：**
- 可视化的错误分布
- 详细的错误信息
- 便于与团队分享

### 场景3：性能基准测试
**目标：** 评估API性能

```bash
# 生成JSON报告
python mct.py \
  --api-key $API_KEY \
  --base-url $API_URL \
  --output benchmark.json

# 查看详细分析
cat benchmark_analysis.json | jq '.health_score'
```

**效果：**
- 量化的性能指标
- 平均响应时间统计
- 便于性能追踪

### 场景4：跳过特定模型类型
**目标：** 只测试需要的模型类型

```bash
# 只测试语言模型，跳过其他类型
python mct.py \
  --api-key $API_KEY \
  --base-url $API_URL \
  --skip-vision \
  --skip-audio \
  --skip-embedding \
  --skip-image-gen \
  --output language_models.txt
```

**效果：**
- 节省测试时间
- 专注于特定模型类型
- 减少API调用次数

## 健康度评分说明

### 评分维度

健康度评分（0-100分）由三个维度组成：

| 维度 | 权重 | 说明 |
|-----|------|------|
| 成功率 | 50% | 模型测试成功的比例 |
| 响应速度 | 30% | 平均响应时间，目标<2秒 |
| 稳定性 | 20% | 错误分布的均匀程度 |

### 等级划分

| 分数 | 等级 | 评价 |
|-----|------|------|
| 90-100 | A | 优秀 |
| 80-89 | B | 良好 |
| 70-79 | C | 中等 |
| 60-69 | D | 较差 |
| <60 | F | 不及格 |

### 告警类型

| 告警类型 | 严重程度 | 触发条件 |
|---------|---------|---------|
| LOW_SUCCESS_RATE | 高 | 成功率 < 50% |
| SLOW_RESPONSE | 中 | 平均响应时间 > 5秒 |
| RATE_LIMIT | 高 | HTTP 429错误 > 50个 |
| PERMISSION_DENIED | 高 | HTTP 403错误 > 100个 |
| TIMEOUT | 中 | 超时错误 > 20个 |

## 常见问题

### Q1: 分析报告文件在哪里？
**A:** 自动保存在输出文件同目录，文件名为 `<输出文件名>_analysis.json`。
例如：`--output results.txt` 会生成 `results_analysis.json`

### Q2: 如何提高测试速度？
**A:** 
1. 使用 `--skip-vision` 等参数跳过不需要的模型类型
2. 减小 `--request-delay` 参数（默认3秒，需注意API速率限制）
3. 增加 `--timeout` 可以减少等待时间

### Q4: 如何批量测试多个API？
**A:** 
工具会自动检测配置。在 `config.yaml` 中配置 `apis` 列表即可：
```yaml
# 全局配置
testing:
  message: "hello"

# 配置多个API，工具自动启用批量测试
apis:
  - name: OpenAI
    key: ${OPENAI_API_KEY}
    base_url: https://api.openai.com
    enabled: true
  
  - name: DeepSeek
    key: ${DEEPSEEK_API_KEY}
    base_url: https://api.deepseek.com
    enabled: true
```
运行 `python mct.py`，工具会自动检测并批量测试所有启用的API。

### Q5: 多API配置时如何为不同API设置不同参数？
**A:** 
每个API可以覆盖全局配置：
```yaml
# 全局配置
testing:
  message: "hello"
  skip_vision: false

# API特定配置会覆盖全局配置
apis:
  - name: OpenAI
    key: ${OPENAI_API_KEY}
    base_url: https://api.openai.com
    timeout: 30
    request_delay: 3.0
    # 使用全局 testing 配置
  
  - name: LocalAPI
    key: sk-local
    base_url: http://localhost:8000
    timeout: 60
    request_delay: 1.0
    testing:  # 覆盖全局配置
      message: "你好"
      skip_vision: true
```

### Q6: 多API配置时，测试结果会保存到哪里？
**A:** 
无论单API还是多API模式，测试结果都会**自动按base_url分类保存**：

```
test_results/
├── api.openai.com/          ← OpenAI的所有测试结果
│   ├── test_20250103_143022.txt
│   └── test_20250103_150315.txt
├── api.deepseek.com/        ← DeepSeek的所有测试结果
│   └── test_20250103_144530.txt
└── localhost/               ← 本地API的所有测试结果
    └── test_20250103_151200.txt
```

### Q7: 如何并发测试多个API？（v2.5.0 新增）
**A:**
使用 `--api-concurrent` 参数控制多API并发数：

```bash
# 顺序测试（默认）- 一个API完成后再测试下一个
python mct.py

# 并发测试 - 同时测试3个API
python mct.py --api-concurrent 3
```

**并发模式显示格式：**
```
==================================================
多API并发测试模式
==================================================
并发API数: 3
==================================================

API名称      | 模型名称                            | 响应时间  | 错误信息   | 响应内容
--------------------------------------------------
OpenAI      | gpt-4                              | 1.23秒   | -         | Hello!...
Anthropic   | claude-3-opus                       | 1.45秒   | -         | Hi!...
DeepSeek    | deepseek-chat                      | 2.10秒   | -         | 你好！...
```

**双层并发说明：**
- **第1层并发**（`concurrent`）：每个API内部并发测试多个模型
- **第2层并发**（`--api-concurrent`）：同时并发测试多个API
- **组合效果**：3个API × 每个10并发 = 最多30个并发请求

**性能对比：**
- 顺序测试3个API（每个50模型）：~230秒
- 并发测试3个API（--api-concurrent 3）：~80秒
- **节省时间：65%**

**说明：**
- 全局 `output.file` 配置仅作为**文件名模板**
- 实际保存路径由每个API的 `base_url` 自动决定
- 不同API的测试结果自动隔离，互不干扰
- 每次测试会生成带时间戳的新文件，不会覆盖历史记录

### Q3: 如何理解健康度评分？
**A:** 
- **90分以上（A）**：API状态优秀，建议保持
- **80-89分（B）**：API状态良好，可考虑优化
- **70-79分（C）**：API状态一般，需要关注
- **60-69分（D）**：API状态较差，建议排查问题
- **60分以下（F）**：API状态很差，需要立即处理

### Q4: 告警信息表示什么？
**A:** 告警信息指出可能的问题：
- **LOW_SUCCESS_RATE**: 成功率过低，检查API配置或网络
- **SLOW_RESPONSE**: 响应时间过慢，可能影响用户体验
- **RATE_LIMIT**: 触发速率限制，建议增加延迟
- **PERMISSION_DENIED**: 权限问题，检查API密钥
- **TIMEOUT**: 超时过多，检查网络或增加超时时间

### Q5: 不同输出格式有什么区别？
**A:**
- **TXT**: 适合命令行查看，简洁明了
- **JSON**: 适合程序处理和API集成
- **CSV**: 适合Excel分析和数据处理
- **HTML**: 适合浏览器查看，美观直观

### Q6: 如何在CI/CD中使用？
**A:** 
```bash
# 在CI脚本中运行测试
python mct.py \
  --api-key $API_KEY \
  --base-url $API_URL \
  --output test_results.json

# 检查健康度评分
score=$(cat test_results_analysis.json | jq -r '.health_score.score')
if [ "$score" -lt 80 ]; then
  echo "API健康度低于80分，测试失败"
  exit 1
fi
```

## 高级技巧

### 技巧1：自动化监控脚本
创建定时监控脚本：
```bash
#!/bin/bash
# monitor.sh - API健康监控脚本

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_FILE="health_check_${TIMESTAMP}.json"

# 运行测试
python mct.py \
  --api-key $API_KEY \
  --base-url $API_URL \
  --output $OUTPUT_FILE

# 检查健康度评分
SCORE=$(jq -r '.health_score.score' "${OUTPUT_FILE}_analysis.json")
if [ $(echo "$SCORE < 80" | bc) -eq 1 ]; then
    echo "警告：API健康度仅为 ${SCORE}，低于80分！"
    # 发送告警通知
    # send_alert "API健康度异常: ${SCORE}"
fi
```

### 技巧2：对比分析
比较不同时间的测试结果：
```bash
# 保存多次测试结果
python mct.py --api-key $API_KEY --base-url $API_URL --output results_$(date +%Y%m%d).json

# 使用jq对比分析
jq -s '.[0].health_score, .[1].health_score' \
  results_20250116_analysis.json \
  results_20250117_analysis.json
```

### 技巧3：自定义告警阈值
通过分析JSON报告实现自定义告警：
```python
import json

with open('test_results_analysis.json') as f:
    analysis = json.load(f)

# 自定义检查
score = analysis['health_score']['score']
success_rate = analysis['health_score']['details']['success_rate']
avg_time = analysis['health_score']['details']['avg_response_time']

if score < 85:
    print(f"警告：健康度评分 {score} 低于85分")
if success_rate < 90:
    print(f"警告：成功率 {success_rate}% 低于90%")
if avg_time > 3.0:
    print(f"警告：平均响应时间 {avg_time}秒 超过3秒")
```

### 技巧4：集成到监控系统
将测试结果推送到监控系统：
```bash
# 运行测试并推送到Prometheus
python mct.py --api-key $API_KEY --base-url $API_URL --output metrics.json

# 解析指标
SCORE=$(jq -r '.health_score.score' metrics_analysis.json)
SUCCESS_RATE=$(jq -r '.health_score.details.success_rate' metrics_analysis.json)

# 推送到Prometheus Pushgateway
cat <<EOF | curl --data-binary @- http://pushgateway:9091/metrics/job/llmct_test
# HELP llmct_health_score API健康度评分
# TYPE llmct_health_score gauge
llmct_health_score $SCORE
# HELP llmct_success_rate 测试成功率
# TYPE llmct_success_rate gauge
llmct_success_rate $SUCCESS_RATE
EOF
```

## 最佳实践

1. **定期健康检查**
   - 每天运行一次健康检查
   - 监控健康度评分趋势
   - 及时响应告警信息

2. **保存测试历史**
   - 每次测试保存到带时间戳的文件
   - 便于历史对比和趋势分析
   - 建议格式：`results_YYYYMMDD_HHMMSS.json`

3. **关注健康度评分**
   - 定期查看评分变化
   - 评分下降时及时调查原因
   - 目标保持80分以上

4. **合理设置请求延迟**
   - 根据API速率限制调整
   - 避免触发429错误
   - 平衡速度和稳定性

5. **充分利用分析报告**
   - 阅读自动生成的告警信息
   - 根据建议优化API配置
   - 追踪问题解决进度

6. **选择合适的输出格式**
   - 日常检查使用TXT
   - 自动化处理使用JSON
   - 数据分析使用CSV
   - 分享结果使用HTML

## 总结

LLMCT提供：
- ✅ 实时测试，无缓存干扰
- ✅ 自动健康度评分（0-100分）
- ✅ 智能告警系统
- ✅ 多格式输出支持
- ✅ 简洁易用的命令行界面

专注于核心功能，提供更高效的API测试体验！
