# coding: utf-8
# MBTI Personality Classifier with 40-question Quiz + Campaign Recommendation (Yes/No)

import pandas as pd
import numpy as np
import nltk
import string
from nltk.classify import NaiveBayesClassifier
from nltk.tokenize import wordpunct_tokenize
import tkinter as tk
from tkinter import messagebox

# =========================
# تحميل الموارد المطلوبة
# =========================
nltk.download('stopwords')

# =========================
# تحميل الداتا
# =========================
data_set = pd.read_csv("mbti_1.csv")
types = np.unique(np.array(data_set['type']))

# =========================
# تجميع كل البوستات حسب النوع
# =========================
all_posts = pd.DataFrame()
for t in types:
    posts = data_set[data_set['type'] == t]['posts']
    collected = []
    for p in posts:
        collected += p.split('|||')
    all_posts[t] = pd.Series(collected)

# =========================
# تجهيز Bag of Words
# =========================
useless_words = nltk.corpus.stopwords.words("english") + list(string.punctuation)
def build_bag_of_words_features_filtered(text):
    words = wordpunct_tokenize(text)
    return {word.lower(): 1 for word in words if word.lower() not in useless_words}

# =========================
# تجهيز Features لكل Type
# =========================
features = []
for t in types:
    posts = all_posts[t].dropna()
    features.append([(build_bag_of_words_features_filtered(p), t) for p in posts])

# =========================
# تقسيم Train / Test
# =========================
split = np.array([int(len(f) * 0.8) for f in features])
train = []
test = []
for i in range(16):
    train += features[i][:split[i]]
    test  += features[i][split[i]:]

# =========================
# موديلات منفصلة لكل Axis
# =========================
def train_axis(pos_letter, neg_letter, pos_label, neg_label):
    feats = []
    for t in types:
        posts = all_posts[t].dropna()
        if pos_letter in t:
            feats.append([(build_bag_of_words_features_filtered(p), pos_label) for p in posts])
        elif neg_letter in t:
            feats.append([(build_bag_of_words_features_filtered(p), neg_label) for p in posts])
    train_axis_data = []
    test_axis_data = []
    for i in range(16):
        train_axis_data += feats[i][:split[i]]
        test_axis_data  += feats[i][split[i]:]
    model = NaiveBayesClassifier.train(train_axis_data)
    return model

# تدريب الأربع محاور
IntroExtro = train_axis('I','E','I','E')
IntuitionSensing = train_axis('N','S','N','S')
ThinkingFeeling = train_axis('T','F','T','F')
JudgingPercieving = train_axis('J','P','J','P')

# =========================
# MBTI → Recommended Campaigns
# =========================
MBTI_to_campaign = {
    'INTJ': 'Tech Gadgets, Books, Online Courses',
    'ENTP': 'Startup Tools, Adventure Travel',
    'INFJ': 'Wellness Products, Mindfulness Apps',
    'ENFP': 'Lifestyle, Creative Tools',
    'ISTJ': 'Office Supplies, Professional Services',
    'ESTJ': 'Management Courses, Business Tools',
    'ISFJ': 'Home Essentials, Family Products',
    'ESFJ': 'Beauty, Fashion',
    'ISTP': 'Sports Equipment, DIY Tools',
    'ESTP': 'Outdoor Activities, Adventure Gear',
    'ISFP': 'Art Supplies, Music Instruments',
    'ESFP': 'Party Items, Fashion Accessories',
    'INFP': 'Books, Creative Apps',
    'ENFJ': 'Leadership Courses, Social Apps',
    'INTP': 'Tech Gadgets, Research Tools',
    'ENTJ': 'Business Tools, Productivity Software'
}

# =========================
# 40 سؤال مع Axis
# =========================
# Format: (Question text, Axis, OptionYes counts for first letter, OptionNo counts for second letter)
questions = [
    ("You enjoy social gatherings and meeting new people.", "I/E", "E", "I"),
    ("You prefer concrete facts over abstract ideas.", "N/S", "S", "N"),
    ("You make decisions based on logic rather than emotions.", "T/F", "T", "F"),
    ("You like to plan things in advance rather than go with the flow.", "J/P", "J", "P"),
    ("You feel energized after spending time with others.", "I/E", "E", "I"),
    ("You enjoy imagining possibilities rather than focusing on reality.", "N/S", "N", "S"),
    ("You value fairness over compassion.", "T/F", "T", "F"),
    ("You like having a structured schedule.", "J/P", "J", "P"),
    ("You prefer quiet time alone.", "I/E", "I", "E"),
    ("You trust facts more than theories.", "N/S", "S", "N"),
    ("You often rely on feelings when making decisions.", "T/F", "F", "T"),
    ("You enjoy being spontaneous.", "J/P", "P", "J"),
    ("You are outgoing and talkative.", "I/E", "E", "I"),
    ("You focus on ideas rather than details.", "N/S", "N", "S"),
    ("You prioritize logic in problem solving.", "T/F", "T", "F"),
    ("You prefer organization over flexibility.", "J/P", "J", "P"),
    ("You enjoy interacting with many people.", "I/E", "E", "I"),
    ("You are imaginative and creative.", "N/S", "N", "S"),
    ("You empathize with others easily.", "T/F", "F", "T"),
    ("You dislike strict schedules.", "J/P", "P", "J"),
    ("You like attending parties.", "I/E", "E", "I"),
    ("You focus on the big picture.", "N/S", "N", "S"),
    ("You make decisions rationally.", "T/F", "T", "F"),
    ("You prefer routines.", "J/P", "J", "P"),
    ("You enjoy group activities.", "I/E", "E", "I"),
    ("You enjoy abstract thinking.", "N/S", "N", "S"),
    ("You consider others' feelings in decisions.", "T/F", "F", "T"),
    ("You like to adapt and go with the flow.", "J/P", "P", "J"),
    ("You are talkative and energetic.", "I/E", "E", "I"),
    ("You rely on intuition.", "N/S", "N", "S"),
    ("You prioritize ethical concerns.", "T/F", "F", "T"),
    ("You prefer a planned lifestyle.", "J/P", "J", "P"),
    ("You enjoy being in social environments.", "I/E", "E", "I"),
    ("You focus on possibilities.", "N/S", "N", "S"),
    ("You are thoughtful and analytical.", "T/F", "T", "F"),
    ("You like to keep things organized.", "J/P", "J", "P"),
    ("You enjoy interacting with others.", "I/E", "E", "I"),
    ("You use your imagination often.", "N/S", "N", "S"),
    ("You consider emotions in decisions.", "T/F", "F", "T"),
    ("You prefer flexibility over strict planning.", "J/P", "P", "J"),
    ("You are sociable and talkative.", "I/E", "E", "I"),
    ("You think creatively.", "N/S", "N", "S"),
    ("You value logic in decisions.", "T/F", "T", "F"),
    ("You like structured routines.", "J/P", "J", "P")
]

# =========================
# تخزين الإجابات
# =========================
answers_count = {"I":0,"E":0,"N":0,"S":0,"T":0,"F":0,"J":0,"P":0}
current_question = 0

# =========================
# حساب MBTI
# =========================
def calculate_mbti():
    mbti = ""
    mbti += "I" if answers_count["I"] >= answers_count["E"] else "E"
    mbti += "N" if answers_count["N"] >= answers_count["S"] else "S"
    mbti += "T" if answers_count["T"] >= answers_count["F"] else "F"
    mbti += "J" if answers_count["J"] >= answers_count["P"] else "P"
    return mbti

# =========================
# السؤال التالي مع Yes/No
# =========================
def next_question(answer):
    global current_question
    q_text, axis, yes_count, no_count = questions[current_question]
    # اختيار Yes أو No
    if answer == "Yes":
        answers_count[yes_count] += 1
    else:
        answers_count[no_count] += 1

    current_question += 1

    if current_question >= len(questions):
        mbti_result = calculate_mbti()
        recommended_campaigns = MBTI_to_campaign.get(mbti_result,"General Campaigns")
        messagebox.showinfo("Result",
            f"Your MBTI: {mbti_result}\nRecommended Campaigns: {recommended_campaigns}")
        root.destroy()
    else:
        q_text, axis, yes_count, no_count = questions[current_question]
        question_label.config(text=f"Q{current_question+1}: {q_text}")
        buttonYes.config(command=lambda: next_question("Yes"))
        buttonNo.config(command=lambda: next_question("No"))

# =========================
# واجهة Tkinter
# =========================
root = tk.Tk()
root.title("MBTI Quiz & Affiliance Campaigns")
root.geometry("700x400")

tk.Label(root, text="Answer the 40-question quiz with Yes/No to get your MBTI and Campaigns:", font=("Arial",14)).pack(pady=10)

question_label = tk.Label(root, text="", wraplength=650, font=("Arial",14))
question_label.pack(pady=20)

buttonYes = tk.Button(root, text="Yes", width=20, height=2, bg="lightgreen", font=("Arial",12), command=lambda: next_question("Yes"))
buttonYes.pack(pady=5)

buttonNo = tk.Button(root, text="No", width=20, height=2, bg="orange", font=("Arial",12), command=lambda: next_question("No"))
buttonNo.pack(pady=5)

# عرض أول سؤال
q_text, axis, yes_count, no_count = questions[0]
question_label.config(text=f"Q1: {q_text}")

root.mainloop()
