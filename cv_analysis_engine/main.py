from services.cv_parser import extract_text_from_cv
from services.analysis_service import analyze_profile

def main():
    file_path = input("Enter path to PDF CV: ").strip()
    
    try:
        cv_text = extract_text_from_cv(file_path)
        if not cv_text.strip():
            print("The PDF is empty or cannot be read.")
            return

        result = analyze_profile(cv_text)

        print("------ CV Analysis Result ------")
        print(f"Score: {result['score']}")
        print(f"Price Range: {result['price_range']}")
        print("Suggested Campaigns:")
        for c in result["allowed_campaigns"]:
            print(f"- {c}")

    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
