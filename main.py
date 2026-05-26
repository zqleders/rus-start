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
    
    # 设定坐标
    CLICK_X = 1370
    CLICK_Y = 100
    
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
                
                # 2. 进入控制台
                page.goto(acc["url"])
                page.wait_for_load_state("domcontentloaded")
                
                # 3. 执行点击
                page.mouse.click(CLICK_X, CLICK_Y)
                
                # 4. 绘制红点（保留功能以便确认）
                page.evaluate(f"""() => {{
                    const marker = document.createElement('div');
                    marker.style.position = 'absolute';
                    marker.style.left = '{CLICK_X}px';
                    marker.style.top = '{CLICK_Y}px';
                    marker.style.width = '12px';
                    marker.style.height = '12px';
                    marker.style.backgroundColor = 'red';
                    marker.style.borderRadius = '50%';
                    marker.style.zIndex = '9999';
                    document.body.appendChild(marker);
                }}""")
                
                # 5. 截图反馈
                page.wait_for_timeout(2000)
                page.screenshot(path=screenshot_path)
                send_tg_photo(screenshot_path, f"账号 {acc['user']} 已执行点击并标注")
                
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
