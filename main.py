from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
import re
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

app = FastAPI(title="Diabetes Management API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PatientData(BaseModel):
    bloodSugar: Optional[str] = Field(None, description="Current blood sugar level")
    timing: str = Field(..., description="Measurement timing context")
    mealPlan: str = Field(..., description="Planned food or meal")

# Initialize OpenAI Client safely
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None

# Fixed to accept 2 arguments: prompt and fallback_type
def get_openai_recommendation(prompt: str, fallback_type: str = "exercise") -> str:
    fallback_responses = {
        "exercise": "Engage in 20 minutes of moderate brisk walking post-meal to enhance insulin sensitivity and facilitate gradual glucose uptake.",
        "meal": "Ensure a balanced plate architecture by pairing complex fiber sources with lean proteins to blunt rapid postprandial glycemic spikes."
    }
    
    if not client:
        return fallback_responses.get(fallback_type, "Maintain consistent tracking and adhere to prescribed dietary protocols.")

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system", 
                    "content": "You are a clinical diabetes informatics assistant. Provide direct, precise feedback based on standard nutritional protocols. Do not include generic medical disclaimers."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            max_tokens=300,
            temperature=0.2,
        )
        return response.choices[0].message.content
    except Exception:
        return fallback_responses.get(fallback_type, "Maintain consistent tracking and adhere to prescribed dietary protocols.")

# --- DETERMINISTIC CLINICAL LOGIC ---
def analyze_blood_sugar_locally(sugar_string: str, timing: str) -> str:
    if not sugar_string or sugar_string.strip() == "":
        return "Classification: Not Provided\nAction: Regular tracking is recommended to establish clinical baselines."
    
    match = re.search(r"[-+]?\d*\.\d+|\d+", sugar_string)
    if not match:
        return f"Metric '{sugar_string}' logged. Ensure standardized numerical inputs (e.g., 6.0 mmol/L) for automated threshold analysis."
        
    val = float(match.group())
    is_mgdl = "mg" in sugar_string.lower() or val > 30 
    
    if is_mgdl:
        if "fasting" in timing.lower():
            if val >= 126: return f"Classification: Elevated ({val} mg/dL).\nContext: Fasting targets are generally below 126 mg/dL."
            elif val < 70: return f"Classification: Low ({val} mg/dL).\nContext: Monitor closely for hypoglycemia."
            else: return f"Classification: Target Range ({val} mg/dL).\nContext: Metric is within standard fasting parameters."
        else:
            if val >= 180: return f"Classification: Elevated ({val} mg/dL).\nContext: Post-meal targets should generally remain below 180 mg/dL."
            else: return f"Classification: Target Range ({val} mg/dL).\nContext: Metric is within standard post-meal parameters."
    else:
        if "fasting" in timing.lower():
            if val >= 7.0: return f"Classification: Elevated ({val} mmol/L).\nContext: Fasting targets are generally below 7.0 mmol/L."
            elif val < 4.0: return f"Classification: Low ({val} mmol/L).\nContext: Monitor closely for hypoglycemia."
            else: return f"Classification: Target Range ({val} mmol/L).\nContext: Metric is within standard fasting parameters."
        else:
            if val >= 8.5: return f"Classification: Elevated ({val} mmol/L).\nContext: Post-meal targets should generally remain below 8.5 mmol/L."
            else: return f"Classification: Target Range ({val} mmol/L).\nContext: Metric is within standard post-meal parameters."

@app.post("/api/analyze")
def analyze_patient_metrics(data: PatientData):
    analysis_result = analyze_blood_sugar_locally(data.bloodSugar, data.timing)
    
    base_context = f"Patient data - Blood sugar: {data.bloodSugar or 'Not provided'} ({data.timing}). Planned meal: {data.mealPlan}."
    
    prompt_exercise = f"{base_context} Provide a concise, 2-sentence exercise suggestion optimized for glucose metabolism based on this specific timing."
    prompt_meal = f"{base_context} Provide a concise, 2-sentence nutritional critique of this meal, suggesting specific macro-nutrient adjustments if necessary."
    
    exercise = get_openai_recommendation(prompt_exercise, "exercise")
    meal = get_openai_recommendation(prompt_meal, "meal")
    
    return {
        "exercise": exercise,
        "meal": meal,
        "analysis": analysis_result
    }