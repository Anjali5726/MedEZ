# MedEase 🩺 — Plain-Language Medical Assistant

MedEase is a patient-centric web application designed to translate complex medical paperwork and report details into simple, plain language. Built with Indian families in mind, it helps patients understand discharge summaries, decode laboratory test biomarkers, check symptoms to find the right medical specialist, and find affordable generic medicine alternatives.

---

## 🚀 Key Features

* **📄 Discharge Summary Translator:** Upload hospital discharge PDFs to get a cohesive, plain-language breakdown of diagnoses, surgeries, and care steps, with key medical terms translated into Hindi in parentheses.
* **🔬 Lab Report Explainer:** Upload blood tests or panel reports to understand reference ranges and biomarker values, flagged dynamically by clinical severity.
* **🩺 Symptom to Specialist Mapper:** Describe symptoms in simple words to find out which medical specialist is needed and locate clinics or hospitals nearby using interactive Leaflet maps.
* **💊 Medicine Substitute Finder:** Find cheaper generic equivalents of branded medications, cross-referenced with official Jan Aushadhi database data to save healthcare costs.
* **📁 Personal Medical Records:** Securely store and organize your clinical explanations and report summaries in custom folders.

---

## 🛠️ Tech Stack

* **Backend:** Python, Flask
* **Database:** MySQL (for users, folders, and reports data)
* **AI Engine:** Google Gemini API (for clinical translation and triaging)
* **Frontend:** Responsive HTML5, Premium CSS3, Javascript
* **Maps API:** Leaflet.js, OpenStreetMap / Nominatim (for local doctor searches)

---

## 💻 Local Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone <your-repository-url>
   cd MebEZ
   ```

2. **Configure environment variables:**
   Create a `.env` file in the root directory and add the following keys:
   ```env
   GEMINI_KEY=your_gemini_api_key_here
   DB_PASSWORD=your_mysql_root_password
   DB_HOST=localhost
   ```

3. **Initialize the MySQL database:**
   ```bash
   mysql -u root -p < database/setup.sql
   ```

4. **Run the Flask application:**
   ```bash
   python app.py
   ```
   Open `http://localhost:8081` in your browser.
