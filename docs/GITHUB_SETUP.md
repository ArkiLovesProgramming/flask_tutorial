# GitHub 上传指南

本指南将带你完成将项目上传到 GitHub 的完整流程。

## 📋 前置准备

### 1. 确保已安装 Git
```powershell
git --version
```

### 2. 配置 Git 用户信息（如果还没有配置）

```powershell
# 设置用户名（使用你的 GitHub 用户名或真实姓名）
git config --global user.name "Your Name"

# 设置邮箱（使用你的 GitHub 邮箱）
git config --global user.email "your.email@example.com"

# 验证配置
git config --global user.name
git config --global user.email
```

> **注意**：如果只想为当前项目设置，去掉 `--global` 参数。

---

## 🚀 步骤 1: 初始化 Git 仓库（已完成）

```powershell
cd "C:\Users\betaw\Documents\Visual Studio Projects\Flask_Celery_POC"
git init
```

✅ **已完成**

---

## 📝 步骤 2: 添加文件到暂存区

```powershell
# 添加所有文件（.gitignore 会自动排除不需要的文件）
git add .

# 查看将要提交的文件
git status
```

---

## 💾 步骤 3: 创建初始提交

```powershell
git commit -m "Initial commit: Flask Celery POC with Docker support"
```

---

## 🌐 步骤 4: 在 GitHub 上创建仓库

### 方法一：使用 GitHub 网页

1. **登录 GitHub**
   - 访问 https://github.com
   - 登录你的账户

2. **创建新仓库**
   - 点击右上角的 **"+"** → **"New repository"**
   - 或者访问：https://github.com/new

3. **填写仓库信息**
   - **Repository name**: `Flask_Celery_POC`（或你喜欢的名字）
   - **Description**: `Flask application with Celery distributed task queue and Redis broker`
   - **Visibility**: 
     - ✅ **Public** - 公开（任何人都能看到）
     - 🔒 **Private** - 私有（只有你能看到）
   - ⚠️ **不要**勾选以下选项：
     - ❌ Add a README file（我们已经有了）
     - ❌ Add .gitignore（我们已经有了）
     - ❌ Choose a license（可以稍后添加）

4. **点击 "Create repository"**

5. **复制仓库 URL**
   - 创建后会显示仓库页面
   - 复制 HTTPS 或 SSH URL，例如：
     - HTTPS: `https://github.com/yourusername/Flask_Celery_POC.git`
     - SSH: `git@github.com:yourusername/Flask_Celery_POC.git`

### 方法二：使用 GitHub CLI（如果已安装）

```powershell
# 安装 GitHub CLI: https://cli.github.com/
gh repo create Flask_Celery_POC --public --source=. --remote=origin --push
```

---

## 🔗 步骤 5: 添加远程仓库并推送

### 使用 HTTPS（推荐，简单）

```powershell
# 添加远程仓库（替换为你的实际 URL）
git remote add origin https://github.com/yourusername/Flask_Celery_POC.git

# 验证远程仓库
git remote -v

# 推送代码到 GitHub
git branch -M main  # 将分支重命名为 main（GitHub 默认）
git push -u origin main
```

### 使用 SSH（需要配置 SSH 密钥）

```powershell
# 添加远程仓库
git remote add origin git@github.com:yourusername/Flask_Celery_POC.git

# 推送代码
git branch -M main
git push -u origin main
```

---

## 🔐 步骤 6: 身份验证

### HTTPS 方式
- 如果提示输入用户名和密码：
  - **用户名**: 你的 GitHub 用户名
  - **密码**: 使用 **Personal Access Token (PAT)**，而不是账户密码
  - 创建 PAT: https://github.com/settings/tokens
    - 权限选择：`repo`（完整仓库访问权限）

### SSH 方式
- 需要先配置 SSH 密钥
- 参考：https://docs.github.com/en/authentication/connecting-to-github-with-ssh

---

## ✅ 验证上传成功

1. **刷新 GitHub 仓库页面**
   - 应该能看到所有文件

2. **检查文件**
   - 确认 `.env` 文件**没有**被上传（应该在 .gitignore 中）
   - 确认敏感信息没有被提交

3. **查看提交历史**
   ```powershell
   git log --oneline
   ```

---

## 📌 后续操作

### 添加仓库描述和主题
在 GitHub 仓库页面：
- 点击 **⚙️ Settings** → **General**
- 添加 **Description** 和 **Topics**（如：`flask`, `celery`, `redis`, `docker`, `python`）

### 添加 LICENSE
1. 在 GitHub 仓库页面点击 **"Add file"** → **"Create new file"**
2. 文件名输入：`LICENSE`
3. GitHub 会自动提示选择许可证模板
4. 推荐：**MIT License** 或 **Apache License 2.0**

### 添加 README 徽章（可选）
在 `README.md` 顶部添加：
```markdown
![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![Flask](https://img.shields.io/badge/flask-2.0-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
```

---

## 🛠️ 常用 Git 命令

```powershell
# 查看状态
git status

# 查看提交历史
git log --oneline

# 查看远程仓库
git remote -v

# 拉取最新更改
git pull origin main

# 添加新文件并提交
git add .
git commit -m "描述你的更改"
git push origin main

# 创建新分支
git checkout -b feature/new-feature
git push -u origin feature/new-feature
```

---

## ⚠️ 注意事项

### 不要提交的文件
- ✅ `.env` - 环境变量（已在 .gitignore 中）
- ✅ `instance/db/*.db` - 数据库文件（已在 .gitignore 中）
- ✅ `__pycache__/` - Python 缓存（已在 .gitignore 中）
- ✅ `.venv/` - 虚拟环境（已在 .gitignore 中）

### 应该提交的文件
- ✅ `.env.example` - 环境变量模板
- ✅ `README.md` - 项目说明
- ✅ `requirements.txt` 或 `pyproject.toml` - 依赖管理
- ✅ `Dockerfile` 和 `docker-compose.yml` - Docker 配置
- ✅ 源代码文件

---

## 🆘 遇到问题？

### 问题 1: 推送被拒绝
```powershell
# 如果远程仓库有 README 等文件，需要先拉取
git pull origin main --allow-unrelated-histories
git push origin main
```

### 问题 2: 忘记添加 .gitignore
```powershell
# 如果已经提交了敏感文件，需要从 Git 历史中删除
git rm --cached .env
git commit -m "Remove .env from repository"
git push origin main
```

### 问题 3: 更改远程仓库 URL
```powershell
git remote set-url origin https://github.com/yourusername/new-repo-name.git
```

---

## 📚 参考资源

- [Git 官方文档](https://git-scm.com/doc)
- [GitHub 文档](https://docs.github.com/)
- [创建 Personal Access Token](https://github.com/settings/tokens)
- [SSH 密钥配置](https://docs.github.com/en/authentication/connecting-to-github-with-ssh)

