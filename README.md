# 微信读书划线卡片

把微信读书的划线自动同步为：
1. **手机卡片网页**（随时翻看回顾）
2. **A4 可裁剪卡片 PDF**（打印用）

每天自动更新，无需手动操作。

---

## 你需要做的事（按顺序）

### 第 1 步：注册 GitHub 账号（2 分钟）

如果你还没有 GitHub 账号：

1. 打开 https://github.com/signup
2. 填邮箱、密码、用户名，完成注册
3. 去邮箱点验证链接

> GitHub 是全球最大的代码托管平台，免费账号完全够用。我们的"自动同步"靠它实现。

---

### 第 2 步：获取微信读书 API Key（5 分钟）

1. 电脑浏览器打开：https://weread.qq.com/r/weread-skills
2. 用手机微信扫码登录
3. 页面会显示你的 **API Key**（一串字符）
4. 复制保存好，后面要用

> ⚠️ 这个 Key 等于你微信读书账号的钥匙，**不要发给任何人、不要截图发到网上**。如果泄露，重新登录一次旧 Key 就会失效。

---

### 第 3 步：Fork 这个仓库（1 分钟）

1. 登录 GitHub 后，在本仓库页面（就是你 Fork 来的这个）点右上角 **Fork**
2. 选择你的账号作为目标，点 **Create fork**
3. 现在你有了一份自己的仓库：`https://github.com/你的用户名/weread-cards-project`

---

### 第 4 步：配置 API Key（2 分钟）

1. 进入你 Fork 后的仓库页面
2. 点 **Settings** → 左侧 **Secrets and variables** → **Actions**
3. 点 **New repository secret**
4. 填写：
   - Name：`WEREAD_API_KEY`
   - Secret：粘贴你第 2 步拿到的 API Key
5. 点 **Add secret**

---

### 第 5 步：启用 GitHub Actions（1 分钟）

1. 进入你 Fork 后的仓库，点顶部 **Actions** 标签
2. 如果提示需要启用，点 **I understand my workflows, go ahead and enable them**
3. 左侧找到 **"每日同步微信读书划线"**
4. 点右侧 **Run workflow** → **Run workflow**，手动跑一次测试

跑完后（大约 2-5 分钟），仓库里会多出：
- `data/highlights.json`（划线数据）
- `index.html`（卡片网页）
- `highlights.pdf`（打印用PDF）

---

### 第 6 步：开启 GitHub Pages（1 分钟，用于手机访问）

> 如果你用 Vercel（见第 7 步），可以跳过这一步。但 GitHub Pages 更简单，建议先试这个。

1. 进入仓库 **Settings** → 左侧 **Pages**
2. **Source** 选 **Deploy from a branch**
3. **Branch** 选 `main`，文件夹选 `/ (root)`
4. 点 **Save**
5. 等几分钟后，页面顶部会显示你的网址：
   `https://你的用户名.github.io/weread-cards-project/`

手机浏览器打开这个网址，就是你的划线卡片网页。
可以加到手机桌面（Safari 点分享 → 添加到主屏幕；Chrome 点菜单 → 添加到主屏幕），像 App 一样打开。

---

### 第 7 步（可选）：用 Vercel 部署，国内访问更快

如果 GitHub Pages 在你的网络下打开慢，用 Vercel：

1. 打开 https://vercel.com ，点 **Sign Up**，选 **Continue with GitHub**，用 GitHub 账号登录
2. 授权 Vercel 访问你的 GitHub
3. 点 **Add New** → **Project**
4. 找到 `weread-cards-project` 仓库，点 **Import**
5. 其他都不用改，直接点 **Deploy**
6. 等大约 1 分钟，部署完成后会给你一个网址：
   `https://weread-cards-project-xxx.vercel.app`

这个网址国内访问比 GitHub Pages 快得多。手机打开即可，同样可以加到主屏幕。

> 之后每天 GitHub Actions 自动跑完，Vercel 会自动检测到仓库更新，重新部署。你什么都不用做。

---

## 日常使用

### 手机回顾
- 打开网页链接（GitHub Pages 或 Vercel 的地址）
- 上下滑动浏览卡片，每张卡是一条划线
- 顶部搜索框可搜划线内容
- 顶部下拉可按书筛选
- 右下角"下载PDF"可跳转打印版

### 打印
- 网页右下角点"下载PDF"，或直接在仓库里下载 `highlights.pdf`
- A4 纸打印，每页 6 张卡片（2×3），沿虚线裁剪

### 自动更新
- **你什么都不用做**。GitHub Actions 每天凌晨 3 点自动运行
- 拉取微信读书新划线 → 更新网页和 PDF
- 手机刷新网页就是最新内容

---

## 常见问题

### Q: Actions 运行失败怎么办？
进 **Actions** 标签，点失败的那次运行，看报错。最常见的原因：
- `WEREAD_API_KEY` 没配或填错 → 重新配 Secret
- API Key 失效 → 重新去微信读书网页版拿新的 Key

### Q: GitHub Pages 打不开/很慢？
用第 7 步的 Vercel 方案，国内访问稳定。

### Q: 划线数据会丢失吗？
不会。所有划线存在你 GitHub 仓库的 `data/highlights.json` 里，是你的私有备份。

### Q: 支持想法/笔记吗？
当前版本只同步划线。如需同步想法（你写的批注），可以在 `sync_weread.py` 里扩展。

### Q: 多久同步一次？
默认每天一次。想更频繁，改 `.github/workflows/sync.yml` 里的 cron 表达式。也可以随时在 Actions 页面手动 Run workflow。

---

## 文件说明

| 文件/目录 | 作用 |
|---|---|
| `scripts/sync_weread.py` | 拉取微信读书划线 → `data/highlights.json` |
| `scripts/generate_html.py` | 生成手机卡片网页 `index.html` |
| `scripts/generate_pdf.py` | 生成 A4 打印 PDF `highlights.pdf` |
| `.github/workflows/sync.yml` | GitHub Actions 每日定时任务 |
| `vercel.json` | Vercel 部署配置 |
| `data/highlights.json` | 划线数据（自动生成） |
