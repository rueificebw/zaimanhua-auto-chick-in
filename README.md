# Zaimanhua Auto Check-in

基于 GitHub Actions 的再漫画 (zaimanhua.com) 每日任务自动化工具。

## 功能特性

| 功能 | 说明 | 触发时间 (北京) |
|-----|------|----------------|
| 每日签到 | 自动完成签到任务、领取积分、领取VIP福利 | 8:00 |
| 每日评论 | 在随机漫画下发表评论 | 9:30 |
| 每日阅读 | 自动阅读漫画 | 10:00 |
| 每日抽奖 | 完成任务并自动抽奖 | 11:00 |
| 四周年活动 | 发送祝福 + 转盘抽奖 | 5:00-23:00 每20分钟 |
| 新年活动 | 完成任务 + 祝福抽奖 | 8:00-23:00 每15分钟 |
| 积分领取 | 任务完成后自动领取积分 | 随任务执行 |

其他特性：
- 支持多账号（最多 5 个）
- 日志显示账号真实用户名，便于识别
- Cookie 失效自动检测，workflow 失败触发邮件通知
- 所有任务支持手动触发
- 智能跳过无效/付费章节
- 避免重复评论同一漫画

### 抽奖功能说明

抽奖活动入口：https://luck-draw.zaimanhua.com/

> **注意事项：**
> - 该页面需要在**手机端**或**移动端浏览器**访问
> - **首次使用**需要手动关注官方微博，之后脚本可自动完成任务
> - 抽奖任务包括：关注微博、分享页面、阅读漫画

### 四周年活动说明

活动入口：https://activity.zaimanhua.com/draw-4th/

> **活动时间：** 2026.1.16 - 2026.1.22
>
> **功能说明：**
> - **发送祝福**：自动在弹幕墙发送祝福语
> - **转盘抽奖**：自动使用所有可用抽奖次数
>
> **触发频率：** 北京时间 5:00-23:00，每 20 分钟触发一次
>
> **注意：** 活动结束后可禁用或删除 `draw_4th.yml` workflow

### 新年活动说明

活动入口：https://activity.zaimanhua.com/newYear/

> **活动时间：** 2026.2.15 - 2026.2.23，每天 10:00-24:00
>
> **功能说明：**
> - **分享任务**：自动完成分享获取抽奖机会
> - **观看漫画**：通过 Playwright 访问漫画页面完成任务
> - **祝福评论**：每次执行发送一条随机祝福弹幕，获取抽奖机会
> - **自动抽奖**：用完所有可用抽奖次数
>
> **触发频率：** 北京时间 8:00-23:00，每 15 分钟触发一次
>
> **注意：** 活动结束后可禁用或删除 `2026new_year.yml` workflow

### 每日评论功能说明

> **重要：账号需要绑定手机号才能正常发表评论**
>
> 未绑定手机号的账号可以"发送"评论（前端不阻止），但评论不会真正发布到评论区，任务也不会完成。
> 如果发现评论任务一直失败，请检查账号是否已绑定手机号。

## 快速开始

### 1. Fork 本仓库

点击右上角的 **Fork** 按钮，将仓库复制到你的账号下。

### 2. 获取 Cookie

1. 在浏览器中登录 https://i.zaimanhua.com/
2. 按 **F12** 打开开发者工具
3. 切换到 **Console（控制台）** 标签
4. 输入以下命令并回车：
   ```javascript
   document.cookie
   ```
5. 复制输出的整个字符串（去掉首尾引号）

### 3. 配置 GitHub Secret

1. 进入你 Fork 的仓库
2. 点击 **Settings** → **Secrets and variables** → **Actions**
3. 点击 **New repository secret**
4. Name 填写：`ZAIMANHUA_COOKIE`
5. Value 填写：上一步复制的 Cookie 字符串
6. 点击 **Add secret**

### 4. 启用 Actions

1. 进入仓库的 **Actions** 标签
2. 如果看到提示，点击 **I understand my workflows, go ahead and enable them**
3. 任务将按计划自动运行

### 5. 手动测试

1. 进入 **Actions** 标签
2. 在左侧选择要测试的 workflow：
   - **Zaimanhua Auto Check-in** - 签到
   - **Daily Comment** - 评论
   - **Daily Watch** - 阅读
   - **Daily Lottery** - 抽奖
   - **New Year Activity** - 新年活动
3. 点击 **Run workflow** → 选择分支 → **Run workflow**
4. 查看运行日志确认任务成功

## 多账号配置

如需为多个账号执行任务，添加多个 Secret：

| Secret 名称 | 说明 |
|------------|------|
| `ZAIMANHUA_COOKIE` | 默认账号 |
| `ZAIMANHUA_COOKIE_1` | 账号 1 |
| `ZAIMANHUA_COOKIE_2` | 账号 2 |
| `ZAIMANHUA_COOKIE_3` | 账号 3 |
| `ZAIMANHUA_COOKIE_4` | 账号 4 |
| `ZAIMANHUA_COOKIE_5` | 账号 5 |

> 所有配置的账号都会依次执行任务。

## 项目结构

```
├── src/
│   ├── checkin.py      # 签到脚本
│   ├── comment.py      # 评论脚本
│   ├── auto_read.py    # 阅读脚本 (API 模拟)
│   ├── lottery.py      # 抽奖脚本
│   ├── draw_4th.py     # 四周年活动脚本
│   ├── 2026new_year.py # 新年活动脚本
│   └── utils.py        # 共享工具函数
├── .github/workflows/
│   ├── checkin.yml     # 签到 workflow
│   ├── comment.yml     # 评论 workflow
│   ├── watch.yml       # 阅读 workflow
│   ├── lottery.yml     # 抽奖 workflow
│   ├── draw_4th.yml    # 四周年活动 workflow
│   └── 2026new_year.yml # 新年活动 workflow
└── requirements.txt    # Python 依赖
```

## 任务时间表

| Workflow | UTC 时间 | 北京时间 |
|----------|---------|---------|
| 签到 | 00:00 | 08:00 |
| 评论 | 01:30 | 09:30 |
| 阅读 | 02:00 | 10:00 |
| 抽奖 | 03:00 | 11:00 |
| 四周年活动 | 21:00-15:00 每20分钟 | 5:00-23:00 每20分钟 |
| 新年活动 | 0:00-15:00 每15分钟 | 8:00-23:00 每15分钟 |

## 注意事项

- **Cookie 有效期**：Cookie 可能会过期，失效时 workflow 会自动失败并触发邮件通知，届时请按下方步骤更新
- **GitHub Actions 限制**：免费账户每月 2000 分钟，阅读任务约需 15 分钟/次
- **GitHub 通知设置**：确保在 GitHub Settings > Notifications 中开启 Actions 失败通知
- **隐私安全**：Cookie 存储在 GitHub Secrets 中，不会公开显示

## Cookie 过期更新

当 Cookie 失效时，workflow 运行日志会显示如下错误：

```
[ERROR] Cookie 无效: API 返回错误: 用户未登录
请更新 默认账号 (张三) 的 Cookie
```

同时 GitHub Actions 会因非零退出码触发失败通知邮件。收到通知后，按以下步骤更新：

### 1. 重新获取 Cookie

1. 在浏览器中打开 https://i.zaimanhua.com/ 并**重新登录**（或确认已登录）
2. 按 **F12** 打开开发者工具
3. 切换到 **Console（控制台）** 标签
4. 输入以下命令并回车：
   ```javascript
   document.cookie
   ```
5. 复制输出的整个字符串（去掉首尾引号）

### 2. 更新 GitHub Secret

1. 进入你 Fork 的仓库
2. 点击 **Settings** → **Secrets and variables** → **Actions**
3. 找到需要更新的 Secret（根据日志中提示的账号名称对应）：
   - `ZAIMANHUA_COOKIE` — 默认账号
   - `ZAIMANHUA_COOKIE_1` — 账号 1
   - 以此类推...
4. 点击该 Secret 右侧的 **编辑（铅笔图标）**
5. 在 Value 中粘贴新的 Cookie 字符串
6. 点击 **Update secret**

### 3. 验证更新

1. 进入 **Actions** 标签
2. 选择任意 workflow，点击 **Run workflow** 手动触发
3. 查看运行日志，确认不再出现 Cookie 无效的错误

> **提示**：日志中会显示账号的真实用户名（如 `默认账号 (张三)`），方便快速定位需要更新的账号。

## 技术栈

- Python 3.11
- Playwright（浏览器自动化）
- GitHub Actions（定时任务）

## 免责声明

**重要提示：请在使用本项目前仔细阅读以下声明**

1. **仅供学习交流**：本项目仅供学习和技术交流使用，不得用于任何商业用途或非法目的。

2. **风险自负**：使用本项目可能违反再漫画网站的服务条款。因使用本项目而导致的任何账号封禁、数据丢失或其他损失，作者概不负责。

3. **遵守法律法规**：用户应遵守当地法律法规及再漫画网站的使用条款。如有违反，后果自负。

4. **不提供担保**：本项目按"原样"提供，不提供任何形式的明示或暗示担保。

5. **Cookie 安全**：请妥善保管您的 Cookie 信息，不要泄露给他人。

6. **随时停止维护**：作者保留随时停止维护本项目的权利，恕不另行通知。

**使用本项目即表示您已阅读、理解并同意以上免责声明。如不同意，请立即停止使用并删除本项目。**

## License

MIT
