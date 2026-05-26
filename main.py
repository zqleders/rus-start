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
            screenshot_path = f"final_click_{acc['user']}.png"
            
            try:
                # 1. 登录与访问
                page.goto(login_url)
                page.fill('input[name="username"]', acc["user"])
                page.fill('input[name="password"]', acc["pass"])
                page.click('button[type="submit"]')
                page.wait_for_selector('p:has-text("Welcome back")', timeout=15000)
                page.goto(acc["url"])
                page.wait_for_load_state("domcontentloaded")
                
                # 2. 定位按钮并执行偏移坐标点击
                # 依然使用 XPath 找到元素，但目的是获取它的原始位置，不执行 XPath 点击
                start_btn = page.locator("//button[contains(normalize-space(), 'Start')]").first
                box = start_btn.bounding_box()
                
                if box:
                    # 设定偏移量：往右多一点，往下一点
                    # 你可以根据上次红点偏离的程度继续修改这些数值
                    offset_x = 15  # 向右增加像素
                    offset_y = 10  # 向下增加像素
                    
                    target_x = box['x'] + (box['width'] / 2) + offset_x
                    target_y = box['y'] + (box['height'] / 2) + offset_y
                    
                    # 执行精确坐标点击
                    page.mouse.click(target_x, target_y)
                else:
                    raise Exception("未能定位到按钮框体")
                
                # 3. 截图反馈
                page.wait_for_timeout(2000)
                page.screenshot(path=screenshot_path)
                send_tg_photo(screenshot_path, f"账号 {acc['user']} 已执行偏移后的坐标点击")
                
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
