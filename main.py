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
            screenshot_path = f"debug_marker_{acc['user']}.png"
            
            try:
                # 登录与访问逻辑保持不变
                page.goto(login_url)
                page.fill('input[name="username"]', acc["user"])
                page.fill('input[name="password"]', acc["pass"])
                page.click('button[type="submit"]')
                page.wait_for_selector('p:has-text("Welcome back")', timeout=15000)
                page.goto(acc["url"])
                page.wait_for_load_state("domcontentloaded")
                
                # 调试逻辑：定位 Start 按钮并标记红点
                start_btn_xpath = "//button[contains(normalize-space(), 'Start')]"
                page.wait_for_selector(start_btn_xpath, timeout=20000)
                
                # 在页面上绘制红点标记
                page.evaluate(f"""() => {{
                    const el = document.evaluate("{start_btn_xpath}", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                    if (el) {{
                        const marker = document.createElement('div');
                        marker.style.position = 'absolute';
                        marker.style.left = (el.getBoundingClientRect().left + window.scrollX) + 'px';
                        marker.style.top = (el.getBoundingClientRect().top + window.scrollY) + 'px';
                        marker.style.width = '20px';
                        marker.style.height = '20px';
                        marker.style.backgroundColor = 'red';
                        marker.style.borderRadius = '50%';
                        marker.style.zIndex = '9999';
                        document.body.appendChild(marker);
                    }}
                }}""")
                
                page.wait_for_timeout(2000)
                page.screenshot(path=screenshot_path)
                send_tg_photo(screenshot_path, f"账号 {acc['user']} 调试：红点已标注在检测到的元素位置")
                
            except Exception as e:
                send_tg_photo(screenshot_path, f"账号 {acc['user']} 调试失败: {str(e)[:100]}")
            
            finally:
                context.close()
                if os.path.exists(screenshot_path):
                    os.remove(screenshot_path)
        
        browser.close()

if __name__ == "__main__":
    run()
