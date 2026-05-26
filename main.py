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
                
                # --- 调整核心逻辑：增加相对于按钮左上角的偏移量 ---
                # 设定偏移像素 (X=向右, Y=向下)，将红点移到按钮中心
                offset_x = 35 # 按钮约 70px 宽，这里设为中心点附近
                offset_y = 15 # 按钮约 30px 高，这里设为中心点附近

                # 在页面上绘制红点标记，应用了偏移量
                page.evaluate(f"""() => {{
                    const el = document.evaluate("{start_btn_xpath}", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                    if (el) {{
                        const rect = el.getBoundingClientRect();
                        const marker = document.createElement('div');
                        marker.style.position = 'absolute';
                        // 使用 rect.left + window.scrollX 加上偏移量调整
                        marker.style.left = (rect.left + window.scrollX + {offset_x}) + 'px';
                        // 使用 rect.top + window.scrollY 加上偏移量调整
                        marker.style.top = (rect.top + window.scrollY + {offset_y}) + 'px';
                        marker.style.width = '10px';  // 稍微减小标记尺寸，以便更精确地观察位置
                        marker.style.height = '10px';
                        marker.style.backgroundColor = 'red';
                        marker.style.borderRadius = '50%';
                        marker.style.zIndex = '9999';
                        document.body.appendChild(marker);
                    }}
                }}""")
                
                # 这里依然不要执行点击，等待你确认红点位置
                page.wait_for_timeout(2000)
                page.screenshot(path=screenshot_path)
                send_tg_photo(screenshot_path, f"账号 {acc['user']} 调试：红点位置调整尝试")
                
            except Exception as e:
                send_tg_photo(screenshot_path, f"账号 {acc['user']} 调试失败: {str(e)[:100]}")
            
            finally:
                context.close()
                if os.path.exists(screenshot_path):
                    os.remove(screenshot_path)
        
        browser.close()

if __name__ == "__main__":
    run()
