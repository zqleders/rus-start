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
                page.goto(login_url)
                page.fill('input[name="username"]', acc["user"])
                page.fill('input[name="password"]', acc["pass"])
                page.click('button[type="submit"]')
                page.wait_for_selector('p:has-text("Welcome back")', timeout=15000)
                
                page.goto(acc["url"])
                page.wait_for_load_state("domcontentloaded")
                
                # 寻找按钮
                start_btn = page.locator("button:has-text('Start')").first
                
                # 检查按钮是否在页面上且是否处于启用状态
                if start_btn.is_visible() and not start_btn.get_attribute("disabled"):
                    start_btn.click(force=True)
                    # 只有点击了才截图反馈
                    page.wait_for_timeout(2000)
                    page.screenshot(path=screenshot_path)
                    send_tg_photo(screenshot_path, f"账号 {acc['user']} 已点击 Start")
                else:
                    # 如果按钮是 disabled 或者没找到，不报错，直接跳过
                    print(f"账号 {acc['user']} 的 Start 按钮当前不可用，跳过点击")
                
            except Exception as e:
                # 其它异常才报错
                page.screenshot(path=screenshot_path)
                send_tg_photo(screenshot_path, f"账号 {acc['user']} 发生意外: {str(e)[:50]}")
            
            finally:
                context.close()
                if os.path.exists(screenshot_path):
                    os.remove(screenshot_path)
        
        browser.close()

if __name__ == "__main__":
    run()
