import pandas as pd
import re
import json

file_path = r"C:\Users\Dell\Desktop\Basics_java\Admin Exam Questions - Full Sets.csv"
df = pd.read_csv(file_path)
df = df.iloc[1:]

questions = []

for _, row in df.iterrows():
    question_text = str(row["Unnamed: 1"]).strip()
    correct = [x.strip().upper() for x in str(row["Unnamed: 2"]).split(",") if x.strip()]

    parts = re.split(r"([A-E]\.\s)", question_text)
    if len(parts) > 1:
        question_body = parts[0].strip()
        options = {}
        for i in range(1, len(parts) - 1, 2):
            letter = parts[i].replace(".", "").strip()
            text = parts[i + 1].strip()
            options[letter] = text
    else:
        question_body = question_text
        options = {"A": "Нет вариантов"}

    questions.append({
        "question": question_body,
        "options": options,
        "answers": correct
    })

with open("quiz_questions.json", "w", encoding="utf-8") as f:
    json.dump(questions, f, ensure_ascii=False, indent=2)

print(f"✅ Загружено {len(questions)} вопросов.")
