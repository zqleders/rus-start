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
            context = browser.new_context()
            page = context.new_page()
            screenshot_path = f"screenshot_{acc['user']}.png"
            
            try:
                # 1. 使用全局 login_url 登录
                page.goto(login_url)
                page.fill('input[name="username"]', acc["user"])
                page.fill('input[name="password"]', acc["pass"])
                page.click('button[type="submit"]')
                
                # 2. 验证登录成功
                try:
                    page.wait_for_selector('p:has-text("Welcome back")', timeout=15000)
                except:
                    page.screenshot(path=screenshot_path)
                    send_tg_photo(screenshot_path, f"账号 {acc['user']} 登录失败：未检测到 'Welcome back'")
                    context.close()
                    continue

                # 3. 访问目标控制台页面
                page.goto(acc["url"])
                page.wait_for_load_state("networkidle")
                
                # 4. 点击 Start 按钮
                start_btn = page.locator('button:has-text("Start")').first
                start_btn.wait_for(state="visible", timeout=15000)
                start_btn.click(force=True)
                
                # 5. 截图反馈
                page.wait_for_timeout(2000)
                page.screenshot(path=screenshot_path)
                send_tg_photo(screenshot_path, f"账号 {acc['user']} 操作成功：已点击 Start")
                
            except Exception as e:
                page.screenshot(path=screenshot_path)
                send_tg_photo(screenshot_path, f"账号 {acc['user']} 运行异常: {str(e)[:100]}")
            
            finally:
                context.close()
                if os.path.exists(screenshot_path):
                    os.remove(screenshot_path)
        
        browser.close()

if __name__ == "__main__":
    run()
