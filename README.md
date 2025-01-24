# NER API

NER API is a FastAPI application that analyzes text to detect key information such as dates, times, and PESEL numbers. It leverages a machine learning model to recognize named entities such as persons, locations, and organizations, while dates, times, and PESEL numbers are detected using regular expressions.

## Project Structure

```
ner_api/
│-- app/
│   │-- data/
|   |   │-- time_words.json
│   │-- models/
│   │   │-- ner_model.py
│   │-- utils/
│   │   │-- extractors.py
│   │-- __init__.py
│-- main.py
│-- docker-compose.yml
│-- Dockerfile
│-- requirements.txt
```

- **app/models/ner_model.py** - Loads the NER model to recognize named entities such as persons, locations, and organizations.
- **app/utils/extractors.py** - Functions for extracting dates, times, and PESEL numbers.
- **main.py** - Main FastAPI application with an endpoint `/analyze`.
- **docker-compose.yml** - Configuration file to run the application in a Docker container.
- **Dockerfile** - Docker image definition for the application.
- **requirements.txt** - List of required dependencies.

## Installation and Running

1. **Running locally:**

   Requirements: Python 3.8+

   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

   The application will be available at: `http://localhost:8000`

2. **Running with Docker:**

   ```bash
   docker-compose up --build
   ```

   The application will be available at: `http://localhost:8000`

## Using the API

Available endpoint:

- **POST /analyze** - Analyzes the text for named entities, dates, and PESEL numbers.

  Example request:

  ```json
  {
      "Jan Kowalski was born on May 5, 1987. His PESEL number is 87050512345. The meeting will take place at nine in the morning."
  }
  ```

  Example response:

  ```json
  {
      "input_text": "Jan Kowalski was born on May 5, 1987. His PESEL number is 87050512345. The meeting will take place at nine in the morning.",
      "ner_results": [...],
      "DATE": [{"date": "May 5, 1987", "start": 19, "stop": 30}],
      "TIME": [{"time": "09:00", "start": 65, "stop": 79}],
      "PESEL": [{"pesel": "87050512345", "start": 45, "stop": 56}]
  }
  ```

## Technologies Used

- FastAPI
- Transformers (Herbert Base NER model)
- PyTorch
- Docker

## Author
Project developed by [Your Name].
