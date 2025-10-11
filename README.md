# 大模型连通性和可用性测试工具 [增强版]

自动获取并测试所有大模型的连通性和可用性，支持多种模型类型的专项测试。

## 功能特性

- 🔍 自动获取API提供的所有模型列表
- 🎯 精准识别7种模型类型（语言/视觉/音频/嵌入/图像生成/重排/审核）
- 💬 **语言模型**：发送测试消息并验证响应
- 👁️ **视觉模型**：发送图像+文本进行多模态测试
- 🎵 **音频模型**：检测ASR/TTS端点可用性
- 📊 **嵌入模型**：实际调用embedding接口并显示向量维度
- 🎨 **图像生成**：测试图像生成功能
- ⚙️ 灵活配置：可选择性跳过特定类型的实际测试
- 📈 显示详细的响应时间和测试结果
- 💾 自动保存测试结果到文件
- 🎨 表格化显示，实时输出

## 环境要求

- Python 3.7+
- Windows 11 / PowerShell
- 网络连接

## 安装

```powershell
# 安装依赖
pip install -r requirements.txt
```

## 使用方法

### 基本用法

```powershell
python test_models.py --api-key <YOUR_API_KEY> --base-url <API_BASE_URL>
```

### 示例

```powershell
# 基础测试（包含所有类型的实际测试）
python test_models.py --api-key sk-xxxxxxxx --base-url https://api.openai.com

# 自定义测试消息
python test_models.py --api-key sk-xxxxxxxx --base-url https://api.openai.com --message "你好"

# 设置超时时间
python test_models.py --api-key sk-xxxxxxxx --base-url https://api.openai.com --timeout 60

# 指定输出文件
python test_models.py --api-key sk-xxxxxxxx --base-url https://api.openai.com --output my_results.txt

# 仅测试语言模型（跳过其他类型的实际测试，节省API配额）
python test_models.py --api-key sk-xxxxxxxx --base-url https://api.openai.com --skip-vision --skip-audio --skip-embedding --skip-image-gen

# 测试语言和视觉模型
python test_models.py --api-key sk-xxxxxxxx --base-url https://api.openai.com --skip-audio --skip-embedding --skip-image-gen
```

## 参数说明

| 参数 | 必需 | 说明 | 默认值 |
|------|------|------|--------|
| `--api-key` | 是 | API密钥 | - |
| `--base-url` | 是 | API基础URL | - |
| `--message` | 否 | 测试消息 | hello |
| `--timeout` | 否 | 超时时间(秒) | 30 |
| `--output`, `-o` | 否 | 结果输出文件路径 | test_results.txt |
| `--skip-vision` | 否 | 跳过视觉模型的实际测试 | False |
| `--skip-audio` | 否 | 跳过音频模型的实际测试 | False |
| `--skip-embedding` | 否 | 跳过嵌入模型的实际测试 | False |
| `--skip-image-gen` | 否 | 跳过图像生成模型的实际测试 | False |

## 输出示例

```
==================================================================================================================
大模型连通性和可用性测试 [增强版]
Base URL: https://api.openai.com
测试时间: 2024-01-01 12:00:00
测试配置: 视觉=True, 音频=True, 嵌入=True, 图像生成=True
==================================================================================================================

正在获取模型列表...
共发现 8 个模型

==================================================================================================================
模型名称                                      |  响应时间  |   错误信息   | 响应内容
------------------------------------------------------------------------------------------------------------------
gpt-4o                                       |   1.23秒   |      -       | Hello! How can I assist you today?
gpt-3.5-turbo                               |   0.85秒   |      -       | Hi there! How may I help you?
gpt-4o-vision                               |   2.34秒   |      -       | The image shows a beautiful landscap...
text-embedding-ada-002                      |   0.45秒   |      -       | Embedding维度:1536
text-embedding-3-large                      |   0.52秒   |      -       | Embedding维度:3072
whisper-1                                   |   0.61秒   |      -       | 音频端点可用
tts-1                                       |   0.58秒   |      -       | TTS端点可用
dall-e-3                                    |   8.23秒   |      -       | 图像生成成功
==================================================================================================================
测试完成 | 总计: 8 | 成功: 8 | 失败: 0 | 成功率: 100.0%
==================================================================================================================
```

### 输出说明

- **模型名称**: 显示模型ID，超过45字符会截断
- **响应时间**: 显示秒数，失败时可能显示 -
- **错误信息**: 显示错误代码（TIMEOUT、HTTP_xxx、CONN_FAILED等），成功时显示 -
- **响应内容**: 根据模型类型显示不同信息
  - 语言模型：返回的文本内容（截断至40字符）
  - 视觉模型：对图像的描述（截断至40字符）
  - 嵌入模型：`Embedding维度:xxxx`
  - 音频模型：`音频端点可用` 或 `TTS端点可用`
  - 图像生成：`图像生成成功`
  - 其他模型：`连接成功` 或 `[模型类型] 连接成功`

## 测试结果保存

测试结果会自动保存到文件（默认：`test_results.txt`），文件内容包括：
- 测试基本信息（Base URL、测试时间）
- 完整的测试结果表格
- 统计信息（总计、成功、失败、成功率）

**文件格式示例：**
```
==================================================================================================================
大模型连通性和可用性测试结果
Base URL: https://api.openai.com
测试时间: 2024-01-01 12:00:00
==================================================================================================================

==================================================================================================================
模型名称                                      |  响应时间  |   错误信息   | 响应内容
------------------------------------------------------------------------------------------------------------------
gpt-4                                        |   1.23秒   |      -       | Hello! How can I assist you today?
...
==================================================================================================================
测试完成 | 总计: 5 | 成功: 3 | 失败: 2 | 成功率: 60.0%
==================================================================================================================
```

**注意：** 测试结果文件已添加到 `.gitignore`，不会被提交到版本控制系统。

## 错误说明

测试过程中可能遇到各种错误，详细的错误信息、原因和解决方案请查看 [错误说明文档](ERRORS.md)。

常见错误包括：
- **HTTP_403**: 没有模型访问权限
- **HTTP_429**: 超出速率限制
- **TIMEOUT**: 请求超时
- **CONN_FAILED**: 连接失败

## 注意事项

- 确保API密钥有足够的权限访问模型列表
- 某些API可能有速率限制，大量模型测试时注意间隔
- 超时时间根据网络状况调整
- 测试会产生API调用费用（如果适用）

## 支持的API格式

本工具兼容OpenAI API格式，支持以下端点：
- `/v1/models` - 获取模型列表
- `/v1/chat/completions` - 测试语言模型和视觉模型
- `/v1/embeddings` - 测试嵌入模型
- `/v1/audio/transcriptions` - 测试音频转录模型
- `/v1/audio/speech` - 测试TTS模型
- `/v1/images/generations` - 测试图像生成模型
- `/v1/models/{model_id}` - 测试基础连通性

## 支持的模型类型

### 1. 语言模型（Language Models）
- GPT系列：gpt-4o, gpt-3.5-turbo, o1-mini
- Claude系列：claude-3, claude-4
- Qwen系列：Qwen2.5, Qwen3
- GLM系列：GLM-4, GLM-Z1
- Gemini系列：gemini-2.0, gemini-2.5
- DeepSeek系列：DeepSeek-V3, DeepSeek-R1
- 其他：Moonshot, ERNIE, Doubao, Yi等

### 2. 视觉模型（Vision Models）
- 多模态对话模型（支持图像输入）
- GPT-4o, Claude-3/4, Gemini
- Qwen-VL, GLM-4V, InternVL
- QVQ, Llama-Vision, Molmo, Aria

### 3. 音频模型（Audio Models）
- ASR（语音转文字）：Whisper, SenseVoice, TeleASR
- TTS（文字转语音）：tts-1, CosyVoice, Fish-Speech

### 4. 嵌入模型（Embedding Models）
- text-embedding-ada-002, text-embedding-3-large
- bge-m3, bge-large
- Doubao-embedding, embedding-001

### 5. 图像生成模型（Image Generation）
- DALL-E 2/3, Flux.1, Stable Diffusion
- Kolors, CogView, Dreamshaper
- SeedDream, SeedDance, SeedEdit

### 6. 其他模型
- Reranker：bge-reranker-v2-m3
- Moderation：text-moderation-stable

## 优化说明

相比原版，本增强版主要改进：

1. **精准的模型分类** - 从简单的"语言/非语言"二分改为7种类型识别
2. **针对性测试方法** - 每种类型使用对应的API端点和测试方式
3. **更丰富的测试信息** - 显示嵌入维度、端点类型等详细信息
4. **灵活的测试配置** - 可选择性跳过特定类型以节省API配额
5. **更准确的结果** - 减少HTTP_400/404错误，提高测试成功率

详细优化说明请查看 [OPTIMIZATION_NOTES.md](OPTIMIZATION_NOTES.md)
