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
                # 1. 登录逻辑 (保持不变)
                page.goto(login_url)
                page.fill('input[name="username"]', acc["user"])
                page.fill('input[name="password"]', acc["pass"])
                page.click('button[type="submit"]')
                page.wait_for_selector('p:has-text("Welcome back")', timeout=15000)
                
                # 2. 进入控制台 (保持不变)
                page.goto(acc["url"])
                page.wait_for_load_state("domcontentloaded")
                
                # 3. 精准屏蔽：只包裹点击逻辑
                try:
                    # 尝试定位并点击，如果按钮没加载好或者不可点，这个 try-except 会默默处理
                    page.locator("button:has-text('Start')").first.click(force=True, timeout=5000)
                except:
                    # 这里什么都不写，报错了也不会打印到控制台，也不会影响后面代码运行
                    pass
                
                # 4. 截图反馈 (保持不变)
                page.wait_for_timeout(2000)
                page.screenshot(path=screenshot_path)
                send_tg_photo(screenshot_path, f"账号 {acc['user']} 操作完成")
                
            except Exception as e:
                # 只有登录失败、无法进入网页等严重错误才会触发这里的截图报警
                page.screenshot(path=screenshot_path)
                send_tg_photo(screenshot_path, f"账号 {acc['user']} 发生关键错误: {str(e)[:50]}")
            
            finally:
                context.close()
                if os.path.exists(screenshot_path):
                    os.remove(screenshot_path)
        
        browser.close()

if __name__ == "__main__":
    run()
