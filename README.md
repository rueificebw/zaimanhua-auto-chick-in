# Zaimanhua Auto Check-in

基于 GitHub Actions 的再漫画 (zaimanhua.com) 自动签到工具。

## 功能

- 每天自动签到三次（北京时间 8:00、12:00、20:00）
- **每日自动评论**（北京时间 9:30）
- **每日自动阅读**（北京时间 10:00，阅读12分钟）
- **自动领取任务积分**
- 支持多账号签到（最多 5 个账号）
- 使用 Playwright 模拟浏览器操作
- 支持手动触发签到
- 自动检测签到状态，避免重复签到

## GitHub Actions Workflows

| Workflow | 触发时间 (北京) | 功能 |
|----------|----------------|------|
| `checkin.yml` | 8:00, 12:00, 20:00 | 每日签到 |
| `comment.yml` | 9:30 | 每日评论 |
| `watch.yml` | 10:00 | 每日阅读（12分钟） |

所有 workflow 都支持手动触发（workflow_dispatch）。

## 使用方法

### 1. Fork 本仓库

点击右上角的 Fork 按钮，将仓库复制到你的账号下。

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
2. 点击 **Settings** -> **Secrets and variables** -> **Actions**
3. 点击 **New repository secret**
4. Name 填写：`ZAIMANHUA_COOKIE`
5. Value 填写：上一步复制的 Cookie 字符串
6. 点击 **Add secret**

#### 多账号配置（可选）

如需签到多个账号，添加多个 Secret：

| Secret 名称 | 说明 |
|------------|------|
| `ZAIMANHUA_COOKIE` | 默认账号（单账号时使用） |
| `ZAIMANHUA_COOKIE_1` | 账号 1 |
| `ZAIMANHUA_COOKIE_2` | 账号 2 |
| `ZAIMANHUA_COOKIE_3` | 账号 3 |
| ... | 最多支持 5 个账号 |

> 注意：`ZAIMANHUA_COOKIE` 和 `ZAIMANHUA_COOKIE_1` 可以同时配置，脚本会依次签到所有账号。

### 4. 启用 Actions

1. 进入仓库的 **Actions** 标签
2. 如果看到提示，点击 **I understand my workflows, go ahead and enable them**
3. 签到任务将按计划自动运行

### 5. 手动测试

1. 进入 **Actions** 标签
2. 选择 **Zaimanhua Auto Check-in**
3. 点击 **Run workflow** -> **Run workflow**
4. 查看运行日志确认签到成功

## 签到时间

| UTC 时间 | 北京时间 |
|---------|---------|
| 00:00   | 08:00   |
| 04:00   | 12:00   |
| 12:00   | 20:00   |

## 注意事项

- **Cookie 有效期**：Cookie 可能会过期，建议每月检查一次，如签到失败请更新 Cookie
- **GitHub Actions 限制**：免费账户每月有 2000 分钟运行时间，每次签到约需 1-2 分钟
- **隐私安全**：Cookie 存储在 GitHub Secrets 中，不会公开显示

## 技术栈

- Python 3.11
- Playwright（浏览器自动化）
- GitHub Actions（定时任务）

## 免责声明

**重要提示：请在使用本项目前仔细阅读以下声明**

1. **仅供学习交流**：本项目仅供学习和技术交流使用，不得用于任何商业用途或非法目的。

2. **风险自负**：使用本项目可能违反再漫画网站的服务条款。因使用本项目而导致的任何账号封禁、数据丢失或其他损失，作者概不负责。

3. **遵守法律法规**：用户应遵守当地法律法规及再漫画网站的使用条款。如有违反，后果自负。

4. **不提供担保**：本项目按"原样"提供，不提供任何形式的明示或暗示担保，包括但不限于适销性、特定用途适用性和非侵权性。

5. **Cookie 安全**：请妥善保管您的 Cookie 信息，不要泄露给他人。Cookie 泄露可能导致账号被盗用。

6. **随时停止维护**：作者保留随时停止维护本项目的权利，恕不另行通知。

**使用本项目即表示您已阅读、理解并同意以上免责声明。如不同意，请立即停止使用并删除本项目。**

## License

MIT
