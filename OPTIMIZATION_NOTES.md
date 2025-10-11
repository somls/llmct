# 图像/音频等非文本模型测试优化说明

## 优化概述

本次优化针对原有的大模型测试工具进行了增强，主要改进了对图像、音频、嵌入等非文本模型的测试能力。

## 主要改进

### 1. 精准的模型分类

**之前的问题：**
- 简单的关键词匹配，容易误判
- 视觉模型（如 `qwen-vl-plus`）被错误识别
- 音频模型（如 `whisper-1`）无法正确测试

**优化后：**
新增 `classify_model()` 方法，支持7种模型类型识别：

- **language** - 纯文本语言模型
- **vision** - 视觉理解模型（支持图像输入的多模态对话）
- **audio** - 音频模型（TTS和ASR）
- **embedding** - 向量嵌入模型
- **image_generation** - 图像生成模型
- **reranker** - 重排序模型
- **moderation** - 内容审核模型

识别覆盖的模型示例：
- 视觉：`gpt-4o`, `claude-3`, `gemini-`, `qwen-vl`, `internvl`, `glm-4v`
- 音频：`whisper`, `tts`, `cosyvoice`, `fish-speech`, `sensevoice`
- 图像生成：`dall-e`, `flux`, `stable-diffusion`, `kolors`, `cogview`
- 嵌入：`embedding`, `bge-m3`, `bge-large`

### 2. 专门的测试方法

#### 视觉模型测试 `test_vision_model()`
- 发送包含图像URL的多模态请求
- 使用标准的OpenAI vision格式
- 默认测试图像：Wikipedia自然风景图
- 验证模型能否理解和描述图像内容

```python
# 请求格式
{
    "model": model_id,
    "messages": [{
        "role": "user",
        "content": [
            {"type": "text", "text": "What's in this image?"},
            {"type": "image_url", "image_url": {"url": image_url}}
        ]
    }]
}
```

#### 音频模型测试 `test_audio_model()`
- 检测 `/v1/audio/transcriptions` (ASR) 端点
- 检测 `/v1/audio/speech` (TTS) 端点
- 使用OPTIONS请求验证端点可用性
- 避免实际音频文件上传的复杂性

#### 嵌入模型测试 `test_embedding_model()`
- 使用 `/v1/embeddings` 端点
- 发送简单文本 "hello world"
- 验证返回的向量维度
- 显示嵌入维度信息（如：`Embedding维度:1536`）

```python
# 请求格式
{
    "model": model_id,
    "input": "hello world"
}
```

#### 图像生成模型测试 `test_image_generation_model()`
- 使用 `/v1/images/generations` 端点
- 发送简单提示词 "a white cat"
- 请求256x256小尺寸图像（节省资源）
- 验证图像生成成功

```python
# 请求格式
{
    "model": model_id,
    "prompt": "a white cat",
    "n": 1,
    "size": "256x256"
}
```

### 3. 灵活的测试配置

新增命令行参数，支持选择性测试：

```bash
# 跳过视觉模型的实际测试（仅连通性测试）
--skip-vision

# 跳过音频模型的实际测试
--skip-audio

# 跳过Embedding模型的实际测试
--skip-embedding

# 跳过图像生成模型的实际测试
--skip-image-gen
```

**使用场景：**
- 快速测试时跳过耗时的图像/音频API调用
- API配额有限时避免昂贵的调用
- 仅测试特定类型的模型

### 4. 改进的测试逻辑

```python
# 根据模型类型和配置选择测试方法
if model_type == 'language':
    # 语言模型：发送文本消息
    test_language_model()
elif model_type == 'vision' and test_vision:
    # 视觉模型：发送图像+文本
    test_vision_model()
elif model_type == 'audio' and test_audio:
    # 音频模型：检测音频端点
    test_audio_model()
elif model_type == 'embedding' and test_embedding:
    # 嵌入模型：请求文本向量
    test_embedding_model()
elif model_type == 'image_generation' and test_image_gen:
    # 图像生成：发送提示词
    test_image_generation_model()
else:
    # 其他或禁用的类型：基础连通性测试
    test_connectivity()
```

## 解决的问题

### 之前的HTTP错误现在会改善：

1. **HTTP_404 错误** (音频/嵌入模型)
   - 之前：使用 `/v1/models/{model_id}` 端点失败
   - 现在：使用正确的 `/v1/audio/*` 或 `/v1/embeddings` 端点

2. **HTTP_400 错误** (图像生成/视觉模型)
   - 之前：用chat completions接口测试图像模型
   - 现在：使用 `/v1/images/generations` 或正确的vision格式

3. **误判为"连接成功"** (但实际不可用)
   - 之前：非语言模型只测试连通性
   - 现在：进行实际的功能测试

### 受益的模型示例：

| 模型类型 | 模型示例 | 优化前 | 优化后 |
|---------|---------|--------|--------|
| 视觉模型 | qwen-vl-plus | UNKNOWN_ERROR | 实际视觉理解测试 |
| 音频ASR | whisper-1, @cf/openai/whisper | HTTP_404 | 音频端点检测 |
| 音频TTS | tts-1, cosyvoice | HTTP_404 | 音频端点检测 |
| 嵌入模型 | text-embedding-ada-002 | "连接成功" | 实际嵌入测试+维度 |
| 图像生成 | dall-e-3, flux | "连接成功" | 实际生成测试 |
| Reranker | bge-reranker-v2-m3 | HTTP_400 | 正确识别+跳过 |

## 使用示例

### 完整测试（包含所有类型）
```bash
python test_models.py --api-key sk-xxx --base-url https://api.example.com
```

### 仅测试语言模型（跳过其他类型的实际测试）
```bash
python test_models.py --api-key sk-xxx --base-url https://api.example.com \
  --skip-vision --skip-audio --skip-embedding --skip-image-gen
```

### 测试语言和视觉模型
```bash
python test_models.py --api-key sk-xxx --base-url https://api.example.com \
  --skip-audio --skip-embedding --skip-image-gen
```

### 自定义超时和输出
```bash
python test_models.py --api-key sk-xxx --base-url https://api.example.com \
  --timeout 60 --output enhanced_test_results.txt
```

## 输出示例

优化后的输出会显示更详细的信息：

```
==================================================================================================================
大模型连通性和可用性测试 [增强版]
Base URL: https://api.example.com
测试时间: 2025-01-15 14:30:00
测试配置: 视觉=True, 音频=True, 嵌入=True, 图像生成=True
==================================================================================================================

==================================================================================================================
模型名称                                      |  响应时间  |   错误信息   | 响应内容
------------------------------------------------------------------------------------------------------------------
gpt-4o                                       |   2.45秒   |      -       | Hello! How can I assist you today?
qwen-vl-plus                                 |   3.21秒   |      -       | The image shows a beautiful natural...
whisper-1                                    |   0.52秒   |      -       | 音频端点可用
text-embedding-3-large                       |   0.61秒   |      -       | Embedding维度:3072
dall-e-3                                     |   8.34秒   |      -       | 图像生成成功
==================================================================================================================
```

## 技术细节

### 错误处理
所有测试方法都包含完整的错误处理：
- `Timeout` - 请求超时
- `HTTPError` - HTTP状态码错误
- `RequestException` - 请求失败
- `Exception` - 未知错误

### 性能考虑
1. **超时控制**：每个请求都受 `--timeout` 参数控制
2. **资源节约**：
   - 图像生成使用最小尺寸 (256x256)
   - 视觉模型使用小尺寸测试图像
   - max_tokens限制为100
3. **可选测试**：通过 `--skip-*` 参数避免不必要的API调用

### 兼容性
- 保持向后兼容：默认行为与原版相同
- 新功能可选：通过参数启用/禁用
- 支持OpenAI API格式的所有兼容服务

## 未来优化方向

1. **批量测试优化**
   - 添加速率限制控制
   - 支持重试机制
   - 分批测试以避免HTTP_429

2. **更多模型类型**
   - 视频生成模型（如Sora）
   - 代码生成专用模型
   - 多轮对话测试

3. **测试深度**
   - 音频模型：实际上传音频文件测试
   - 图像生成：验证图像质量
   - 视觉模型：测试多种图像类型

4. **报告增强**
   - 按模型类型分组统计
   - 生成HTML可视化报告
   - 性能基准测试

## 贡献

本次优化基于实际测试1128个模型的经验，针对发现的问题进行了系统性改进。

主要改进领域：
- ✅ 模型分类准确性
- ✅ 测试方法针对性
- ✅ 配置灵活性
- ✅ 错误信息准确性
- ⏳ 批量测试性能（待优化）

## 参考文档

- OpenAI API文档：https://platform.openai.com/docs/api-reference
- 原始错误分析：[ERRORS.md](ERRORS.md)
- 测试结果分析：[test_analysis.md](test_analysis.md)
