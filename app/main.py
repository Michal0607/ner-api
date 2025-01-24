from fastapi import FastAPI, HTTPException
from app.models.ner_model import load_ner_model, predict_ner
from app.utils.extractors import extract_dates_with_positions,  extract_pesel_with_positions, extract_time

app = FastAPI(title="ner-api-sim")

ner_pipeline = load_ner_model()

@app.post("/analyze")
async def analyze_text(text: str):
    try:
        ner_results = predict_ner(text, ner_pipeline)

        dates = extract_dates_with_positions(text)
        times = extract_time(text)

        pesels = extract_pesel_with_positions(text)

        return {
            "input_text": text,
            "ner_results": ner_results,
            "DATE": dates,
            "TIME": times,
            "PESEL": pesels,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")