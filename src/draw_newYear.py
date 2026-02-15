"""四周年活动自动化模块

活动地址: https://activity.zaimanhua.com/draw-4th/
活动时间: 2026.1.16 - 2026.1.22
功能:
  1. 发送祝福
  2. 转盘抽奖
"""
import os
import re
import time

from utils import extract_user_info_from_cookies, get_all_cookies, parse_cookies
from playwright.sync_api import sync_playwright

# 配置
ACTIVITY_URL = "https://activity.zaimanhua.com/newYear/"
MOBILE_UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
DEBUG_DIR = "debug"


def ensure_debug_dir():
    """确保调试目录存在"""
    if not os.path.exists(DEBUG_DIR):
        os.makedirs(DEBUG_DIR)


def save_debug_info(page, prefix):
    """保存调试信息（截图和HTML）"""
    ensure_debug_dir()
    timestamp = int(time.time())
    try:
        page.screenshot(path=f"{DEBUG_DIR}/{prefix}_{timestamp}.png", full_page=True)
        print(f"    已保存截图: {DEBUG_DIR}/{prefix}_{timestamp}.png")
    except Exception as e:
        print(f"    保存截图失败: {e}")

    try:
        html_content = page.content()
        with open(f"{DEBUG_DIR}/{prefix}_{timestamp}.html", 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"    已保存HTML: {DEBUG_DIR}/{prefix}_{timestamp}.html")
    except Exception as e:
        print(f"    保存HTML失败: {e}")


def create_activity_context(playwright, cookie_str):
    """创建移动端浏览器上下文（为活动域名设置Cookie）"""
    cookies = parse_cookies(cookie_str)

    # 为活动域名设置 cookies
    activity_cookies = []
    for c in cookies:
        activity_cookies.append({
            'name': c['name'],
            'value': c['value'],
            'domain': 'activity.zaimanhua.com',
            'path': '/'
        })

    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent=MOBILE_UA,
        viewport={'width': 375, 'height': 812}  # iPhone X 尺寸
    )
    context.add_cookies(activity_cookies)
    page = context.new_page()

    return browser, context, page


def send_blessing(page) -> bool:
    """发送祝福

    页面结构:
    - 弹幕输入框: .dammu-input
    - 发送按钮: .dammu-send-btn
    """
    print("\n  [祝福] 尝试发送祝福...")

    try:
        # 定位弹幕输入框
        input_elem = page.locator('.dammu-input')
        if input_elem.is_visible(timeout=3000):
            # 输入祝福语
            blessing_text = "四周年快乐！越来越好！"
            input_elem.fill(blessing_text)
            page.wait_for_timeout(500)
            print(f"    已输入祝福: {blessing_text}")
        else:
            print("    未找到弹幕输入框")

        # 定位发送按钮
        send_btn = page.locator('.dammu-send-btn')
        if send_btn.is_visible(timeout=3000):
            send_btn.click()
            page.wait_for_timeout(2000)
            print("    [v] 已点击发送按钮")
            return True
        else:
            print("    [x] 未找到发送按钮")
            return False

    except Exception as e:
        print(f"    [x] 发送祝福异常: {e}")
        return False


def do_lottery(page) -> int:
    """执行转盘抽奖

    页面结构:
    - 抽奖按钮: .pointer (包含 "抽" 图片)
    - 抽奖次数: .draw-count (格式: "次数：4")
    - 中奖弹窗: .winPrize (需要关闭后才能继续抽奖)

    Returns:
        抽奖执行次数
    """
    print("\n  [抽奖] 尝试转盘抽奖...")

    lottery_count = 0

    try:
        # 获取当前抽奖次数
        count_elem = page.locator('.draw-count')
        if count_elem.is_visible(timeout=3000):
            count_text = count_elem.inner_text()
            # 解析 "次数：4" 格式
            match = re.search(r'(\d+)', count_text)
            available_times = int(match.group(1)) if match else 0
            print(f"    当前抽奖次数: {available_times}")
        else:
            print("    未找到抽奖次数显示")
            available_times = 0

        if available_times == 0:
            print("    [!] 没有可用的抽奖次数")
            return 0

        # 定位抽奖按钮 (pointer 区域)
        lottery_btn = page.locator('.pointer')
        if not lottery_btn.is_visible(timeout=3000):
            print("    [x] 未找到抽奖按钮")
            return 0

        # 执行抽奖
        for i in range(available_times):
            # 重新检查剩余次数
            if i > 0:
                count_elem = page.locator('.draw-count')
                if count_elem.is_visible(timeout=2000):
                    count_text = count_elem.inner_text()
                    match = re.search(r'(\d+)', count_text)
                    remaining = int(match.group(1)) if match else 0
                    if remaining == 0:
                        print("    抽奖次数用完")
                        break

            # 点击抽奖
            try:
                lottery_btn.click(timeout=5000)
                print(f"    第 {i + 1} 次抽奖: 已点击")

                # 等待转盘动画完成（约5秒）
                page.wait_for_timeout(5500)

                lottery_count += 1

                # 关闭中奖弹窗 (.winPrize)
                win_popup = page.locator('.winPrize')
                if win_popup.is_visible(timeout=2000):
                    # 获取奖品名称
                    try:
                        prize_name = page.locator('.winPrize .prizeName span').inner_text(timeout=2000)
                        print(f"    获得奖品: {prize_name}")
                    except:
                        pass

                    # 点击关闭按钮 (img.close)
                    try:
                        close_btn = page.locator('.winPrize .close')
                        if close_btn.is_visible(timeout=2000):
                            close_btn.click(timeout=3000)
                            page.wait_for_timeout(1000)
                            print("    已关闭中奖弹窗")
                    except Exception as e:
                        # 如果点击失败，尝试用 JavaScript 关闭
                        try:
                            page.evaluate('document.querySelector(".winPrize")?.remove()')
                            page.wait_for_timeout(500)
                            print("    已强制关闭弹窗")
                        except:
                            pass

                # 间隔等待
                page.wait_for_timeout(1500)

            except Exception as e:
                error_msg = str(e)
                # 检查是否是弹窗拦截导致的点击失败
                if 'winPrize' in error_msg or 'intercepts pointer' in error_msg:
                    print(f"    中奖弹窗拦截，尝试关闭...")
                    try:
                        # 强制关闭弹窗
                        page.evaluate('document.querySelector(".winPrize")?.remove()')
                        page.wait_for_timeout(1000)
                        print("    已强制关闭弹窗")
                    except:
                        pass
                else:
                    print(f"    抽奖点击异常: {e}")
                    break

        if lottery_count > 0:
            print(f"    [v] 完成 {lottery_count} 次抽奖")
        else:
            print("    [!] 没有执行抽奖")

    except Exception as e:
        print(f"    [x] 抽奖异常: {e}")

    return lottery_count


def run_4th_anniversary(cookie_str: str, account_name: str, save_debug: bool = False):
    """执行单账号的四周年活动流程"""
    print(f"\n  === 开始四周年活动 ===")

    user_info = extract_user_info_from_cookies(cookie_str)
    username = user_info.get('nickname', user_info.get('username', '未知'))
    print(f"  用户: {username}")

    with sync_playwright() as p:
        browser, context, page = create_activity_context(p, cookie_str)

        try:
            # 1. 访问活动页面
            print("\n  [1] 访问活动页面...")
            page.goto(ACTIVITY_URL, wait_until='domcontentloaded', timeout=60000)
            page.wait_for_timeout(5000)  # 等待页面加载

            # 首次运行保存调试信息
            if save_debug:
                save_debug_info(page, f"4th_{account_name}_initial")

            # 2. 发送祝福
            print("\n  [2] 发送祝福...")
            send_blessing(page)

            # 3. 执行抽奖
            print("\n  [3] 执行转盘抽奖...")
            lottery_count = do_lottery(page)

            # 保存最终状态
            if save_debug:
                save_debug_info(page, f"4th_{account_name}_final")

            print(f"\n  === 四周年活动完成 ===")
            print(f"  抽奖次数: {lottery_count}")

        except Exception as e:
            print(f"  [x] 活动执行异常: {e}")
            if save_debug:
                save_debug_info(page, f"4th_{account_name}_error")
        finally:
            browser.close()


def main():
    """主函数"""
    print("=== 四周年活动自动化 ===")
    print(f"活动地址: {ACTIVITY_URL}")
    print(f"活动时间: 2026.1.16 - 2026.1.22\n")

    cookies_list = get_all_cookies()
    if not cookies_list:
        print("错误: 请设置 ZAIMANHUA_COOKIE 环境变量")
        return

    print(f"检测到 {len(cookies_list)} 个账号")

    # 首次运行保存调试信息
    save_debug = True

    for account_name, cookie_str in cookies_list:
        print(f"\n{'='*50}")
        print(f"账号: {account_name}")
        print('='*50)

        run_4th_anniversary(cookie_str, account_name.replace(' ', '_'), save_debug)

        # 只在首个账号保存调试信息
        save_debug = False

        # 账号间隔
        if len(cookies_list) > 1:
            print("\n等待 3 秒后处理下一个账号...")
            time.sleep(3)

    print(f"\n{'='*50}")
    print("所有账号处理完成")
    print('='*50)


if __name__ == "__main__":
    main()
