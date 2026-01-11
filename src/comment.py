"""每日评论自动化"""
import os
import time
import random
from playwright.sync_api import sync_playwright
from utils import get_all_cookies, create_browser_context, claim_rewards

# 配置
MAX_RETRIES = 3
COMMENTED_COMICS_FILE = "commented_comics.txt"

# 评论内容池 (通用型支持语句)
COMMENTS = [
    "好看！",
    "支持作者~",
    "期待更新！",
    "追了！",
    "不错不错",
    "继续加油！",
    "支持！",
    "加油！",
]


def get_commented_comics():
    """获取已评论的漫画ID列表"""
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(script_dir, COMMENTED_COMICS_FILE)
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return set(line.strip() for line in f if line.strip())
    except Exception as e:
        print(f"读取已评论记录失败: {e}")
    return set()


def save_commented_comic(comic_id):
    """保存已评论的漫画ID"""
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(script_dir, COMMENTED_COMICS_FILE)
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(comic_id + '\n')
    except Exception as e:
        print(f"保存评论记录失败: {e}")


def post_daily_comment(page):
    """发表每日评论"""
    print("\n=== 每日评论任务 ===")
    try:
        # 获取已评论的漫画
        commented_comics = get_commented_comics()
        print(f"已评论过 {len(commented_comics)} 部漫画")

        # 访问首页获取漫画链接
        print("访问首页获取漫画链接...")
        page.goto('https://www.zaimanhua.com/', wait_until='domcontentloaded')
        page.wait_for_timeout(3000)

        # 获取所有漫画详情链接
        comic_links = page.locator("a[href*='/info/']").all()
        print(f"首页共找到 {len(comic_links)} 个漫画链接")

        # 收集漫画信息并过滤已评论的
        available_comics = []
        for link in comic_links:
            try:
                href = link.get_attribute('href')
                if href:
                    # 提取漫画ID (格式: /info/12345/ 或 /info/comic-name.html)
                    comic_id = href.split('/info/')[-1].rstrip('/').replace('.html', '')
                    if comic_id and comic_id not in commented_comics:
                        full_url = href if href.startswith('http') else 'https://www.zaimanhua.com' + href
                        available_comics.append((comic_id, full_url))
            except:
                continue

        # 去重
        available_comics = list(set(available_comics))
        print(f"可选择的未评论漫画: {len(available_comics)} 部")

        if not available_comics:
            print("所有漫画都已评论过，尝试随机选择一部...")
            # 如果都评论过了，随机选一部（可能会重复）
            for link in comic_links:
                try:
                    href = link.get_attribute('href')
                    if href:
                        comic_id = href.split('/info/')[-1].rstrip('/').replace('.html', '')
                        full_url = href if href.startswith('http') else 'https://www.zaimanhua.com' + href
                        available_comics.append((comic_id, full_url))
                except:
                    continue
            available_comics = list(set(available_comics))

        if not available_comics:
            print("未找到任何漫画链接")
            return False

        # 随机选择一部漫画
        comic_id, comic_url = random.choice(available_comics)
        print(f"随机选择漫画: {comic_url} (ID: {comic_id})")

        # 访问漫画详情页
        page.goto(comic_url, wait_until='domcontentloaded')
        page.wait_for_timeout(3000)
        print(f"漫画页标题: {page.title()}")

        # 滚动到评论区
        page.evaluate("window.scrollTo(0, document.body.scrollHeight * 0.3)")
        page.wait_for_timeout(2000)

        # 查找评论输入框
        comment_input = page.query_selector("textarea.el-textarea__inner")
        if not comment_input:
            comment_input = page.query_selector("textarea[placeholder*='发表']")

        if comment_input:
            # 随机选择评论内容
            comment_text = random.choice(COMMENTS)
            print(f"输入评论: {comment_text}")
            comment_input.fill(comment_text)
            page.wait_for_timeout(1000)

            # 查找发布按钮 (使用正确的选择器)
            publish_btn = page.query_selector("a.SubmitBtn")
            if not publish_btn:
                publish_btn = page.query_selector(".new_pl_submit a")
            if not publish_btn:
                publish_btn = page.query_selector("a:has-text('发布')")

            if publish_btn:
                print("点击发布按钮...")
                publish_btn.click()
                page.wait_for_timeout(3000)
                print("评论发布成功！")
                # 记录已评论的漫画
                save_commented_comic(comic_id)
                return True
            else:
                print("未找到发布按钮")
                return False
        else:
            print("未找到评论输入框")
            return False

    except Exception as e:
        print(f"评论任务失败: {e}")
        return False


def run_comment(cookie_str):
    """执行评论任务"""
    with sync_playwright() as p:
        browser, context, page = create_browser_context(p, cookie_str)

        try:
            # 发表评论
            comment_result = post_daily_comment(page)

            # 领取积分
            claim_result = claim_rewards(page)

            return {
                'comment': comment_result,
                'claim': claim_result
            }

        except Exception as e:
            print(f"任务执行出错: {e}")
            return {'comment': False, 'claim': False}
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
        print(f"正在执行评论任务: {name}")
        print('='*50)

        for attempt in range(1, MAX_RETRIES + 1):
            print(f"\n尝试第 {attempt}/{MAX_RETRIES} 次...")
            try:
                results = run_comment(cookie_str)

                if results.get('comment') is False:
                    if attempt < MAX_RETRIES:
                        print(f"评论失败，等待重试...")
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
        print("所有账号评论任务完成！")
    else:
        print("部分任务失败，请检查日志")

    return all_success


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
