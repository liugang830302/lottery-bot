import os
import requests
import google.generativeai as genai
from datetime import datetime, timedelta, timezone

# 读取保密配置
API_KEY = os.environ.get("GEMINI_API_KEY")
SC_KEY = os.environ.get("SERVERCHAN_KEY") # 改用 Server酱 Key

# 设置时区 (北京时间 UTC+8)
def get_beijing_time():
    utc_dt = datetime.now(timezone.utc)
    bj_dt = utc_dt + timedelta(hours=8)
    return bj_dt

# 判断今天跑什么彩种
def check_draw_day():
    today = get_beijing_time()
    weekday = today.weekday() + 1 # 1=周一, 7=周日
    
    # 周二(2)、周四(4)、周日(7) -> 双色球
    if weekday in [2, 4, 7]:
        return "双色球必中", "双色球"
    # 周一(1)、周三(3)、周六(6) -> 大乐透
    elif weekday in [1, 3, 6]:
        return "大乐透必中", "大乐透"
    else:
        return None, None

def send_to_serverchan(title, content):
    """发送到 Server酱"""
    if not SC_KEY:
        print("错误：未找到 SERVERCHAN_KEY")
        return
    
    url = f"https://sctapi.ftqq.com/{SC_KEY}.send"
    data = {
        "title": title,
        "desp": content # Server酱的内容字段叫 desp
    }
    try:
        response = requests.post(url, data=data)
        print(f">>> Server酱响应: {response.text}")
    except Exception as e:
        print(f"!!! 推送失败: {e}")

def run_task():
    print(">>> 开始执行自动分析任务 (Server酱版)...")
    
    command, lottery_name = check_draw_day()
    if not command:
        print("今天没有核心彩种开奖，任务结束。")
        return

    print(f">>> 识别到今日开奖：{lottery_name}")

    # 1. 调用 Gemini
    try:
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash') 
        
        prompt = f"""
        你现在是资深数据分析师。请执行指令：“{command}”。
        要求：
        1. 基于28模型混合智能策略。
        2. 严格按照 [单注 -> 双注 -> 五注 -> 复式] 的格式输出。
        3. 输出 Markdown 格式。
        4. 并在最后加上一句：“祝您今天好运！(报告生成时间：{get_beijing_time().strftime('%Y-%m-%d %H:%M')})”
        """
        
        print(">>> 正在请求 Google Gemini...")
        response = model.generate_content(prompt)
        content = response.text
        print(">>> AI 回复生成成功！")

        # 2. 推送微信 (Server酱)
        print(">>> 正在推送至微信...")
        send_to_serverchan(f"【{lottery_name}】早9点裁决报告", content)

    except Exception as e:
        print(f"!!! 发生错误: {e}")
        send_to_serverchan("任务执行失败", str(e))

if __name__ == "__main__":
    run_task()
