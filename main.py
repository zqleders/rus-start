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
        # 必须固定窗口大小，否则坐标点击会因为分辨率变化而失效
        browser = p.chromium.launch(headless=True)
        
        for acc in accounts:
            context = browser.new_context(viewport={"width": 1280, "height": 720})
            page = context.new_page()
            screenshot_path = f"action_{acc['user']}.png"
            
            try:
                # 1. 登录
                page.goto(login_url)
                page.fill('input[name="username"]', acc["user"])
                page.fill('input[name="password"]', acc["pass"])
                page.click('button[type="submit"]')
                page.wait_for_selector('p:has-text("Welcome back")', timeout=15000)
                
                # 2. 进入控制台并等待页面加载完全
                page.goto(acc["url"])
                page.wait_for_load_state("networkidle")
                page.wait_for_timeout(3000) # 给页面渲染留出余量
                
                # 3. 直接使用测试通过的坐标点击 (X, Y)
                # 请将下面的 x 和 y 替换为你确认正确的红点坐标值
                # 假设你红点对应的坐标是 x, y
                page.mouse.click(x=730, y=170) 
                
                # 4. 结果反馈
                page.wait_for_timeout(3000)
                page.screenshot(path=screenshot_path)
                send_tg_photo(screenshot_path, f"账号 {acc['user']} 已执行固定坐标点击")
                
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
