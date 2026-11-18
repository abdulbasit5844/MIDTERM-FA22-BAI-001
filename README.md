# CSC418 Lab Midterm – FA22-BAI-001

Automated ML retraining pipeline: **GitHub push → Jenkins (webhook) → retrain → test → Docker build → redeploy on AWS EC2 → email**.

| Item | Value |
|---|---|
| Jenkins job | `MIDTERM-FA22-BAI-001` (http://13.51.196.90:8081) |
| API | http://13.51.196.90:8000/metrics , `POST /predict` |
| Dataset | `dataset/train.csv` generated from `config.json` with `generate_dataset.py` |

## Pipeline stages (Jenkinsfile)
1. **Fetch latest data** – `checkout scm`
2. **Build dependency image** – cached `deps` stage of the Dockerfile
3. **Retrain model** – `python train.py` → `artifacts/model.joblib`, `artifacts/metrics.json`
4. **Test** – `pytest tests` (dataset, /health, /metrics, /predict)
5. **Build Docker image** – `midterm-fa22-bai-001:<build>`
6. **Deploy on EC2** – replace container `midterm-api` on port 8000, verify `git_sha`
7. **Post-build email** – to qasimalik@gmail.com, subject contains `FA22-BAI-001`

## Local usage
```bash
python generate_dataset.py --config config.json --output dataset/train.csv
python train.py
uvicorn app:app --port 8000
```

Example prediction:
```bash
curl -X POST http://13.51.196.90:8000/predict -H 'Content-Type: application/json' \
  -d '{"records":[{"cpu_usage":0.5,"memory_pressure":0.2,"disk_io":-0.1,"request_rate":0.4}]}'
```
