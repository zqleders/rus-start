import os
import json
import time
from playwright.sync_api import sync_playwright
import requests

# 记忆窗口位置逻辑保持不变
POS_FILE = "window_pos.json"
def save_pos(page):
    pos = page.evaluate("() => ({x: window.screenX, y: window.screenY})")
    with open(POS_FILE, "w") as f:
        json.dump(pos, f)

def send_tg(message):
    token = os.environ.get("TG_TOKEN")
    chat_id = os.environ.get("TG_CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, data={"chat_id": chat_id, "text": message})

def run():
    # 读取所有账号配置
    accounts = json.loads(os.environ.get("ACCOUNTS_JSON", "[]"))
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        for acc in accounts:
            try:
                context = browser.new_context()
                page = context.new_page()
                
                # 1. 登录
                page.goto("https://my.rustix.me/auth/login")
                page.fill('input[name="username"]', acc["user"])
                page.fill('input[name="password"]', acc["pass"])
                page.click('button[type="submit"]')
                
                # 等待导航完成
                page.wait_for_load_state("networkidle")
                
                # 2. 访问对应的 Console 页面
                page.goto(acc["url"])
                
                # 3. 点击 Start
                start_btn = page.locator('button:has-text("Start")')
                # 等待元素加载
                start_btn.wait_for(state="visible", timeout=10000)
                start_btn.click(force=True)
                
                send_tg(f"账号 {acc['user']} 操作成功")
                
            except Exception as e:
                send_tg(f"账号 {acc['user']} 操作失败: {str(e)}")
            finally:
                context.close()
        
        browser.close()

if __name__ == "__main__":
    run()
