# 快速设置指南 - 5分钟完成配置

## 📋 前置准备

在开始之前，请确保您已准备好：
- ✅ GitHub 账号
- ✅ Tianapi API Key（从 https://www.tianapi.com/ 获取）
- ✅ （可选）Anthropic API Key（如需使用Claude AI增强分析）

---

## 步骤1：获取 API Keys（5分钟）

### 1.1 获取 Tianapi API Key（必需）

1. 访问 https://www.tianapi.com/
2. 点击右上角"注册/登录"
3. 登录后进入"控制台" → "API密钥"
4. 复制您的 API Key（格式类似：`aae54e1454e686a2eaca4e11de03d6fb`）

### 1.2 获取 Anthropic API Key（可选）

1. 访问 https://console.anthropic.com/
2. 注册并验证账号
3. 进入 "API Keys" 页面
4. 点击 "Create Key"
5. 复制生成的 API Key（格式类似：`sk-ant-xxxxx`）

---

## 步骤2：配置 GitHub Secrets（3分钟）

### 2.1 进入仓库设置

1. 在 GitHub 上打开您的代码仓库
2. 点击顶部 "Settings" 标签
3. 左侧菜单找到 "Secrets and variables" → "Actions"

### 2.2 添加 Secrets

点击 "New repository secret"，添加以下 secrets：

| Secret 名称 | Secret 值 | 是否必需 |
|------------|-----------|---------|
| `TIANAPI_KEY` | 您的Tianapi API Key | ✅ 必需 |
| `ANTHROPIC_API_KEY` | 您的Anthropic API Key | ⚠️ 可选 |

---

## 步骤3：推送代码到 GitHub（2分钟）

### 3.1 初始化 Git 仓库（如果还没有）

```bash
cd "D:\AI资料库\01 编程开发\claude skills\skills\weibo-resou"
git init
```

### 3.2 添加远程仓库

```bash
# 替换为您的GitHub用户名和仓库名
git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git
```

### 3.3 提交并推送代码

```bash
# 添加所有文件
git add .

# 提交
git commit -m "feat: Add GitHub Actions workflow for Weibo hot analysis"

# 设置主分支
git branch -M main

# 推送代码
git push -u origin main
```

---

## 步骤4：验证工作流（1分钟）

### 4.1 手动触发测试

1. 进入 GitHub 仓库页面
2. 点击 "Actions" 标签
3. 在左侧选择 "Weibo Hot Search Analysis"
4. 点击 "Run workflow" 按钮
5. 选择分支，点击绿色的 "Run workflow"

### 4.2 查看执行日志

1. 等待几秒后刷新页面
2. 点击正在运行的任务查看详情
3. 展开各个步骤查看日志
4. 确认所有步骤都成功完成 ✅

---

## 步骤5：查看生成的报告

### 方式1：从 Artifacts 下载

1. 进入 Actions 页面
2. 点击完成的工作流运行
3. 滚动到底部 "Artifacts" 区域
4. 点击 `weibo-hot-report-XXX` 下载
5. 解压后打开 HTML 文件查看

### 方式2：从仓库查看

如果工作流成功提交了报告：
1. 进入仓库的 `output/` 目录
2. 点击最新的 HTML 文件
3. 直接在浏览器中查看

---

## 🎉 完成！

现在您的 GitHub Actions 已经配置好了！

### 自动运行时间
- **每天早上8点**（北京时间）自动执行
- 分析TOP10热搜并生成报告
- 报告自动保存到仓库和Artifacts

### 手动运行
- 随时在 Actions 页面点击 "Run workflow"
- 可以指定分析的热搜数量（默认10个）

---

## ⚙️ 高级配置

### 修改运行时间

编辑 `.github/workflows/weibo-hot-analysis.yml`：

```yaml
schedule:
  - cron: '0 0 * * *'  # 每天8点 (UTC 0点)
```

常用时间示例：
- `0 0 * * *` - 每天8点
- `0 1 * * *` - 每天9点
- `0 0,12 * * *` - 每天8点和20点
- `0 0 * * 1-5` - 每周一到五8点

### 修改分析数量

在工作流文件中修改：

```yaml
- cron: '0 0 * * *'
  workflow_dispatch:
    inputs:
      count:
        default: '15'  # 修改为15个
```

---

## 🔍 故障排查

| 问题 | 可能原因 | 解决方案 |
|-----|---------|---------|
| 工作流不运行 | 时区设置错误 | cron使用UTC时间，北京时间=UTC+8 |
| API调用失败 | Secret配置错误 | 检查Secret名称和值是否正确 |
| 报告未生成 | 脚本执行出错 | 查看Actions日志，检查错误信息 |
| 无法下载Artifacts | 运行未完成 | 等待工作流完成后再下载 |

---

## 📞 获取帮助

- 查看 [完整迁移方案](./GITHUB_ACTIONS_MIGRATION.md)
- 检查 [GitHub Actions日志](https://docs.github.com/en/actions/monitoring-and-troubleshooting-workflows/using-workflow-run-logs)
- 查看 [Tianapi文档](https://www.tianapi.com/apiview/156)
