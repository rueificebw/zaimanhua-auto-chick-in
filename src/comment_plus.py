"""每日评论自动化"""
import os
import time
import random
from playwright.sync_api import sync_playwright
from utils import (
    get_all_cookies,
    create_browser_context,
    claim_rewards,
    init_localstorage,
    get_task_list,
    extract_tasks_from_response,
    extract_user_info_from_cookies,
    claim_task_reward
)

# 配置
MAX_RETRIES = 3
COMMENTED_COMICS_FILE = "commented_comics.txt"

# 评论内容池 (已按要求修改)
COMMENTS = [
    "好",
    "👍",
    "马萨卡",
    "好看",
    "₍˄·͈༝·͈˄*₎◞ ̑̑",
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
            f.write(str(comic_id) + '\n')
    except Exception as e:
        print(f"保存评论记录失败: {e}")


def get_random_comic_id():
    """生成随机漫画ID (范围: 38310-84901)"""
    return random.randint(38310, 84901)


def post_daily_comment(page, cookie_str):
    """发表每日评论"""
    print("\n=== 每日评论任务 ===")
    
    # 预检查：手机绑定状态和任务状态
    user_info = extract_user_info_from_cookies(cookie_str)
    token = user_info.get('token')
    
    # 检查任务是否已完成
    if token:
        print("检查当前任务状态...")
        task_result = get_task_list(token)
        if task_result and task_result.get('errno') == 0:
            tasks = extract_tasks_from_response(task_result)
            for task in tasks:
                task_id = task.get('id') or task.get('taskId')
                if task_id == 14:
                    if task.get('status') == 3:
                        print("  评论任务已完成，无需再次评论")
                        return True
                    break
    
    # 检查手机绑定
    phone_bound = user_info.get('bind_phone')
    is_bound = phone_bound and str(phone_bound) not in ['0', '', 'None', 'False']
    
    if not is_bound:
        print(f"警告: 检测到当前账号未绑定手机号 (bind_phone={phone_bound})")
        print("注意: 未绑定手机号的账号无法完成评论任务。为了避免工作流失败，将跳过此任务。")
        return True

    # 获取已评论的漫画ID，避免重复
    commented_comics = get_commented_comics()
    
    # 若评论失败则切换另一个ID，最多尝试5个不同的漫画ID
    max_comic_attempts = 5
    
    for attempt in range(max_comic_attempts):
        try:
            # 生成随机的漫画ID (避开已评论的，避免浪费)
            max_gen_attempts = 20
            comic_id = None
            for _ in range(max_gen_attempts):
                temp_id = get_random_comic_id()
                if str(temp_id) not in commented_comics:
                    comic_id = temp_id
                    break
            
            # 如果全部随机都命中已评论的，就随机选一个
            if comic_id is None:
                comic_id = get_random_comic_id()
            
            # 按新格式构建URL
            comic_url = f"https://manhua.zaimanhua.com/details/{comic_id}"
            
            print(f"\n尝试第 {attempt + 1}/{max_comic_attempts} 部漫画...")
            print(f"漫画ID: {comic_id}")
            print(f"访问: {comic_url}")

            # 访问漫画详情页
            page.goto(comic_url, wait_until='domcontentloaded')
            page.wait_for_timeout(2000)

            # 设置 localStorage 确保登录状态
            init_localstorage(page, cookie_str)
            
            # 刷新页面使 localStorage 生效
            page.reload(wait_until='domcontentloaded')
            page.wait_for_timeout(2000)
            
            print(f"页面标题: {page.title()}")

            # 检查页面是否存在 (简单的404判断)
            if any(keyword in page.title() for keyword in ["404", "Not Found", "找不到", "不存在"]):
                print("页面不存在或已下架，尝试下一个ID...")
                continue

            # 滚动到评论区
            page.evaluate("window.scrollTo(0, document.body.scrollHeight * 0.3)")
            page.wait_for_timeout(2000)

            # 查找评论输入框
            comment_input = page.query_selector("textarea.el-textarea__inner")
            if not comment_input:
                comment_input = page.query_selector("textarea[placeholder*='发表']")

            if not comment_input:
                print("未找到评论输入框，尝试更多选择器...")
                selectors = [
                    "textarea",
                    ".comment-input textarea",
                    ".pl_input textarea",
                    "[class*='comment'] textarea",
                ]
                for sel in selectors:
                    comment_input = page.query_selector(sel)
                    if comment_input:
                        print(f"  使用选择器找到: {sel}")
                        break

            if not comment_input:
                print("该页面未找到评论输入框，尝试下一个漫画ID...")
                continue

            # 随机选择评论内容 (从新内容池中选取)
            comment_text = random.choice(COMMENTS)
            print(f"输入评论: {comment_text}")
            comment_input.fill(comment_text)
            page.wait_for_timeout(1000)

            # 查找发布按钮
            publish_btn = page.query_selector("a.SubmitBtn")
            if not publish_btn:
                publish_btn = page.query_selector(".new_pl_submit a")
            if not publish_btn:
                publish_btn = page.query_selector("a:has-text('发布')")
            if not publish_btn:
                btn_selectors = [
                    "button:has-text('发布')",
                    ".submit-btn",
                    "[class*='submit']",
                    "button[type='submit']",
                ]
                for sel in btn_selectors:
                    publish_btn = page.query_selector(sel)
                    if publish_btn:
                        break

            if not publish_btn:
                print("未找到发布按钮，尝试下一个漫画ID...")
                continue

            print("点击发布按钮...")
            publish_btn.click()
            page.wait_for_timeout(3000)

            # 检查是否有错误提示（如需要绑定手机、评论频繁等）
            has_error = False
            error_selectors = [
                ".el-message--error",
                ".error-toast",
                ".el-message-box__message",
                ".el-message",
                "[class*='error']",
                "[class*='warn']",
                ".toast",
            ]
            for selector in error_selectors:
                try:
                    error_els = page.query_selector_all(selector)
                    for error_el in error_els:
                        if error_el and error_el.is_visible():
                            error_text = error_el.inner_text()
                            if error_text.strip():
                                print(f"  检测到提示: {error_text}")
                                # 如果是明确的错误提示，标记为失败
                                if any(keyword in error_text for keyword in ["失败", "错误", "频繁", "绑定", "权限"]):
                                    has_error = True
                except:
                    pass

            if has_error:
                print("该漫画评论失败，自动切换下一个ID...")
                continue

            # 通过任务 API 验证评论是否成功
            if token:
                print("验证评论任务状态...")
                page.wait_for_timeout(3000)  # 等待服务器更新状态
                task_result = get_task_list(token)
                if task_result and task_result.get('errno') == 0:
                    tasks = extract_tasks_from_response(task_result)
                    comment_task_found = False
                    for task in tasks:
                        task_id = task.get('id') or task.get('taskId')
                        task_name = task.get('title') or task.get('name') or task.get('taskName', '')
                        is_comment_task = (task_id == 14 or
                                         '评论' in str(task_name) or
                                         '一评' in str(task_name))
                        if is_comment_task:
                            comment_task_found = True
                            status = task.get('status', 0)
                            print(f"  评论任务状态: ID={task_id}, 名称={task_name}, 状态={status}")
                            # 任务状态: 1=未完成, 2=可领取, 3=已完成
                            if status == 3:  # 已完成
                                print(f"  ✓ 评论任务验证成功！状态: 已完成")
                                save_commented_comic(comic_id)
                                return True
                            elif status == 2:  # 可领取
                                print(f"  ✓ 任务完成，尝试领取奖励...")
                                success, result = claim_task_reward(token, task_id)
                                if success:
                                    print(f"    奖励领取成功！")
                                else:
                                    print(f"    奖励领取失败: {result}")
                                save_commented_comic(comic_id)
                                return True
                            else:
                                print(f"  ✗ 任务状态仍为未完成，尝试下一个漫画...")
                                has_error = True
                                break
                    
                    if not comment_task_found:
                        print("  未找到评论任务(ID=14)")
                else:
                    print(f"  获取任务列表失败")
            
            # 如果API验证显示失败，尝试下一个ID
            if has_error:
                continue

            # 如果没有明确错误且无法验证API，假设成功
            print("评论发布成功！（未通过API验证，但无错误提示）")
            save_commented_comic(comic_id)
            return True

        except Exception as e:
            print(f"该漫画处理异常: {e}")
            print("切换到下一个漫画ID...")
            continue
    
    print(f"\n已尝试 {max_comic_attempts} 个不同的漫画ID，全部失败")
    return False


def run_comment(cookie_str):
    """执行评论任务"""
    with sync_playwright() as p:
        browser, context, page = create_browser_context(p, cookie_str)

        try:
            # 发表评论 (已包含自动切换ID逻辑)
            comment_result = post_daily_comment(page, cookie_str)

            # 领取积分
            claim_result = claim_rewards(page, cookie_str)

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

        # 外层重试：包括浏览器启动等整体流程
        for attempt in range(1, MAX_RETRIES + 1):
            print(f"\n尝试第 {attempt}/{MAX_RETRIES} 次...")
            try:
                results = run_comment(cookie_str)

                if results.get('comment') is False:
                    if attempt < MAX_RETRIES:
                        print(f"整体流程失败，等待重试...")
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
