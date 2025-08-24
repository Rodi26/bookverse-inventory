# BookVerse Inventory Service

Minimal FastAPI service for BookVerse.

## Local run
```
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Docker
```
docker build -t bookverse-inventory:dev .
docker run -p 8000:8000 bookverse-inventory:dev
```
