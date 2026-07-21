# 🏥 MedEase — AI-Powered Healthcare Assistant for India

> Helping every Indian family understand their medical documents in plain language.

🌐 **Live:** [http://medez.duckdns.org/]

---

## What it does

| Feature | Description |
|---------|-------------|
| 📄 Discharge Summary Translator | Upload hospital discharge PDF → plain language explanation with Hindi terms |
| 💊 Medicine Substitute Finder | Find verified cheaper generics from Jan Aushadhi database with price comparison |
| 🔬 Medical Report Explainer | Upload any report (blood, X-ray, MRI, ECG) → AI explains every finding |
| 🩺 Symptom to Specialist | Describe symptoms → get specialist recommendation + nearby doctors on map |
| 🗂️ Medical Records Storage | Save your reports securely on AWS S3 |

---

## Tech Stack

`Python` `Flask` `MySQL` `Google Gemini API` `PyMuPDF` `JavaScript` `HTML5/CSS3` `AWS EC2` `AWS S3` `OpenStreetMap`

---

## Safety

AI is used for explanation only — never diagnosis. Critical value flagging uses hard-coded ICMR thresholds, not AI. All PDFs are deleted immediately after processing (DPDP Act 2023 compliant).

> ⚠️ Not medical advice. Always consult a qualified doctor. Emergency: **112**

---

## Run Locally

```bash
git clone https://github.com/Anjali5726/MedEase.git
cd MedEase
pip install -r requirements.txt
mysql -u root -p < database/setup.sql
cp .env.example .env   # add your Gemini API key + DB password
python app.py
```

---

*This project is for portfolio purposes. Please contact me before reusing any part of this project.*

