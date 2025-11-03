# 安全注意事项

## 敏感信息保护

本项目涉及 API 密钥等敏感信息，请注意以下事项：

### ⚠️ 不要提交的文件

以下文件类型已在 `.gitignore` 中配置，请勿提交到远程仓库：

1. **包含真实 API 密钥的配置文件**:
   - `config.yaml`
   - `config_*.yaml` (除了 `config_example.yaml`)
   - `.env` 文件

2. **临时测试文件**:
   - `quick_api_test.py`
   - `test_*.py` (除了 `tests/test_*.py`)
   - 包含 API 密钥的临时脚本

3. **包含敏感信息的文档**:
   - `*_ANALYSIS.md` (测试分析报告)
   - `*_REPORT.md` (测试报告)
   - `*_GUIDE.md` (使用指南，如果包含真实密钥)

4. **测试结果文件**:
   - `test_results/` 目录下的所有文件
   - `*.json`, `*.csv`, `*.html` (测试结果)

### ✅ 正确使用方式

#### 1. 使用配置模板

**步骤**:
```bash
# 复制模板
cp config_example.yaml config.yaml

# 编辑配置，填入你的 API 密钥
nano config.yaml
```

`config.yaml` 已在 `.gitignore` 中，不会被提交。

#### 2. 使用环境变量

**推荐方式**:
```bash
# Linux/Mac
export LLMCT_API_KEY="your-api-key"
export LLMCT_BASE_URL="https://your-api-endpoint.com"

# Windows PowerShell
$env:LLMCT_API_KEY="your-api-key"
$env:LLMCT_BASE_URL="https://your-api-endpoint.com"

# 运行测试
python mct.py --message "hello"
```

#### 3. 使用 .env 文件

**创建 `.env` 文件** (已在 .gitignore 中):
```bash
LLMCT_API_KEY=your-api-key
LLMCT_BASE_URL=https://your-api-endpoint.com
```

**加载环境变量** (需要安装 python-dotenv):
```python
from dotenv import load_dotenv
load_dotenv()

# 现在可以使用环境变量
import os
api_key = os.getenv('LLMCT_API_KEY')
```

### 🔍 检查敏感信息

**提交前检查**:
```bash
# 1. 查看暂存区的文件
git diff --cached

# 2. 搜索是否包含 API 密钥模式
git diff --cached | grep -i "sk-"
git diff --cached | grep -i "api[_-]key"

# 3. 查看将要提交的文件列表
git status
```

### 🚨 如果不慎提交了敏感信息

#### 方案 1: 未推送到远程 (最简单)
```bash
# 撤销最后一次提交，保留更改
git reset --soft HEAD~1

# 删除包含敏感信息的文件
rm sensitive_file.yaml

# 重新提交
git add .
git commit -m "Remove sensitive information"
```

#### 方案 2: 已推送到远程 (需要强制推送)
```bash
# 1. 从历史记录中删除文件
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch path/to/sensitive_file" \
  --prune-empty --tag-name-filter cat -- --all

# 2. 强制推送
git push origin --force --all

# 3. 立即更换 API 密钥！
```

#### 方案 3: 使用 BFG Repo-Cleaner (推荐)
```bash
# 1. 下载 BFG
# https://rtyley.github.io/bfg-repo-cleaner/

# 2. 清理敏感文件
java -jar bfg.jar --delete-files sensitive_file.yaml

# 3. 清理 reflog
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# 4. 强制推送
git push --force
```

**⚠️ 重要**: 无论使用哪种方法，都应该立即更换被泄露的 API 密钥！

### 📋 提交前检查清单

提交代码前，请确认：

- [ ] 没有提交 `config.yaml` 或其他包含真实密钥的配置文件
- [ ] 没有提交包含 `sk-` 开头的 API 密钥的文件
- [ ] 没有提交测试结果文件 (`test_results/`)
- [ ] 没有提交临时测试脚本 (`quick_api_test.py` 等)
- [ ] 没有提交包含敏感信息的分析报告
- [ ] 已运行 `git diff --cached` 检查暂存内容
- [ ] 文档中的示例使用了占位符 (如 `sk-xxx` 或 `your-api-key`)

### 📚 最佳实践

1. **永远不要硬编码 API 密钥**
   ```python
   # ❌ 错误
   api_key = "sk-xxxxxxxxxxxxxxxxxxxx"
   
   # ✅ 正确
   api_key = os.getenv('LLMCT_API_KEY')
   ```

2. **使用配置模板**
   - 提供 `config_example.yaml` 示例
   - 真实配置使用 `config.yaml` (在 .gitignore 中)

3. **文档中使用占位符**
   ```bash
   # ✅ 正确
   python mct.py --api-key sk-xxx --base-url https://api.example.com
   
   # 或
   python mct.py --api-key "your-api-key" --base-url "your-base-url"
   ```

4. **定期审查 .gitignore**
   - 确保所有敏感文件类型都被排除
   - 新增配置文件时及时更新 .gitignore

5. **使用 git-secrets 工具**
   ```bash
   # 安装 git-secrets
   brew install git-secrets  # Mac
   # 或从 https://github.com/awslabs/git-secrets 安装
   
   # 配置
   git secrets --install
   git secrets --register-aws  # 扫描 AWS 密钥
   git secrets --add 'sk-[a-zA-Z0-9]{20,}'  # 扫描自定义密钥格式
   ```

### 🔐 密钥管理建议

1. **使用密钥管理服务**:
   - AWS Secrets Manager
   - HashiCorp Vault
   - Azure Key Vault

2. **限制密钥权限**:
   - 使用最小权限原则
   - 为不同环境使用不同的密钥

3. **定期轮换密钥**:
   - 建议每 90 天轮换一次
   - 泄露后立即轮换

4. **监控密钥使用**:
   - 启用 API 调用日志
   - 设置异常使用告警

### 📞 联系方式

如发现项目中存在敏感信息泄露，请立即：
1. 提交 Issue (不要在 Issue 中包含敏感信息)
2. 联系项目维护者
3. 更换受影响的 API 密钥

---

**更新时间**: 2025-11-03  
**适用版本**: LLMCT v2.4.0+
