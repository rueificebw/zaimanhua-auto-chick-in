"""每日阅读自动化"""
import time
import random
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from utils import get_all_cookies, create_browser_context, claim_rewards, init_localstorage

# 配置
MAX_RETRIES = 3
COMIC_WATCH_MINUTES = 12  # 观看时长（分钟）

# 无效内容关键词 - 需要在错误提示区域出现
INVALID_KEYWORDS = ['不存在', '已被删除', '找不到该漫画', '已下架']
# 付费/VIP 关键词
PAYWALL_KEYWORDS = ['付费', 'VIP专属', '开通会员', '购买章节', '解锁章节']


def safe_goto(page, url, timeout=30000, retries=2):
    """安全的页面导航，带重试"""
    for attempt in range(retries):
        try:
            page.goto(url, wait_until='domcontentloaded', timeout=timeout)
            return True
        except PlaywrightTimeout:
            if attempt < retries - 1:
                print(f"    页面加载超时，重试 {attempt + 2}/{retries}...")
                time.sleep(2)
            else:
                print(f"    页面加载失败: {url}")
                return False
        except Exception as e:
            print(f"    页面访问错误: {e}")
            return False
    return False


def check_page_valid(page):
    """检查页面是否有效（非404、未删除、非付费墙）"""
    try:
        page_text = page.inner_text('body')

        # 检查无效关键词
        for keyword in INVALID_KEYWORDS:
            if keyword in page_text:
                return False, 'invalid'

        # 检查付费墙
        for keyword in PAYWALL_KEYWORDS:
            if keyword in page_text:
                # 进一步确认是否是付费提示（可能是页面其他部分的文字）
                paywall_elements = page.query_selector_all("[class*='pay'], [class*='vip'], .lock")
                if paywall_elements:
                    return False, 'paywall'

        # 对于阅读页面，验证是否有漫画图片内容
        if '/view/' in page.url:
            # 检查是否有来自 zaimanhua 的图片（漫画内容）
            img_elements = page.query_selector_all("img[src*='zaimanhua.com']")
            if img_elements:
                return True, 'ok'
            # 也检查通用的阅读器容器
            reader_elements = page.query_selector_all("[class*='comic'], [class*='reader'], [class*='manga']")
            if reader_elements:
                return True, 'ok'
            # 如果页面文字量很少且没有图片，可能是空白页
            if len(page_text) < 200:
                return False, 'no_content'

        return True, 'ok'
    except Exception as e:
        print(f"    页面检查出错: {e}")
        return False, 'error'


def check_login_status(page, cookie_str):
    """检查登录状态是否有效"""
    try:
        # 设置 localStorage
        init_localstorage(page, cookie_str)

        # 检查是否有登录提示
        login_prompts = page.query_selector_all("[class*='login-btn'], [class*='to-login'], .login-tip")
        if login_prompts and len(login_prompts) > 0:
            # 可能未登录，尝试刷新并重新设置
            page.reload()
            time.sleep(2)
            init_localstorage(page, cookie_str)

        return True
    except Exception as e:
        print(f"登录状态检查出错: {e}")
        return False


def close_popups(page):
    """关闭可能的弹窗/广告"""
    try:
        # 常见的关闭按钮选择器
        close_selectors = [
            "[class*='close']",
            "[class*='Close']",
            ".modal-close",
            ".popup-close",
            "[aria-label='关闭']",
            "[aria-label='close']"
        ]
        for selector in close_selectors:
            close_btns = page.query_selector_all(selector)
            for btn in close_btns[:3]:  # 最多尝试3个
                try:
                    if btn.is_visible():
                        btn.click()
                        time.sleep(0.5)
                except:
                    pass
    except:
        pass


def get_current_page_number(page):
    """尝试获取当前页码"""
    try:
        # 常见的页码显示格式
        page_indicator = page.query_selector("[class*='page-num'], [class*='current-page'], .page-indicator")
        if page_indicator:
            text = page_indicator.inner_text()
            # 解析 "1/20" 或 "第1页" 格式
            import re
            match = re.search(r'(\d+)', text)
            if match:
                return int(match.group(1))
    except:
        pass
    return None


def watch_comic(page, cookie_str, minutes=12):
    """观看漫画指定时长"""
    print(f"\n=== 观看漫画任务 ({minutes}分钟) ===")
    try:
        # 访问首页获取漫画链接
        print("访问首页获取漫画链接...")
        if not safe_goto(page, 'https://www.zaimanhua.com/', timeout=45000):
            print("首页加载失败，尝试备用方案...")
            # 备用：直接访问推荐页
            if not safe_goto(page, 'https://www.zaimanhua.com/rank/', timeout=45000):
                print("备用页面也加载失败")
                return False

        page.wait_for_timeout(3000)

        # 检查并设置登录状态
        if not check_login_status(page, cookie_str):
            print("登录状态异常")
            return False

        # 关闭可能的弹窗
        close_popups(page)

        # 获取多个漫画链接备用 - 只从 www.zaimanhua.com 获取
        comic_links = page.locator("a[href*='/info/']").all()[:30]
        comic_urls = []
        for link in comic_links:
            try:
                href = link.get_attribute('href', timeout=5000)
                if href and '/info/' in href:
                    # 确保使用 www.zaimanhua.com 域名
                    if href.startswith('/'):
                        full_url = 'https://www.zaimanhua.com' + href
                    elif href.startswith('https://www.zaimanhua.com'):
                        full_url = href
                    elif href.startswith('https://manhua.zaimanhua.com'):
                        # 转换为 www 域名
                        full_url = href.replace('https://manhua.zaimanhua.com', 'https://www.zaimanhua.com')
                    else:
                        continue
                    if full_url not in comic_urls:
                        comic_urls.append(full_url)
            except:
                continue

        # 随机打乱顺序，避免总是读同一部漫画
        random.shuffle(comic_urls)
        print(f"备选漫画: {len(comic_urls)} 部")

        if not comic_urls:
            print("未找到漫画链接")
            return False

        total_seconds = minutes * 60
        elapsed_total = 0
        comics_read = 0
        pages_turned = 0
        chapters_turned = 0
        failed_comics = 0  # 记录连续失败次数

        print(f"开始模拟阅读 {minutes} 分钟...")

        # 遍历漫画直到找到有效的
        for comic_url in comic_urls:
            if elapsed_total >= total_seconds:
                break

            # 如果连续失败太多，跳出
            if failed_comics >= 10:
                print("连续失败次数过多，停止尝试")
                break

            print(f"\n尝试漫画: {comic_url}")

            # 访问漫画详情页
            if not safe_goto(page, comic_url, timeout=30000):
                failed_comics += 1
                continue
            page.wait_for_timeout(2000)

            # 重新设置 localStorage
            check_login_status(page, cookie_str)
            close_popups(page)

            # 检查页面是否有效
            is_valid, status = check_page_valid(page)
            if not is_valid:
                print(f"  漫画无效 ({status})，跳过...")
                failed_comics += 1
                continue

            # 找到章节列表并提取所有 URL（在导航前提取，避免 stale locator）
            chapter_links = page.locator("a[href*='/view/']").all()
            if not chapter_links:
                print("  未找到章节，跳过...")
                failed_comics += 1
                continue

            # 先提取所有章节 URL
            chapter_urls = []
            for chapter_link in chapter_links[:5]:
                try:
                    href = chapter_link.get_attribute('href', timeout=5000)
                    if href:
                        # 确保使用 www.zaimanhua.com 域名
                        if href.startswith('/'):
                            full_url = 'https://www.zaimanhua.com' + href
                        elif href.startswith('https://manhua.zaimanhua.com'):
                            full_url = href.replace('https://manhua.zaimanhua.com', 'https://www.zaimanhua.com')
                        elif href.startswith('https://www.zaimanhua.com'):
                            full_url = href
                        else:
                            continue
                        chapter_urls.append(full_url)
                except:
                    continue

            if not chapter_urls:
                print("  未能提取章节URL，跳过...")
                failed_comics += 1
                continue

            # 尝试每个章节直到找到有效的
            valid_chapter_found = False
            for i, chapter_url in enumerate(chapter_urls):
                try:
                    print(f"  尝试章节 {i+1}: {chapter_url}")
                    if not safe_goto(page, chapter_url, timeout=30000):
                        print("    章节加载失败")
                        continue
                    page.wait_for_timeout(3000)

                    # 重新设置 localStorage
                    check_login_status(page, cookie_str)
                    close_popups(page)

                    # 检查章节是否有效
                    is_valid, status = check_page_valid(page)
                    if not is_valid:
                        print(f"    章节无效 ({status})，尝试下一章...")
                        continue

                    valid_chapter_found = True
                    comics_read += 1
                    failed_comics = 0  # 重置失败计数
                    print(f"  [有效] 开始阅读漫画 {comics_read}")
                    break
                except PlaywrightTimeout:
                    print(f"    章节访问超时")
                    continue
                except Exception as e:
                    print(f"    章节访问失败: {e}")
                    continue

            if not valid_chapter_found:
                print("  该漫画无有效章节，跳过...")
                failed_comics += 1
                continue

            # 在当前漫画阅读一段时间
            time_per_comic = min(180, total_seconds - elapsed_total)  # 每部漫画最多3分钟
            last_page_num = get_current_page_number(page)
            stuck_count = 0  # 翻页卡住计数

            for t in range(0, time_per_comic, 10):
                if elapsed_total >= total_seconds:
                    break

                # 每30秒输出一次进度
                if elapsed_total % 30 == 0:
                    remaining = total_seconds - elapsed_total
                    print(f"  已阅读 {elapsed_total//60}分{elapsed_total%60}秒，剩余 {remaining//60}分{remaining%60}秒")

                # 关闭可能出现的弹窗
                close_popups(page)

                # 获取视口尺寸并翻页
                viewport = page.viewport_size
                click_x = int(viewport['width'] * 0.75)
                click_y = int(viewport['height'] * 0.5)

                # 每10秒翻一页
                page.mouse.click(click_x, click_y)
                pages_turned += 1
                page.wait_for_timeout(10000)
                elapsed_total += 10

                # 检查是否翻页成功
                current_page_num = get_current_page_number(page)
                if current_page_num is not None and last_page_num is not None:
                    if current_page_num == last_page_num:
                        stuck_count += 1
                        if stuck_count >= 3:
                            # 可能到达最后一页或卡住，尝试翻章节
                            print("  >> 翻页卡住，尝试跳转下一章...")
                            break
                    else:
                        stuck_count = 0
                        last_page_num = current_page_num

                # 每60秒尝试翻到下一章
                if elapsed_total % 60 == 0 and elapsed_total > 0:
                    next_chapter = page.query_selector("a:has-text('下一章'), .next-chapter, .btm_chapter_btn:has-text('下一'), [class*='next']")
                    if next_chapter:
                        try:
                            next_chapter.click()
                            page.wait_for_timeout(3000)
                            close_popups(page)

                            # 验证新章节有效
                            is_valid, status = check_page_valid(page)
                            if is_valid:
                                chapters_turned += 1
                                stuck_count = 0
                                last_page_num = get_current_page_number(page)
                                print(f"  >> 翻到下一章 (共{chapters_turned}章)")

                                # 重新设置 localStorage
                                check_login_status(page, cookie_str)
                            else:
                                print(f"  >> 下一章无效 ({status})，继续当前章节")
                        except Exception as e:
                            print(f"  >> 翻章失败: {e}")

        # 最后导航离开以触发阅读记录同步
        print("\n触发阅读记录同步...")
        safe_goto(page, 'https://www.zaimanhua.com/', timeout=30000)
        page.wait_for_timeout(2000)

        print(f"\n观看任务完成！已阅读 {elapsed_total//60}分钟，翻页 {pages_turned}，翻章 {chapters_turned}，漫画 {comics_read}部")
        return comics_read > 0

    except Exception as e:
        print(f"观看任务失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_watch(cookie_str, watch_minutes=None):
    """执行阅读任务"""
    if watch_minutes is None:
        watch_minutes = COMIC_WATCH_MINUTES

    with sync_playwright() as p:
        browser, context, page = create_browser_context(p, cookie_str)

        try:
            # 观看漫画 - 传入 cookie_str 用于设置 localStorage
            watch_result = watch_comic(page, cookie_str, watch_minutes)

            # 领取积分
            claim_result = claim_rewards(page)

            return {
                'watch': watch_result,
                'claim': claim_result
            }

        except Exception as e:
            print(f"任务执行出错: {e}")
            return {'watch': False, 'claim': False}
        finally:
            browser.close()


def main():
    """主函数，支持多账号"""
    cookies_list = get_all_cookies()

    if not cookies_list:
        print("Error: 未配置任何账号 Cookie")
        print("请设置 ZAIMANHUA_COOKIE 或 ZAIMANHUA_COOKIE_1 等环境变量")
        return False

    print(f"共发现 {len(cookies_list)} 个账号")

    all_success = True
    for name, cookie_str in cookies_list:
        print(f"\n{'='*50}")
        print(f"正在执行阅读任务: {name}")
        print('='*50)

        for attempt in range(1, MAX_RETRIES + 1):
            print(f"\n尝试第 {attempt}/{MAX_RETRIES} 次...")
            try:
                results = run_watch(cookie_str)

                if results.get('watch') is False:
                    if attempt < MAX_RETRIES:
                        print(f"阅读失败，等待重试...")
                        time.sleep(10)
                        continue
                    else:
                        all_success = False
                break

            except Exception as e:
                print(f"第 {attempt} 次尝试出错: {e}")
                if attempt < MAX_RETRIES:
                    time.sleep(10)
                else:
                    all_success = False

    print(f"\n{'='*50}")
    if all_success:
        print("所有账号阅读任务完成！")
    else:
        print("部分任务失败，请检查日志")

    return all_success


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
