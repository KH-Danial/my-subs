import os, json, requests, re

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

# ------------------------------------------------------------
# ۲. تعریف مدل‌های عمومی (Low-Tier) – همیشه فعال
# ------------------------------------------------------------
general_models = [
    {
        "id": "gpt-4o-mini",
        "role": "دستیار عمومی، برنامه‌نویسی و تحلیل فنی"
    },
    {
        "id": "DeepSeek-R1",
        "role": "تحلیل منطقی، ریاضی و امنیت سایبری"
    },
    {
        "id": "cohere/cohere-command-r-08-2024",
        "role": "نویسندگی خلاق، تولید محتوا و ایده‌پردازی"
    },
    {
        "id": "Mistral-small-2503",
        "role": "تحلیل مفهومی، فلسفه و دیدگاه‌های کلان"
    }
]

# ------------------------------------------------------------
# ۳. تعریف مدل‌های تخصصی (High-Tier) – فقط در حوزه مربوطه فراخوانی می‌شوند
# ------------------------------------------------------------
specialist_models = [
    {
        "id": "openai/gpt-4.1",
        "system": "شما یک تحلیلگر مالی، کارشناس برنامه‌نویسی و متخصص سئو هستید. پاسخ‌های دقیق، فنی و عملیاتی ارائه دهید.",
        "keywords": [
            "تحلیل مالی", "فارکس", "ارز دیجیتال", "سئو", "برنامه‌نویسی",
            "کد", "توسعه وب", "طراحی سایت", "صرافی", "قیمت", "نمودار"
        ]
    },
    {
        "id": "anthropic/claude-3.5-sonnet",
        "system": "شما استاد مقاله‌نویسی آکادمیک، تحلیل فنی عمیق و برنامه‌نویسی هستید. پاسخ‌های ساختاریافته، دقیق و مستند ارائه دهید.",
        "keywords": [
            "مقاله", "تحقیق", "آکادمیک", "کد", "برنامه‌نویسی",
            "تحلیل فنی", "برنامه", "سیستم", "معماری", "پایان‌نامه"
        ]
    },
    {
        "id": "google/gemini-2.5-pro",
        "system": "شما یک محقق خبره، جستجوگر حرفه‌ای و تولیدکننده محتوای خلاق هستید. پاسخ‌های جامع، به‌روز و خوش‌ساخت ارائه دهید.",
        "keywords": [
            "جستجو", "اخبار", "داده", "شبکه‌های اجتماعی",
            "پست اینستاگرام", "تولید محتوا", "خلاق", "بازاریابی", "تحقیق"
        ]
    }
]

# ------------------------------------------------------------
# ۴. ساخت پیام پایه برای مدل‌ها (اجباری فارسی و بدون بهانه)
# ------------------------------------------------------------
def build_user_message(question, model_role="دستیار هوش مصنوعی"):
    return f"""⚠️ دستور: شما فقط باید به زبان فارسی پاسخ دهید. حق استفاده از هیچ زبان دیگری را ندارید.
نقش شما: {model_role}
اگر سوال کاربر حاوی متنی غیرفارسی است، آن را ترجمه کرده و پاسخ خود را کاملاً فارسی بنویسید.
هرگز به «فارسی نبودن» یا «محدودیت زبان» اشاره نکنید. مستقیم پاسخ دهید.

سوال کاربر:
{question}"""

# ------------------------------------------------------------
# ۵. جمع‌آوری پاسخ‌ها
# ------------------------------------------------------------
answers = []

# (الف) مدل‌های عمومی را همیشه فراخوانی کن
for model in general_models:
    response = requests.post(
        "https://models.github.ai/inference/chat/completions",
        headers={
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Content-Type": "application/json"
        },
        json={
            "model": model["id"],
            "messages": [
                {"role": "user", "content": build_user_message(prompt, model["role"])}
            ],
            "max_tokens": 600
        }
    )
    if response.status_code == 200:
        answer = response.json()["choices"][0]["message"]["content"]
        answers.append(f"**{model['id']}** ({model['role']}):\n{answer}\n")
    else:
        answers.append(f"**{model['id']}** (خطا {response.status_code})")

# (ب) مدل‌های تخصصی را فقط در صورت مرتبط بودن حوزه اضافه کن
combined_text = title + " " + body
for spec in specialist_models:
    # چک کن حداقل یکی از کلمات کلیدی در متن وجود داشته باشد
    if any(keyword in combined_text for keyword in spec["keywords"]):
        response = requests.post(
            "https://models.github.ai/inference/chat/completions",
            headers={
                "Authorization": f"Bearer {GITHUB_TOKEN}",
                "Content-Type": "application/json"
            },
            json={
                "model": spec["id"],
                "messages": [
                    {"role": "system", "content": spec["system"]},
                    {"role": "user", "content": build_user_message(prompt, "متخصص سطح بالا")}
                ],
                "max_tokens": 700
            }
        )
        if response.status_code == 200:
            answer = response.json()["choices"][0]["message"]["content"]
            answers.append(f"**🔹 {spec['id']}** (متخصص ویژه):\n{answer}\n")
        else:
            answers.append(f"**🔹 {spec['id']}** (خطا {response.status_code})")

# ------------------------------------------------------------
# ۶. مدل قاضی – جمع‌بندی نهایی
# ------------------------------------------------------------
judge_prompt = f"سوال کاربر: {prompt}\n\nپاسخ‌های متخصصان:\n" + "\n".join(answers) + "\n\nبا توجه به پاسخ‌های بالا، یک پاسخ نهایی جامع و دقیق به فارسی بنویس. اگر پاسخ‌ها متناقض بودند، بهترین نظر را انتخاب کن."

judge_response = requests.post(
    "https://models.github.ai/inference/chat/completions",
    headers={
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Content-Type": "application/json"
    },
    json={
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": judge_prompt}],
        "max_tokens": 800
    }
)

if judge_response.status_code == 200:
    final_answer = judge_response.json()["choices"][0]["message"]["content"]
else:
    final_answer = f"⚠️ خطا در جمع‌بندی نهایی: {judge_response.status_code}"

# ------------------------------------------------------------
# ۷. ارسال کامنت نهایی
# ------------------------------------------------------------
comment_parts = [
    "## 🏛️ هیئت منصفه هوش مصنوعی\n",
    "### 👥 متخصصان دائمی (عمومی):\n",
    *(f"- {m['id']} ({m['role']})\n" for m in general_models),
    "\n### 📣 پاسخ‌ها:\n",
    "\n---\n".join(answers),
    f"\n---\n### ⚖️ پاسخ نهایی (قاضی - GPT-4o mini):\n{final_answer}"
]

comment_body = "".join(comment_parts)

comment_url = f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments"
post = requests.post(
    comment_url,
    headers={
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    },
    json={"body": comment_body}
)

if post.status_code == 201:
    print("✅ کامنت ثبت شد.")
else:
    print(f"❌ خطا: {post.status_code} {post.text[:200]}")