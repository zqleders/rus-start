import os
import json
import requests
from playwright.sync_api import sync_playwright

def send_tg_photo(photo_path, caption):
    token = os.environ.get("TG_TOKEN")
    chat_id = os.environ.get("TG_CHAT_ID")
    if not token or not chat_id:
        return
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    with open(photo_path, 'rb') as f:
        requests.post(url, data={"chat_id": chat_id, "caption": caption}, files={"photo": f})

def run():
    accounts = json.loads(os.environ.get("ACCOUNTS_JSON", "[]"))
    login_url = os.environ.get("LOGIN_URL")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        for acc in accounts:
            context = browser.new_context(viewport={"width": 1920, "height": 1080})
            page = context.new_page()
            screenshot_path = f"action_{acc['user']}.png"
            
            try:
                # 1. 登录
                page.goto(login_url)
                page.fill('input[name="username"]', acc["user"])
                page.fill('input[name="password"]', acc["pass"])
                page.click('button[type="submit"]')
                page.wait_for_selector('p:has-text("Welcome back")', timeout=15000)
                
                # 2. 进入页面
                page.goto(acc["url"])
                page.wait_for_load_state("domcontentloaded")
                
                # --- 核心改进：更优的元素点击策略 ---
                # 使用 XPath 模糊匹配文本，且过滤掉已禁用状态
                # 这样即使类名变了，只要按钮叫 "Start" 就能找到
                start_btn_xpath = "//button[contains(normalize-space(), 'Start') and not(@disabled)]"
                
                # 显式等待按钮变得可点击
                page.wait_for_selector(start_btn_xpath, timeout=20000, state="attached")
                
                # 执行点击，并强制点击中心点
                btn = page.locator(start_btn_xpath).first
                btn.click(force=True, timeout=10000)
                
                # 3. 截图反馈
                page.wait_for_timeout(2000)
                page.screenshot(path=screenshot_path)
                send_tg_photo(screenshot_path, f"账号 {acc['user']} 已使用语义化定位点击成功")
                
            except Exception as e:
                page.screenshot(path=screenshot_path)
                send_tg_photo(screenshot_path, f"账号 {acc['user']} 失败: {str(e)[:50]}")
            
            finally:
                context.close()
                if os.path.exists(screenshot_path):
                    os.remove(screenshot_path)
        
        browser.close()

if __name__ == "__main__":
    run()
