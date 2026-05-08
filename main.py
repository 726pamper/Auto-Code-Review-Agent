import os
import requests
from openai import OpenAI
from dotenv import load_dotenv
import prompts # 导入刚才写的提示词

# 加载环境变量
load_dotenv()

# 初始化大模型客户端
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL")
)

def ask_agent(system_prompt, user_content):
    """调用大模型的通用函数"""
    print(f"🧠 正在调用 Agent...")
    response = client.chat.completions.create(
        model="gpt-4o", # 替换为你实际使用的模型名称，如 deepseek-chat
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        temperature=0.3
    )
    return response.choices[0].message.content

def post_to_github(pr_number, comment_body):
    """将结果发布到 GitHub PR"""
    repo = os.getenv("GITHUB_REPO")
    token = os.getenv("GITHUB_TOKEN")
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.post(url, headers=headers, json={"body": comment_body})
    
    if response.status_code == 201:
        print(f"✅ 成功将 Review 报告推送到 GitHub PR #{pr_number}")
    else:
        print(f"❌ 推送失败: {response.text}")

def run_review_pipeline(pr_diff_text, pr_number):
    """执行三阶段 Agent 流水线"""
    print("🚀 启动自动化 Code Review 流水线...")
    
    # 阶段 1：规范审查
    print("\n--- [Stage 1] 规范审查专家 ---")
    step1_result = ask_agent(prompts.AGENT_1_PROMPT, f"这是 PR 的代码 Diff：\n{pr_diff_text}")
    print("✅ 规范审查完成")
    
    # 阶段 2：逻辑与安全审查
    print("\n--- [Stage 2] 逻辑与安全专家 ---")
    context_for_step2 = f"原始 Diff:\n{pr_diff_text}\n\n规范审查结果:\n{step1_result}"
    step2_result = ask_agent(prompts.AGENT_2_PROMPT, context_for_step2)
    print("✅ 逻辑与安全审查完成")
    
    # 阶段 3：代码重构工程师
    print("\n--- [Stage 3] 重构工程师 ---")
    context_for_step3 = f"原始 Diff:\n{pr_diff_text}\n\n前置审查报告:\n{step1_result}\n\n{step2_result}"
    final_review_report = ask_agent(prompts.AGENT_3_PROMPT, context_for_step3)
    print("✅ 最终报告与重构代码生成完成")
    
    # 执行：推送到 GitHub
    post_to_github(pr_number, final_review_report)

if __name__ == "__main__":
    # 测试用的模拟数据
    test_diff = """
    + @app.post("/predict_img")
    + def run_img(file: UploadFile):
    +    file_path = "/tmp/images/" + file.filename
    +    m = YOLO('yolov11n.pt') 
    +    res = m.predict(file_path)
    +    os.system(f"rm {file_path}") 
    +    return {"msg": "success", "boxes": str(res[0].boxes)}
    """
    # 替换为你 GitHub 仓库里的真实 PR 编号
    TARGET_PR_NUMBER = 1 
    
    run_review_pipeline(test_diff, TARGET_PR_NUMBER)