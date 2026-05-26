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
                # 1. 登录
                page.goto(login_url)
                page.fill('input[name="username"]', acc["user"])
                page.fill('input[name="password"]', acc["pass"])
                page.click('button[type="submit"]')
                
                # 2. 登录验证
                try:
                    page.wait_for_selector('p:has-text("Welcome back")', timeout=15000)
                except:
                    page.screenshot(path=screenshot_path)
                    send_tg_photo(screenshot_path, f"账号 {acc['user']} 登录失败：未检测到 'Welcome back'")
                    context.close()
                    continue

                # 3. 访问控制台
                page.goto(acc["url"])
                # 降低等待强度，防止因长连接导致的超时
                page.wait_for_load_state("domcontentloaded")
                
                # 4. 强制点击 Start 按钮
                # 使用直接定位并强制点击，跳过 visible 等状态检测，防止因样式导致的超时
                start_btn = page.locator('button:has-text("Start")').first
                
                # 增加点击的重试逻辑，确保在页面完全渲染前尝试点击
                for i in range(3):
                    try:
                        start_btn.click(force=True, timeout=5000)
                        break
                    except:
                        page.wait_for_timeout(2000)
                
                # 5. 最终状态截图
                page.wait_for_timeout(2000)
                page.screenshot(path=screenshot_path)
                send_tg_photo(screenshot_path, f"账号 {acc['user']} 操作完毕")
                
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
