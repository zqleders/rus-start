import os
import json
import requests
from playwright.sync_api import sync_playwright

def run():
    # ... 前面登录逻辑保持不变 ...
    
    # 核心点击逻辑
    try:
        # 使用你确认的 1370, 120 坐标进行强制分发事件
        page.evaluate(f"""() => {{
            // 找到元素并强行触发鼠标序列
            const btn = document.elementFromPoint(1370, 120);
            if (btn) {{
                ['mousedown', 'mouseup', 'click'].forEach(evt => 
                    btn.dispatchEvent(new MouseEvent(evt, {{bubbles: true, cancelable: true, view: window}}))
                );
            }}
        }}""")
        print("已分发强制点击事件")
    except Exception as e:
        print(f"点击失败: {e}")

    # ... 截图和其余逻辑保持不变 ...
