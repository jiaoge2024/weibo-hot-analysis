# 微博热搜分析 - GitHub Actions 迁移方案

## 📋 项目概述

将 `/wb` 技能迁移到 GitHub Actions，实现每天8点自动执行微博热搜产品创意分析。

---

## 🔍 当前项目技术分析

### 依赖的API和服务

| API/服务 | 端点 | 用途 | 认证方式 |
|---------|------|------|---------|
| **Tianapi 微博热搜API** | `https://apis.tianapi.com/weibohot/index` | 获取热搜榜单 | API Key |
| **百度搜索** | `https://www.baidu.com/s` | 搜索热点背景 | 无需认证 (Web Scraping) |
| **Claude Agent SDK** | - | 产品创意AI分析 | API Key (改造后) |

### 当前代码结构

```
weibo-resou/
├── weibo_hot_analyzer.py    # 主脚本 (1306行)
├── config.json              # 配置文件 (含API Key)
├── SKILL.md                 # 技能文档
├── output/                  # 报告输出目录
└── .claude/
    └── settings.local.json  # 权限配置
```

---

## 🎯 GitHub Secrets 配置清单

### 必需配置的 Secrets

| Secret 名称 | 说明 | 获取方式 |
|------------|------|---------|
| `TIANAPI_KEY` | 天数据微博热搜API密钥 | 访问 https://www.tianapi.com/ 注册获取 |
| `ANTHROPIC_API_KEY` | Claude API密钥 | 访问 https://console.anthropic.com/ 获取 |

### 可选配置的 Secrets

| Secret 名称 | 说明 | 默认值 |
|------------|------|--------|
| `ANALYSIS_COUNT` | 每次分析的热搜数量 | `10` |
| `CLAUDE_MODEL` | 使用的Claude模型 | `claude-3-5-sonnet-20241022` |

---

## 📁 需要创建的文件

### 1. `.github/workflows/weibo-hot-analysis.yml`

GitHub Actions 工作流定义文件

### 2. `requirements.txt`

Python 依赖清单

### 3. `weibo_analyzer_sdk.py` (方案B)

改造后的主脚本，集成 Claude Agent SDK

### 4. `.gitignore`

确保敏感信息不被提交

---

## 🚀 方案A：快速部署（无需修改代码）

### 步骤1：创建 `.github/workflows` 目录结构

```bash
mkdir -p .github/workflows
```

### 步骤2：创建工作流文件

创建 `.github/workflows/weibo-hot-analysis.yml`：

```yaml
name: Weibo Hot Search Analysis

on:
  schedule:
    # 每天8点执行 (UTC时间0点 = 北京时间8点)
    - cron: '0 0 * * *'
  workflow_dispatch:  # 允许手动触发

jobs:
  analyze:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install requests beautifulsoup4

      - name: Run Weibo Hot Analysis
        env:
          TIANAPI_KEY: ${{ secrets.TIANAPI_KEY }}
          ANALYSIS_COUNT: 10
        run: |
          # 创建配置文件
          cat > config.json << EOF
          {
            "weibo_api": {
              "url": "https://apis.tianapi.com/weibohot/index",
              "key": "${TIANAPI_KEY}"
            },
            "analysis": {
              "default_count": ${ANALYSIS_COUNT},
              "enable_ai_analysis": true,
              "enable_web_search": true,
              "max_concurrent_searches": 5
            },
            "output": {
              "directory": "output",
              "auto_open": false
            }
          }
          EOF

          # 运行分析脚本
          python weibo_hot_analyzer.py ${ANALYSIS_COUNT}

      - name: Upload reports as artifacts
        uses: actions/upload-artifact@v4
        with:
          name: weibo-hot-report-${{ github.run_number }}
          path: output/*.html
          retention-days: 30

      - name: Commit and push reports
        run: |
          git config --local user.email "github-actions[bot]@users.noreply.github.com"
          git config --local user.name "github-actions[bot]"
          git add output/*.html
          git diff --quiet && git diff --staged --quiet || git commit -m "🤖 Auto: Weibo hot analysis report"
          git push
```

### 步骤3：更新 `.gitignore`

```
# 忽略配置文件中的敏感信息
config.json

# 保留输出目录但忽略临时文件
output/*.tmp
```

---

## 🎨 方案B：Claude Agent SDK 改造（推荐）

### 架构变化

```
原架构：Tianapi → 百度搜索 → 规则引擎 → HTML
新架构：Tianapi → 百度搜索 → Claude AI → HTML
```

### 改造核心代码

创建 `weibo_analyzer_sdk.py`，替换 `mock_ai_analysis()` 函数：

```python
import anthropic
import os
import json
from typing import Dict, List

class ClaudeProductAnalyzer:
    """使用Claude Agent SDK进行产品创意分析"""

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        self.model = os.environ.get("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")

    def analyze_product_idea(self, topic: str, search_results: List[Dict]) -> Dict:
        """使用Claude分析产品创意"""

        # 构建上下文
        context = self._build_context(topic, search_results)

        # Claude分析提示词
        prompt = f"""你是一位产品创新专家。请基于以下热搜话题进行产品创意分析：

{context}

请以JSON格式返回分析结果，包含以下字段：
{{
    "name": "产品名称（不超过15字）",
    "core_features": ["核心功能1", "核心功能2", "核心功能3", "核心功能4", "核心功能5"],
    "market_pain_points": ["痛点1", "痛点2", "痛点3", "痛点4", "痛点5"],
    "target_users": "目标用户描述（50字内）",
    "innovation_points": ["创新点1", "创新点2", "创新点3", "创新点4", "创新点5"],
    "market_potential": {{
        "market_size": "市场规模描述",
        "growth_stage": "增长阶段",
        "competitive_advantage": "竞争优势",
        "revenue_model": "商业模式"
    }},
    "scores": {{
        "innovation": 创新性分数(15-30),
        "pain_point": 痛点洞察分数(15-25),
        "potential": 潜力空间分数(10-15),
        "social": 社交属性分数(5-10),
        "practicality": 实用性分数(5-10),
        "feasibility": 可行性分数(5-10)
    }}
}}

请确保分析具体、有洞察力，避免套话。直接返回JSON，不要有其他文字。"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # 解析Claude响应
            result_text = response.content[0].text
            analysis = json.loads(result_text)

            # 计算总分
            scores = analysis["scores"]
            interest_score = scores["innovation"] + scores["pain_point"] + scores["potential"] + scores["social"]
            utility_score = scores["practicality"] + scores["feasibility"]
            scores["total"] = round(interest_score + utility_score, 1)
            scores["interest_score"] = interest_score
            scores["utility_score"] = utility_score

            # 生成事件脉络
            analysis["event_timeline"] = self._generate_timeline(topic, search_results)

            return analysis

        except Exception as e:
            print(f"Claude API调用失败: {e}")
            # 降级到规则引擎
            return self._fallback_analysis(topic, search_results)

    def _build_context(self, topic: str, search_results: List[Dict]) -> str:
        """构建分析上下文"""
        context = f"热搜话题: {topic}\n"

        if search_results:
            context += "\n相关新闻:\n"
            for r in search_results[:5]:
                context += f"  - {r['title']}\n"

        return context

    def _generate_timeline(self, topic: str, search_results: List[Dict]) -> str:
        """生成事件脉络"""
        # 可以复用原有的 generate_event_timeline 函数
        # 或者用Claude生成更精准的脉络
        pass

    def _fallback_analysis(self, topic: str, search_results: List[Dict]) -> Dict:
        """降级分析（使用规则引擎）"""
        # 调用原有的 mock_ai_analysis 函数
        pass
```

### GitHub Actions 工作流（SDK版本）

```yaml
name: Weibo Hot Search Analysis (Claude SDK)

on:
  schedule:
    - cron: '0 0 * * *'  # 每天8点 (北京时间)
  workflow_dispatch:

jobs:
  analyze:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install requests beautifulsoup4 anthropic

      - name: Run Weibo Hot Analysis with Claude SDK
        env:
          TIANAPI_KEY: ${{ secrets.TIANAPI_KEY }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          ANALYSIS_COUNT: 10
          CLAUDE_MODEL: claude-3-5-sonnet-20241022
        run: |
          python weibo_analyzer_sdk.py ${ANALYSIS_COUNT}

      - name: Upload reports
        uses: actions/upload-artifact@v4
        with:
          name: weibo-hot-report-${{ github.run_number }}
          path: output/*.html
          retention-days: 30

      - name: Commit reports
        run: |
          git config --local user.email "github-actions[bot]@users.noreply.github.com"
          git config --local user.name "github-actions[bot]"
          git add output/*.html
          git diff --quiet && git diff --staged --quiet || git commit -m "🤖 Auto: Weibo hot analysis (Claude SDK)"
          git push
```

---

## 📝 完整配置步骤

### 步骤1：准备 GitHub Repository

```bash
# 1. 初始化Git仓库（如果还没有）
cd "D:\AI资料库\01 编程开发\claude skills\skills\weibo-resou"
git init

# 2. 创建必要的目录
mkdir -p .github/workflows
mkdir -p output

# 3. 创建 .gitignore
cat > .gitignore << 'EOF'
# 敏感配置
config.json

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python

# 临时文件
*.tmp
*.cwd
EOF
```

### 步骤2：获取 API Keys

#### Tianapi Key
1. 访问 https://www.tianapi.com/
2. 注册账号并登录
3. 进入"我的数据" → "API密钥"
4. 复制您的API Key

#### Anthropic API Key
1. 访问 https://console.anthropic.com/
2. 注册账号并登录
3. 进入 "API Keys"
4. 创建新的 API Key 并复制

### 步骤3：配置 GitHub Secrets

1. 进入您的 GitHub 仓库页面
2. 点击 "Settings" → "Secrets and variables" → "Actions"
3. 点击 "New repository secret"
4. 添加以下 secrets：

   | Name | Secret |
   |------|--------|
   | `TIANAPI_KEY` | 您的Tianapi API Key |
   | `ANTHROPIC_API_KEY` | 您的Anthropic API Key |

### 步骤4：创建 Requirements 文件

创建 `requirements.txt`：

```
requests>=2.31.0
beautifulsoup4>=4.12.0
anthropic>=0.18.0  # 仅方案B需要
```

### 步骤5：提交代码到 GitHub

```bash
# 添加所有文件
git add .

# 提交
git commit -m "feat: Add GitHub Actions workflow for Weibo hot analysis"

# 添加远程仓库（替换为您的仓库地址）
git remote add origin https://github.com/YOUR_USERNAME/weibo-hot-analysis.git

# 推送代码
git branch -M main
git push -u origin main
```

### 步骤6：验证工作流

1. 进入 GitHub 仓库的 "Actions" 页面
2. 点击左侧的 "Weibo Hot Search Analysis"
3. 点击 "Run workflow" 手动触发测试
4. 查看执行日志

### 步骤7：查看报告

报告将保存在：
- **GitHub Artifacts**: Actions → 点击运行记录 → Artifacts 下载
- **Repository**: `output/` 目录（如果启用了提交）

---

## 🎯 方案选择建议

| 场景 | 推荐方案 | 原因 |
|-----|---------|------|
| 快速上线 | 方案A | 无需修改代码，立即可用 |
| 追求分析质量 | 方案B | Claude AI提供真正洞察 |
| 预算有限 | 方案A | Claude API有调用成本 |
| 长期运营 | 方案B | 可扩展性强，效果更好 |

---

## ⚠️ 注意事项

1. **API配额限制**
   - Tianapi: 免费版每天100次调用
   - Anthropic: 按Token计费，注意用量

2. **运行时长**
   - GitHub Actions 免费版每月2000分钟
   - 每次运行约2-5分钟

3. **安全性**
   - 永远不要将API Key提交到代码仓库
   - 使用 GitHub Secrets 管理敏感信息

4. **时区问题**
   - GitHub Actions 使用 UTC 时间
   - 北京时间8点 = UTC 0点

---

## 📊 成本估算

### 方案A（仅Tianapi）
- Tianapi: 免费版足够（100次/天）
- GitHub Actions: 免费（2000分钟/月）

### 方案B（+Claude）
- Tianapi: 免费
- Anthropic API:
  - 每次分析约10个热搜
  - 每个热搜约500-1000 tokens
  - 估计每次运行: $0.01-0.05
  - 每月(30天): $0.30-1.50

---

## 🔧 故障排查

### 常见问题

| 问题 | 解决方案 |
|-----|---------|
| API调用失败 | 检查Secrets配置是否正确 |
| 工作流不执行 | 检查cron表达式和时区 |
| HTML报告空白 | 查看Actions日志，检查文件生成路径 |
| Claude API超时 | 增加timeout参数，或减少并发数量 |

---

## 📈 后续优化建议

1. **多平台支持**: 扩展到抖音、知乎热搜
2. **报告美化**: 添加更多可视化图表
3. **邮件通知**: 分析完成后发送邮件摘要
4. **历史追踪**: 建立热搜趋势数据库
5. **竞品分析**: 自动对比相似产品

---

## 📞 技术支持

如有问题，请检查：
1. GitHub Actions 运行日志
2. API 服务状态页面
3. 本地测试脚本是否正常运行
