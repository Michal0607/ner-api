from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
import numpy as np

def load_ner_model():
    tokenizer = AutoTokenizer.from_pretrained("pczarnik/herbert-base-ner")
    model = AutoModelForTokenClassification.from_pretrained("pczarnik/herbert-base-ner")
    ner_pipeline = pipeline(
        "ner", model=model, tokenizer=tokenizer, aggregation_strategy="simple"
    )
    return ner_pipeline

def predict_ner(text, ner_pipeline):
    results = ner_pipeline(text)
    for result in results:
        for key, value in result.items():
            if isinstance(value, (np.float32, np.float64)):
                result[key] = float(value)
    return results