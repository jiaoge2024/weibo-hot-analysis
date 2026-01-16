# 微博热搜分析 - GitHub Actions 配置速查表

## ✅ 技术可行性：完全可行

GitHub Actions 原生支持运行 Python 脚本和调用 Claude Agent SDK。

---

## 🔑 需要配置的 GitHub Secrets

### 必需配置（1个）
| Secret 名称 | 获取地址 | 用途 |
|------------|---------|------|
| `TIANAPI_KEY` | https://www.tianapi.com/ | 获取微博热搜数据 |

### 可选配置（1个，用于Claude AI增强）
| Secret 名称 | 获取地址 | 用途 |
|------------|---------|------|
| `ANTHROPIC_API_KEY` | https://console.anthropic.com/ | Claude AI分析 |

---

## 📁 项目调用API信息汇总

### 1. Tianapi 微博热搜API

**端点**: `https://apis.tianapi.com/weibohot/index`

**方法**: GET

**参数**:
| 参数 | 说明 | 示例 |
|-----|------|-----|
| key | API密钥 | 来自Secret |
| num | 获取数量 | 10 |

**响应示例**:
```json
{
  "code": 200,
  "result": {
    "list": [
      {
        "hotWord": "话题名称",
        "hotRank": 1,
        "hotScore": 1234567
      }
    ]
  }
}
```

### 2. 百度搜索（Web Scraping）

**端点**: `https://www.baidu.com/s?wd={encoded_query}`

**方法**: GET（无需认证）

**用途**: 搜索热搜话题的背景信息

### 3. Claude Agent SDK（可选）

**SDK**: `anthropic` Python包

**模型**: `claude-3-5-sonnet-20241022`

**用途**: AI深度分析产品创意

---

## 🚀 快速配置流程（5步完成）

### 步骤1：获取API Keys（5分钟）

```bash
# Tianapi（必需）
访问 https://www.tianapi.com/
注册 → 登录 → 复制API Key

# Anthropic（可选）
访问 https://console.anthropic.com/
注册 → API Keys → Create Key → 复制
```

### 步骤2：配置GitHub Secrets（3分钟）

1. 进入GitHub仓库 → Settings → Secrets and variables → Actions
2. 点击 "New repository secret"
3. 添加：
   - Name: `TIANAPI_KEY`
   - Secret: `您的Tianapi密钥`
4. （可选）添加：
   - Name: `ANTHROPIC_API_KEY`
   - Secret: `您的Anthropic密钥`

### 步骤3：初始化Git仓库（如果需要）

```bash
cd "D:\AI资料库\01 编程开发\claude skills\skills\weibo-resou"
git init
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
```

### 步骤4：提交并推送代码

```bash
git add .
git commit -m "feat: Add GitHub Actions for Weibo hot analysis"
git branch -M main
git push -u origin main
```

### 步骤5：验证工作流

1. 进入GitHub仓库 → Actions
2. 选择 "Weibo Hot Search Analysis"
3. 点击 "Run workflow"
4. 查看执行日志

---

## 📂 已创建的文件

```
weibo-resou/
├── .github/
│   └── workflows/
│       └── weibo-hot-analysis.yml    ✅ GitHub Actions工作流
├── weibo_hot_analyzer.py             ✅ 原始脚本（方案A）
├── weibo_analyzer_sdk.py             ✅ Claude SDK版（方案B）
├── requirements.txt                  ✅ Python依赖
├── .gitignore                        ✅ Git忽略配置
├── GITHUB_ACTIONS_MIGRATION.md       ✅ 完整迁移方案
├── QUICK_SETUP_GUIDE.md              ✅ 快速设置指南
└── COMPARISON.md                     ✅ 方案对比分析
```

---

## 🎯 两种部署方案

### 方案A：快速部署（推荐新手）

**特点**:
- 零代码改动
- 使用现有脚本
- 规则引擎分析

**工作流**:
```yaml
- name: Run Weibo Hot Analysis
  run: python weibo_hot_analyzer.py 10
```

**配置Secrets**:
- `TIANAPI_KEY` ✅

---

### 方案B：Claude AI增强（推荐追求质量）

**特点**:
- Claude AI深度分析
- 更高质量洞察
- 需要API成本

**工作流**:
```yaml
- name: Run Weibo Hot Analysis
  env:
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
  run: python weibo_analyzer_sdk.py 10
```

**配置Secrets**:
- `TIANAPI_KEY` ✅
- `ANTHROPIC_API_KEY` ✅

---

## 📅 执行时间

- **自动执行**: 每天早上8点（北京时间）
- **时区说明**: GitHub Actions使用UTC，北京时间=UTC+8
- **手动执行**: Actions → Run workflow

---

## 💰 成本估算

| 项目 | 方案A | 方案B |
|-----|-------|-------|
| Tianapi | 免费 | 免费 |
| Claude API | - | ~$0.01-0.05/次 |
| GitHub Actions | 免费 | 免费 |
| **月成本** | **$0** | **~$0.30-1.50** |

---

## 📞 快速链接

- [完整迁移方案](./GITHUB_ACTIONS_MIGRATION.md) - 详细技术文档
- [快速设置指南](./QUICK_SETUP_GUIDE.md) - 5分钟配置教程
- [方案对比分析](./COMPARISON.md) - 选择最佳方案

---

## ⚠️ 常见问题

### Q: 工作流不执行？
A: 检查cron表达式，北京时间8点=UTC 0点

### Q: API调用失败？
A: 检查Secrets名称和值是否正确配置

### Q: 如何修改执行时间？
A: 编辑工作流文件中的cron表达式

### Q: 如何手动触发？
A: Actions → Weibo Hot Search Analysis → Run workflow

---

## ✅ 配置检查清单

- [ ] 已获取 Tianapi API Key
- [ ] 已配置 TIANAPI_KEY 到 GitHub Secrets
- [ ] 已初始化 Git 仓库
- [ ] 已推送到 GitHub
- [ ] 已手动测试工作流成功
- [ ] （可选）已配置 ANTHROPIC_API_KEY
- [ ] （可选）已升级到 Claude SDK 版本

---

**配置完成后，您的工作流将每天早上8点自动运行，生成微博热搜产品创意分析报告！** 🎉
