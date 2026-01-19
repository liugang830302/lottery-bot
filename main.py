import os
import requests
import google.generativeai as genai
from datetime import datetime, timedelta, timezone

# 读取保密配置
API_KEY = os.environ.get("GEMINI_API_KEY")
SC_KEY = os.environ.get("SERVERCHAN_KEY")

# 设置时区
def get_beijing_time():
    utc_dt = datetime.now(timezone.utc)
    bj_dt = utc_dt + timedelta(hours=8)
    return bj_dt

# 判断今天跑什么彩种
def check_draw_day():
    today = get_beijing_time()
    weekday = today.weekday() + 1 
    if weekday in [2, 4, 7]:
        return "双色球必中", "双色球"
    elif weekday in [1, 3, 6]:
        return "大乐透必中", "大乐透"
    else:
        return None, None

def send_to_serverchan(title, content):
    if not SC_KEY:
        print("错误：未找到 SERVERCHAN_KEY")
        return
    url = f"https://sctapi.ftqq.com/{SC_KEY}.send"
    data = {"title": title, "desp": content}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"!!! 推送失败: {e}")

# --- 核心：自动寻找可用模型 ---
def get_available_model():
    print(">>> 正在向 Google 询问可用模型列表...")
    try:
        # 遍历所有可用模型
        for m in genai.list_models():
            # 必须支持 generateContent 方法
            if 'generateContent' in m.supported_generation_methods:
                # 优先找 flash 模型 (速度快)，找不到就随便返回一个能用的
                if 'gemini' in m.name:
                    print(f">>> 找到可用模型: {m.name}")
                    return m.name
    except Exception as e:
        print(f"!!! 获取模型列表失败: {e}")
    
    # 如果实在找不到，回退到默认
    return 'models/gemini-1.5-flash'

def run_task():
    print(">>> 开始执行自动分析任务 (自动适配版)...")
    
    command, lottery_name = check_draw_day()
    if not command:
        print("今天无开奖，结束。")
        return

    try:
        genai.configure(api_key=API_KEY)
        
        # 1. 动态获取模型名
        model_name = get_available_model()
        model = genai.GenerativeModel(model_name)
        
        prompt = f"""
        你现在是资深数据分析师。请执行指令：“{command}”。
        要求：
        1. 基于28模型混合智能策略。
        2. 严格按照 [单注 -> 双注 -> 五注 -> 复式] 的格式输出。
        3. 输出 Markdown 格式。
        4. 并在最后加上一句：“祝您今天好运！(报告生成时间：{get_beijing_time().strftime('%Y-%m-%d %H:%M')})”
        """
        
        print(f">>> 正在使用 {model_name} 请求生成...")
        response = model.generate_content(prompt)
        content = response.text
        print(">>> AI 回复生成成功！")

        send_to_serverchan(f"【{lottery_name}】早9点裁决报告", content)

    except Exception as e:
        print(f"!!! 发生错误: {e}")
        send_to_serverchan("任务执行失败", f"错误日志: {str(e)}")

if __name__ == "__main__":
    run_task()
