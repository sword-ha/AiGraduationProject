from flask import Flask, render_template, request, jsonify
from models import MarketerProfile, Campaign
from prompt_builder import build_prompt
from llm_client import generate_marketing_post

app = Flask(__name__)

# إنشاء بيانات المسوق الافتراضية
marketer = MarketerProfile(experience_level="Junior", tone="Casual", platform="Web")
# الحملة الافتراضية
campaign = Campaign(
    product_name="كورسات برمجة",
    goal="Sales",
    pain_point="مفيش دخل ثابت وشغل صعب",
    main_benefit="تتعلم مهارة مطلوبة وتزود دخلك",
    offer="خصم 30% لفترة محدودة",
    audience="شباب من 20 لـ 30 سنة"
)

# حفظ تاريخ المحادثة
chat_history = []

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    global campaign, chat_history
    user_message = request.json.get("message")
    if not user_message:
        return jsonify({"reply": "ممكن تكتب حاجة الأول!"})

    # تعديل خصائص الحملة ديناميكي حسب كلام المستخدم
    if "خصم" in user_message:
        campaign.offer = user_message  # أي خصم جديد يكتبه المستخدم
    if "كوتشي" in user_message:
        campaign.product_name = "كوتشي اير فور"
    if "نتوورك" in user_message:
        campaign.product_name = "كورسات نيتوورك"

    # حفظ رسالة المستخدم
    chat_history.append({"role": "user", "content": user_message})

    prompt = build_prompt(marketer, campaign, user_message, chat_history)
    reply = generate_marketing_post(prompt)

    # حفظ رد البوت
    chat_history.append({"role": "assistant", "content": reply})

    return jsonify({"reply": reply})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
