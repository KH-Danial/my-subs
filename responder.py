import os, json, requests

GITHUB_TOKEN = os.environ["GH_TOKEN"]

# ۱. خواندن اطلاعات Issue
event_path = os.environ["GITHUB_EVENT_PATH"]
with open(event_path, "r", encoding="utf-8") as f:
    event = json.load(f)

issue_number = event["issue"]["number"]
title = event["issue"]["title"]
body = event["issue"]["body"] or ""
repo = os.environ["GITHUB_REPOSITORY"]

prompt = f"{title}\n\n{body}"

# ۲. هر ۸ مدل برای تست جامع
all_8_models = [
    # ۴ مدل اصلی قبلی
    {"id": "gpt-4o-mini", "role": "GPT-4o mini (OpenAI)"},
    {"id": "DeepSeek-R1", "role": "DeepSeek R1"},
    {"id": "cohere/cohere-command-r-08-2024", "role": "Cohere Command R"},
    {"id": "Mistral-small-2503", "role": "Mistral Small"},
    # ۴ مدل جدید پیشنهادی
    {"id": "meta/Llama-3.3-70B-Instruct", "role": "Llama 3.3 70B (Meta)"},
    {"id": "mistral-large", "role": "Mistral Large"},
    {"id": "phi-4", "role": "Phi-4 (Microsoft)"},
    {"id": "openai/gpt-4.1", "role": "GPT-4.1 (OpenAI)"}
]

forced_prompt = f"""⚠️ دستور: شما باید فقط به زبان فارسی پاسخ دهید. حق استفاده از هیچ زبان دیگری را ندارید.
اگر سوال کاربر حاوی متنی غیرفارسی است، آن را ترجمه کرده و پاسخ خود را کاملاً فارسی بنویسید.
به هیچ عنوان به «فارسی نبودن» یا «توانایی زبان» اشاره نکنید. مستقیماً پاسخ دهید.

سوال کاربر:
{prompt}"""

answers = []

for model in all_8_models:
    try:
        response = requests.post(
            "https://models.github.ai/inference/chat/completions",
            headers={
                "Authorization": f"Bearer {GITHUB_TOKEN}",
                "Content-Type": "application/json"
            },
            json={
                "model": model["id"],
                "messages": [{"role": "user", "content": forced_prompt}],
                "max_tokens": 400
            },
            timeout=45
        )
        if response.status_code == 200:
            answer = response.json()["choices"][0]["message"]["content"]
            answers.append(f"## ✅ {model['id']}\n*{model['role']}*\n\n{answer}\n")
        else:
            answers.append(f"## ❌ {model['id']}\n*{model['role']}*\nخطا {response.status_code}: {response.text[:200]}\n")
    except Exception as e:
        answers.append(f"## ❌ {model['id']}\n*{model['role']}*\nاستثنا: {str(e)[:200]}\n")

# ۳. ارسال نتایج
comparison_body = "## 🏛️ تست جامع ۸ مدل\n\n"
comparison_body += f"**سوال:** {prompt}\n\n---\n\n"
comparison_body += "\n---\n".join(answers)
comparison_body += "\n\n---\n## 📊 خلاصه\n"
success_count = sum(1 for a in answers if a.startswith("## ✅"))
comparison_body += f"موفق: {success_count} از ۸"

comment_url = f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments"
post = requests.post(
    comment_url,
    headers={
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    },
    json={"body": comparison_body}
)

if post.status_code == 201:
    print("✅ نتایج تست ۸ مدل ثبت شد.")
else:
    print(f"❌ خطا: {post.status_code} {post.text[:200]}")