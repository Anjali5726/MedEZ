import google.generativeai as genai
import os
import re
import traceback
from dotenv import load_dotenv

load_dotenv()

# ── BANNED PATTERNS ──────────────────────────────────────────────────────────

BANNED_PATTERNS = {
    'you have': r'\byou\s+have\b',
    'you are suffering': r'\byou\s+are\s+suffering\b',
    'you are diagnosed': r'\byou\s+are\s+diagnosed\b',
    'take this medicine': r'\btake\s+this\s+medicine\b',
    'stop taking': r'\bstop\s+taking\b',
    'increase your dose': r'\bincrease\s+your\s+dose\b',
    'you will die': r'\byou\s+will\s+die\b',
    'terminal': r'\bterminal\b(?!\s+(ileum|part|segment|division|branch|section|end|line))'
}

REPLACEMENTS = {
    r'\byou have\b': 'the patient has',
    r'\byou are suffering\b': 'the patient is suffering',
    r'\byou are diagnosed\b': 'the patient is diagnosed',
    r'\btake this medicine\b': 'use this medication',
    r'\bstop taking\b': 'discontinue',
    r'\bincrease your dose\b': 'increase the dosage',
    r'\byou\b': 'the patient',
}

DISCLAIMER = """

---
⚠️ IMPORTANT: This is an automated explanation for 
general understanding only. It is NOT medical advice 
and NOT a diagnosis. Always consult a qualified doctor 
before making any health decision. 
Emergency: Call 112
"""

LOG_PATH = r"C:\Users\Praveen\MebEZ\debug_safety_log.txt"

# ── HELPERS ──────────────────────────────────────────────────────────────────

def write_log(content):
    try:
        with open(LOG_PATH, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception:
        pass

def apply_safety_filter(result):
    """
    Step 1 — auto-replace banned phrases with safe alternatives.
    Step 2 — check if any banned patterns still remain.
    Returns (cleaned_text, is_safe)
    """
    result_clean = result
    for banned_pattern, safe_phrase in REPLACEMENTS.items():
        result_clean = re.sub(banned_pattern, safe_phrase,
                              result_clean, flags=re.IGNORECASE)

    for name, pattern in BANNED_PATTERNS.items():
        if re.search(pattern, result_clean, re.IGNORECASE):
            write_log(
                f"TRIGGERED BANNED PHRASE: {name}\n"
                f"CLEANED TEXT:\n{result_clean}\n\n"
                f"RAW TEXT:\n{result}\n"
            )
            return result_clean, False

    return result_clean, True

def get_model():
    """Configure and return Gemini model, or None if key missing"""
    api_key = os.getenv('GEMINI_KEY')
    if not api_key or api_key == "your_gemini_api_key_here":
        return None
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-flash-latest')


# ── FEATURE 1: Discharge Summary Translator ───────────────────────────────────

def translate_discharge(text):
    """Takes discharge summary text, returns plain language explanation"""

    api_key = os.getenv('GEMINI_KEY')

    # Fallback/Demo Mode if key is missing
    if not api_key or api_key == "your_gemini_api_key_here":
        return """### 📋 Simplified Care Summary (Demo Mode)

The patient underwent a **laparoscopic appendectomy (दूरबीन द्वारा अपेंडिक्स का ऑपरेशन)** due to **acute appendicitis (अपेंडिक्स में अचानक सूजन)**. The surgery was completed successfully, and the patient is currently in a **stable condition (स्थिर स्थिति)**. 

The doctor has prescribed **amoxicillin-clavulanate (Augmentin - एंटीबायोटिक)** to prevent infection and **acetaminophen (Tylenol - दर्द और बुखार की दवा)** for mild post-surgical pain relief. The patient should also continue their routine blood pressure management with **amlodipine (ब्लड प्रेशर की दवा)**. 

Please consult your doctor.""" + DISCLAIMER

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-flash-latest')

        prompt = f"""
You are a helpful medical translator for Indian patients.
The patient has received this hospital discharge summary and cannot understand it.

Your job:
1. Provide a cohesive, plain-language summary of the discharge document written in simple English (suitable for a class 8 student).
2. The entire summary narrative must be written in English. Do NOT write the paragraphs or sentences in Hindi.
3. For key medical terms, surgeries, conditions, or medications mentioned in the summary, include their simple Hindi translation/meaning in parentheses next to the English term (e.g. "wound (घाव)", "kidney (गुर्दा)", "laparoscopy (दूरबीन जांच)", "antibiotics (एंटीबायोटिक)").
4. Write the explanation in clear, patient-friendly paragraphs. Do NOT list/explain every word individually. Just write a cohesive summary.
5. Do NOT say what disease the patient has or diagnose them.
6. Do NOT suggest any new medicines or treatments.
7. End the summary with this exact sentence: "Please consult your doctor."

CRITICAL FORMATTING & SAFETY CONSTRAINTS:
- NEVER add statements like "Ask your doctor about this", "consult your physician", or "please talk to your doctor" anywhere in the body of the explanation. 
- You must ONLY write the consult statement once, exactly at the very end of the summary ("Please consult your doctor.").
- NEVER use the word "you" or address the patient directly.
- ALWAYS write in the objective third-person (e.g. write "the patient", "the condition", "the individual").
- NEVER use any of these exact phrases: "you have", "you are suffering", "you are diagnosed", "take this medicine", "stop taking", "increase your dose", "you will die", "terminal".
- If you need to describe a stopped medication, write: "the doctor discontinued the medication" or "the treatment was stopped" (do NOT use "stop taking").
- If you need to describe a diagnosis, write: "the clinical finding is..." or "the report indicates..." (do NOT use "you are diagnosed" or "you have").

Discharge Summary:
{text}
"""
        response = model.generate_content(prompt)
        result_clean, is_safe = apply_safety_filter(response.text)

        if not is_safe:
            return ("We could not generate a safe explanation for this document. "
                    "Please show this discharge summary directly to your doctor "
                    "or a trusted healthcare worker who can explain it to you.") + DISCLAIMER

        return result_clean + DISCLAIMER

    except Exception as e:
        write_log(
            "PYTHON EXCEPTION OCCURRED DURING CONVERSION\n"
            f"EXCEPTION: {str(e)}\n\n"
            f"TRACEBACK:\n{traceback.format_exc()}"
        )
        return (f"Sorry, we could not process this document right now. "
                f"Please try again or consult your doctor directly.\n\nError: {str(e)}")


# ── FEATURE 3: Medical Report Explainer ──────────────────────────────────────

def explain_medical_report(text):
    """
    Explains any medical report — blood test, X-ray, MRI,
    urine test, ECG, thyroid panel etc. in plain language.
    """
    api_key = os.getenv('GEMINI_KEY')

    if not api_key or api_key == "your_gemini_api_key_here":
        return "Demo mode — Gemini API key not configured." + DISCLAIMER

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-flash-latest')

        prompt = f"""
You are a medical report explainer for Indian patients.
A patient has uploaded a medical report they cannot understand.

Your job:
1. First identify what TYPE of report this is
   (e.g. "This is a Complete Blood Count (CBC) report"
   or "This is a Chest X-Ray report")
2. Explain each finding or value in simple English
   that a class 8 student can understand
3. For blood test values — mention if they appear
   high, low, or normal based on standard ranges
4. For imaging reports (X-ray, MRI, CT scan, Ultrasound)
   — explain what each medical term in the findings means
5. For urine/stool reports — explain what each parameter means
6. At the end — write a section called "What to tell your doctor"
   with 2-3 questions the patient should ask

CRITICAL SAFETY CONSTRAINTS:
- Do NOT diagnose any condition
- Do NOT say what disease the patient has
- Do NOT recommend any medicine or treatment
- NEVER use the word "you" — always write in third person
  e.g. "the patient" not "you"
- If anything looks potentially serious say:
  "This finding needs to be discussed with your doctor promptly"
- NEVER use these phrases: "you have", "you are suffering",
  "you are diagnosed", "stop taking", "terminal"
- Always end with exactly:
  "This explanation is for understanding only.
   Please show this report to your doctor."

Medical Report:
{text}
"""
        response = model.generate_content(prompt)
        result_clean, is_safe = apply_safety_filter(response.text)

        if not is_safe:
            return ("We could not generate a safe explanation. "
                    "Please show this report directly to your doctor.") + DISCLAIMER

        return result_clean + DISCLAIMER

    except Exception as e:
        write_log(
            "PYTHON EXCEPTION IN explain_medical_report\n"
            f"EXCEPTION: {str(e)}\n\n"
            f"TRACEBACK:\n{traceback.format_exc()}"
        )
        return (f"Sorry, could not process this report. "
                f"Please try again.\n\nError: {str(e)}")
    # ── FEATURE 4: Symptom to Specialist Mapper ──────────────────────────────────

def analyse_symptoms(symptoms_text):
    """
    Analyses symptoms and returns specialist recommendation + urgency.
    Returns a dict with specialist, urgency, reason, search_term
    """

    # Hard-coded emergency symptoms — never delegated to AI
    EMERGENCY_KEYWORDS = [
        'can\'t breathe', 'cannot breathe',
        'difficulty breathing', 'unconscious', 'not breathing',
        'stroke', 'seizure', 'fits', 'heavy bleeding',
        'collapsed', 'not responding', 'overdose', 'poisoning'
    ]

    symptoms_lower = symptoms_text.lower()
    for keyword in EMERGENCY_KEYWORDS:
        if keyword in symptoms_lower:
            return {
                'specialist': 'Emergency Room',
                'urgency': 'EMERGENCY',
                'reason': 'The symptoms described may indicate a medical emergency.',
                'search_term': 'hospital',
                'is_emergency': True
            }

    api_key = os.getenv('GEMINI_KEY')
    if not api_key or api_key == "your_gemini_api_key_here":
        return {
            'specialist': 'General Physician',
            'urgency': 'Within a week',
            'reason': 'Demo mode — please configure Gemini API key.',
            'search_term': 'general physician',
            'is_emergency': False
        }

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-flash-latest')

        prompt = f"""
You are a medical triage assistant for Indian patients.
A patient has described their symptoms. 
Your job is to suggest which type of specialist they should see.

Symptoms: {symptoms_text}

Respond in EXACTLY this format — nothing else:
SPECIALIST: [type of specialist, e.g. Cardiologist, General Physician, Dermatologist]
URGENCY: [one of: Today, Within 3 days, Within a week, No rush]
REASON: [one sentence explaining why, in simple English]
SEARCH: [single search keyword for finding this doctor, e.g. cardiologist, dermatologist, general physician]

STRICT RULES:
- Do NOT diagnose any condition
- Do NOT say what disease the patient has
- Do NOT recommend any medicine
- If symptoms sound serious but not emergency, say urgency is "Today"
- SEARCH field must be a single lowercase word or short phrase
- Keep REASON to one simple sentence
"""
        response = model.generate_content(prompt)
        text = response.text.strip()

        # Parse the structured response
        result = {
            'specialist': 'General Physician',
            'urgency': 'Within a week',
            'reason': 'Please consult a doctor about your symptoms.',
            'search_term': 'general physician',
            'is_emergency': False
        }

        for line in text.split('\n'):
            line = line.strip()
            if line.startswith('SPECIALIST:'):
                result['specialist'] = line.replace('SPECIALIST:', '').strip()
            elif line.startswith('URGENCY:'):
                result['urgency'] = line.replace('URGENCY:', '').strip()
            elif line.startswith('REASON:'):
                result['reason'] = line.replace('REASON:', '').strip()
            elif line.startswith('SEARCH:'):
                result['search_term'] = line.replace('SEARCH:', '').strip().lower()

        return result

    except Exception as e:
        write_log(f"EXCEPTION in analyse_symptoms:\n{traceback.format_exc()}")
        return {
            'specialist': 'General Physician',
            'urgency': 'Within a week',
            'reason': f'Could not analyse symptoms. Please consult a doctor.',
            'search_term': 'general physician',
            'is_emergency': False
        }