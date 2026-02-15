"""2026 马年春节活动自动化模块

活动页面: https://activity.zaimanhua.com/newYear/
活动时间: 2/15-2/23 每天 10:00-24:00
每次执行: 完成任务 → 发一条祝福 → 用完所有抽奖次数
通过 GitHub Actions 每 15 分钟触发一次，覆盖 8:00-23:00
"""
import hashlib
import random
import time
import requests

from utils import (
    extract_user_info_from_cookies,
    get_all_cookies,
    parse_cookies,
    validate_cookie,
)
from playwright.sync_api import sync_playwright

# 配置
BASE_URL = "https://activity.zaimanhua.com"
SECRET = "z&m$h*_159753twt"
MOBILE_UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"

BLESSINGS = [
    "新春快乐！马到成功！",
    "马年大吉，万事如意！",
    "龙马精神，前程似锦！",
    "新年快乐，阖家幸福！",
    "马年行大运，好运连连！",
    "一马当先，事事顺心！",
    "马到功成，心想事成！",
    "新春吉祥，福满人间！",
    "马年如意，步步高升！",
    "金马送福，年年有余！",
    "策马奔腾，未来可期！",
    "马跃新春，喜气洋洋！",
    "天马行空，自由自在！",
    "快马加鞭，再创辉煌！",
    "马上有福，幸福美满！",
    "万马奔腾，蒸蒸日上！",
    "骏马奔驰，前途无量！",
    "马年鸿运，财源广进！",
    "千里马志，鹏程万里！",
    "马年快乐，平安喜乐！",
]


def generate_sign(channel: str, timestamp: int) -> str:
    """生成 API 签名: MD5(channel + timestamp + SECRET)"""
    raw = f"{channel}{timestamp}{SECRET}"
    return hashlib.md5(raw.encode()).hexdigest()


def get_api_headers(token: str) -> dict:
    """生成 API 请求头"""
    return {
        "Authorization": f"Bearer {token}",
        "User-Agent": MOBILE_UA,
        "Referer": f"{BASE_URL}/newYear/",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9",
    }


def get_api_params() -> dict:
    """生成通用 API 参数（channel, timestamp, sign）"""
    timestamp = int(time.time() * 1000)
    return {
        "channel": "h5",
        "timestamp": timestamp,
        "sign": generate_sign("h5", timestamp),
    }


def check_status(token: str) -> dict:
    """调用 draw_load 获取活动状态（抽奖次数、任务完成情况）"""
    headers = get_api_headers(token)
    params = get_api_params()

    try:
        resp = requests.get(
            f"{BASE_URL}/drawApi/draw/draw_load",
            params=params,
            headers=headers,
            timeout=10,
        )
        return resp.json()
    except Exception as e:
        print(f"  [x] 获取活动状态异常: {e}")
        return {}


def do_share(token: str) -> bool:
    """完成分享任务"""
    headers = get_api_headers(token)
    params = get_api_params()

    try:
        resp = requests.get(
            f"{BASE_URL}/drawApi/draw/share",
            params=params,
            headers=headers,
            timeout=10,
        )
        result = resp.json()
        if result.get("errno") == 0:
            print("  [v] 分享任务完成")
            return True
        else:
            print(f"  [x] 分享任务失败: {result.get('errmsg', '未知错误')}")
            return False
    except Exception as e:
        print(f"  [x] 分享任务异常: {e}")
        return False


def do_comment(token: str) -> bool:
    """发送一条随机祝福评论（弹幕祝福 source=1）"""
    headers = get_api_headers(token)
    headers["Content-Type"] = "application/json"
    params = get_api_params()

    blessing = random.choice(BLESSINGS)
    body = {"con": blessing, "source": 1}

    try:
        resp = requests.post(
            f"{BASE_URL}/drawApi/draw/add_comment",
            params=params,
            headers=headers,
            json=body,
            timeout=10,
        )
        result = resp.json()
        if result.get("errno") == 0:
            print(f"  [v] 祝福发送成功: {blessing}")
            return True
        else:
            print(f"  [x] 祝福发送失败: {result.get('errmsg', '未知错误')}")
            return False
    except Exception as e:
        print(f"  [x] 祝福发送异常: {e}")
        return False


def do_read_comic(cookie_str: str) -> bool:
    """用 Playwright 访问漫画页面触发阅读任务"""
    cookies = parse_cookies(cookie_str)
    activity_cookies = [
        {"name": c["name"], "value": c["value"], "domain": "activity.zaimanhua.com", "path": "/"}
        for c in cookies
    ]
    main_cookies = [
        {"name": c["name"], "value": c["value"], "domain": ".zaimanhua.com", "path": "/"}
        for c in cookies
    ]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=MOBILE_UA,
            viewport={"width": 375, "height": 812},
        )
        context.add_cookies(activity_cookies + main_cookies)
        page = context.new_page()

        try:
            print("    访问活动页面...")
            page.goto(f"{BASE_URL}/newYear/", wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(5000)

            read_btn = page.locator("text=去观看").first
            if read_btn.is_visible(timeout=3000):
                read_btn.click(timeout=3000)
                page.wait_for_timeout(5000)
                print("    已点击去观看按钮")
            else:
                print("    未找到观看按钮，直接访问漫画页面...")
                page.goto("https://www.zaimanhua.com/", wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(3000)

                comic_link = page.locator("a[href*='/comic/']").first
                if comic_link.is_visible(timeout=3000):
                    comic_link.click(timeout=3000)
                    page.wait_for_timeout(5000)
                    print("    已访问漫画页面")

            print("  [v] 阅读漫画任务尝试完成")
            return True
        except Exception as e:
            print(f"  [x] 阅读漫画任务异常: {e}")
            return False
        finally:
            browser.close()


def do_drawing(token: str) -> dict:
    """执行一次抽奖"""
    headers = get_api_headers(token)
    params = get_api_params()

    try:
        resp = requests.get(
            f"{BASE_URL}/drawApi/draw/drawing",
            params=params,
            headers=headers,
            timeout=10,
        )
        result = resp.json()
        errno = result.get("errno")
        data = result.get("data", {})

        if errno == 0:
            prize_info = data.get("prize", {})
            prize_name = prize_info.get("name") or data.get("prize_name") or "未知奖品"
            print(f"  [v] 抽奖成功！获得: {prize_name}")
        else:
            print(f"  [x] 抽奖失败: {result.get('errmsg', '未知错误')}")
        return result
    except Exception as e:
        print(f"  [x] 抽奖异常: {e}")
        return {}


def draw_all(token: str) -> int:
    """用完所有可用抽奖次数，返回抽奖次数"""
    status = check_status(token)
    if status.get("errno") != 0:
        return 0

    times = status.get("data", {}).get("times", 0)
    if times <= 0:
        return 0

    print(f"\n  [抽奖] 可用次数: {times}")
    for i in range(times):
        print(f"    第 {i + 1}/{times} 次:")
        do_drawing(token)
        if i < times - 1:
            time.sleep(2)
    return times


def run_new_year(cookie_str: str, account_name: str):
    """单账号单轮新年活动流程（由 cron 每 15 分钟触发）"""
    print(f"\n  === 开始新年活动 ===")

    # 1. 提取 token
    user_info = extract_user_info_from_cookies(cookie_str)
    token = user_info.get("token", "")
    if not token:
        print("  [x] Cookie 中未找到 token")
        return False

    nickname = user_info.get("nickname") or user_info.get("username") or "未知"
    print(f"  用户: {nickname}")

    # 2. 获取当前状态
    print("\n  [1] 获取活动状态...")
    status = check_status(token)
    if status.get("errno") != 0:
        errmsg = status.get("errmsg", "未知错误")
        print(f"  [x] 获取状态失败: {errmsg}")
        if "活动" in errmsg or "时间" in errmsg:
            print("  提示: 活动可能不在开放时间段内 (10:00-24:00)")
        return False

    data = status.get("data", {})
    share_done = data.get("shareTimes", 0) > 0
    read_done = data.get("readingComicTimes", 0) > 0

    # 检查用户登录状态
    uid = data.get("userInfo", {}).get("uid", 0)
    if uid == 0:
        print("  [x] 未登录，token 可能已失效")
        return False

    print(f"    当前抽奖次数: {data.get('times', 0)}")
    print(f"    分享任务: {'已完成' if share_done else '未完成'}")
    print(f"    阅读漫画: {'已完成' if read_done else '未完成'}")

    # 3. 完成一次性任务
    print("\n  [2] 执行任务...")

    if not share_done:
        do_share(token)

    if not read_done:
        do_read_comic(cookie_str)

    # 4. 发送一条祝福
    print("\n  [3] 发送祝福...")
    do_comment(token)

    # 5. 用完所有抽奖次数
    time.sleep(1)
    total = draw_all(token)

    if total == 0:
        print("\n  [!] 没有可用的抽奖次数")

    print(f"\n  === 新年活动结束 (本轮抽奖 {total} 次) ===")
    return True


def main():
    """主函数"""
    print("=== 2026 马年春节活动自动化 ===\n")

    cookies_list = get_all_cookies()
    if not cookies_list:
        print("错误: 请设置 ZAIMANHUA_COOKIE 环境变量")
        return False

    all_success = True
    for account_name, cookie_str in cookies_list:
        print(f"\n{'=' * 50}")
        print(f"账号: {account_name}")
        print("=" * 50)

        # 验证 Cookie 有效性
        is_valid, error_msg = validate_cookie(cookie_str)
        if not is_valid:
            print(f"  [ERROR] Cookie 无效: {error_msg}")
            print(f"  请更新 {account_name} 的 Cookie")
            all_success = False
            continue

        success = run_new_year(cookie_str, account_name)
        if not success:
            all_success = False

    return all_success


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
