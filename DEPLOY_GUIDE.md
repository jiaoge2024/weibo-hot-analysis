# 微博热搜分析 - 智谱AI部署指南

## ✅ 配置信息已确认

| 项目 | 值 |
|-----|-----|
| Tianapi API Key | `aae54e1454e686a2eaca4e11de03d6fb` |
| 自定义API端点 | `https://open.bigmodel.cn/api/anthropic` |
| 模型ID | `glm-4.7` |
| API Key | `cd733ef9614e4597b6d7c742f6584e47.nB2bG9CRC6vZGwlw` |

---

## 🚀 部署步骤

### 步骤1：在GitHub上创建仓库

1. 访问 https://github.com/new
2. 填写仓库信息：
   - **Repository name**: `weibo-hot-analysis`
   - **Description**: `微博热搜产品创意分析 - 智谱AI增强版`
   - **Visibility**: Public 或 Private
   - **不要**勾选任何初始化选项
3. 点击 **Create repository**

### 步骤2：推送代码到GitHub

```bash
cd "D:\AI资料库\01 编程开发\claude skills\skills\weibo-resou"
git remote add origin https://github.com/jiaoge2024/weibo-hot-analysis.git
git push -u origin main
```

### 步骤3：配置GitHub Secrets

1. 进入GitHub仓库 → **Settings** → **Secrets and variables** → **Actions**
2. 点击 **New repository secret**
3. 添加以下4个Secrets：

| Secret 名称 | Secret 值 |
|------------|-----------|
| `TIANAPI_KEY` | `aae54e1454e686a2eaca4e11de03d6fb` |
| `ANTHROPIC_API_KEY` | `cd733ef9614e4597b6d7c742f6584e47.nB2bG9CRC6vZGwlw` |
| `CUSTOM_API_URL` | `https://open.bigmodel.cn/api/anthropic` |
| `CUSTOM_MODEL_ID` | `glm-4.7` |

### 步骤4：验证工作流

1. 进入仓库的 **Actions** 标签
2. 选择 "Weibo Hot Search Analysis (智谱AI SDK)"
3. 点击 **Run workflow**
4. 点击绿色的 **Run workflow**
5. 查看执行日志

---

## 📊 执行后结果

- **自动执行**: 每天早上8点（北京时间）
- **报告位置**:
  - GitHub Artifacts（30天）
  - 仓库 `output/` 目录

---

## 🔧 技术架构

```
GitHub Actions (每天8点)
    ↓
Tianapi API → 获取微博热搜TOP10
    ↓
百度搜索 → 获取话题背景信息
    ↓
智谱AI (glm-4.7) → 深度产品创意分析
    ↓
生成HTML报告 → 上传到Artifacts + 提交到仓库
```
