from fastapi import FastAPI, HTTPException, Query
from app.models.ner_model import load_ner_model, predict_ner
from app.utils.extractors import extract_dates_with_positions, extract_pesel_with_positions, extract_time, extract_phone_with_positions


app = FastAPI(title="ner-api-sim")
ner_pipeline = load_ner_model()

@app.post("/analyze")
async def analyze_text(
    text: str,
    threshold: float = Query(0.85, description="Minimalny próg score dla wyników NER")
):
    try:
        ner_results_all = predict_ner(text, ner_pipeline)

        ner_results_filtered = [
            res for res in ner_results_all
            if res.get("score", 0.0) >= threshold
        ]

        dates = extract_dates_with_positions(text)
        times = extract_time(text)
        pesels = extract_pesel_with_positions(text)
        phones = extract_phone_with_positions(text) 

        return {
            "input_text": text,
            "ner_results": ner_results_filtered,
            "DATE": dates,
            "TIME": times,
            "PESEL": pesels,
            "PHONE": phones,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal Server Error: {str(e)}"
        )
