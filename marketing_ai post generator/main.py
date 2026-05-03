from models import MarketerProfile, Campaign
from prompt_builder import build_prompt
from llm_client import generate_marketing_post


def main():
    marketer = MarketerProfile(
        experience_level="Junior",
        tone="Casual",
        platform="Facebook"
    )

    campaign = Campaign(
        product_name="كورس برمجة",
        goal="Sales",
        pain_point="شغل كتير ومفيش دخل ثابت",
        main_benefit="تتعلم مهارة مطلوبة وتزود دخلك",
        offer="خصم 30% لفترة محدودة",
        audience="شباب من 20 لـ 30 سنة"
    )

    prompt = build_prompt(marketer, campaign)
    post = generate_marketing_post(prompt)

    print("\n=== GENERATED MARKETING POST ===\n")
    print(post)


if __name__ == "__main__":
    main()
