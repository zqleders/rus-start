import os
import json
import requests
from playwright.sync_api import sync_playwright

def send_tg_msg(message):
    token = os.environ.get("TG_TOKEN")
    chat_id = os.environ.get("TG_CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, data={"chat_id": chat_id, "text": message})

def send_tg_photo(photo_path, caption):
    token = os.environ.get("TG_TOKEN")
    chat_id = os.environ.get("TG_CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    with open(photo_path, 'rb') as f:
        requests.post(url, data={"chat_id": chat_id, "caption": caption}, files={"photo": f})

def run():
    accounts = json.loads(os.environ.get("ACCOUNTS_JSON", "[]"))
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        for acc in accounts:
            context = browser.new_context()
            page = context.new_page()
            screenshot_path = f"screenshot_{acc['user']}.png"
            
            try:
                # 1. 登录
                page.goto("https://my.rustix.me/auth/login")
                page.fill('input[name="username"]', acc["user"])
                page.fill('input[name="password"]', acc["pass"])
                page.click('button[type="submit"]')
                page.wait_for_url("**/server/**", timeout=30000)
                
                # 2. 访问控制台
                page.goto(acc["url"])
                page.wait_for_load_state("networkidle")
                
                # 3. 点击 Start (使用更稳健的选择器)
                # 选择所有包含 "Start" 文本的 button，并强制点击第一个
                start_btn = page.locator('button:has-text("Start")').first
                start_btn.wait_for(state="visible", timeout=15000)
                start_btn.click(force=True)
                
                # 成功后截图并发送
                page.screenshot(path=screenshot_path)
                send_tg_photo(screenshot_path, f"账号 {acc['user']} 操作成功：已点击 Start")
                
            except Exception as e:
                # 失败后截图并发送
                page.screenshot(path=screenshot_path)
                send_tg_photo(screenshot_path, f"账号 {acc['user']} 操作失败: {str(e)[:100]}")
            
            finally:
                context.close()
                if os.path.exists(screenshot_path):
                    os.remove(screenshot_path) # 发送后删除本地图片
        
        browser.close()

if __name__ == "__main__":
    run()
