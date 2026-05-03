import os
from services.cv_parser import extract_text_from_cv
from services.analysis_service import analyze_profile

def test_cv_analysis():
    # ضع هنا مسار PDF اختبار
    test_pdf = os.path.join(os.path.dirname(__file__), "sample_cv.pdf")
    
    try:
        cv_text = extract_text_from_cv(test_pdf)
        result = analyze_profile(cv_text)
        assert "score" in result
        assert "price_range" in result
        assert "allowed_campaigns" in result
        print("Test Passed!")
        print(result)
    except Exception as e:
        print("Test Failed!")
        print(str(e))

if __name__ == "__main__":
    test_cv_analysis()
