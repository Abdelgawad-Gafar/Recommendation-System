# Recommendation System

## What this system does

Recommends reels using:

* Content-based filtering
* Collaborative filtering (SVD)
* Trend-based ranking

---

## Architecture

* FastAPI backend
* Chroma vector database
* SQL database
* Offline model training

---

## Project Structure

* main.py → API entry
* reel_service.py → recommendation logic
* user_service.py → user logic
* cf_trainer.py → SVD training
* run_daily_training.py → retraining script
* database.py → DB setup
* models.py → schemas

---

## Environment Variables

Create `.env`

```
DB_URL=postgresql://user:password@db:5432/reco
CHROMA_DB_PATH=/data/vector_db
MODEL_PATH=/data/model/svd.pkl
```

---

## Run locally

```
pip install -r requirements.txt
uvicorn main:app --reload
```

---

## Run training

```
python run_daily_training.py
```

---

## API

```
GET /recommend/{user_id}
```

---

## Production

* Use gunicorn + uvicorn workers
* Store model + vector DB in volume
* Use cron or celery for retraining
* Add caching layer (Redis)

---

## Scaling

* Separate training service
* Use async DB
* Add monitoring (Prometheus)

---

## Notes

* Do not commit .env
* Do not commit logs
* Clean **pycache**
