"""Tests run by Jenkins after train.py has produced artifacts/."""
import json
import os
from pathlib import Path

import pandas as pd
from fastapi.testclient import TestClient

from app import app

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
CONFIG = json.loads((ROOT / 'config.json').read_text())
client = TestClient(app)


def test_dataset_has_required_columns():
    df = pd.read_csv(ROOT / 'dataset' / 'train.csv')
    assert set(CONFIG['features'] + ['label']).issubset(df.columns)
    assert len(df) >= 100 and df['label'].nunique() == 2


def test_health_ok():
    assert client.get('/health').json()['status'] == 'ok'


def test_metrics_fields_and_quality():
    m = client.get('/metrics').json()
    for key in ['student_id', 'accuracy', 'training_rows', 'model_version', 'git_sha']:
        assert key in m
    assert m['student_id'] == CONFIG['student_id']
    assert m['training_rows'] == len(pd.read_csv(ROOT / 'dataset' / 'train.csv'))
    assert m['accuracy'] >= 0.6
    assert m['git_sha'] == os.environ.get('GIT_COMMIT', m['git_sha'])


def test_predict():
    record = {f: 0.5 for f in CONFIG['features']}
    r = client.post('/predict', json={'records': [record, record]})
    assert r.status_code == 200
    body = r.json()
    assert len(body['predictions']) == 2
    assert all(p in (0, 1) for p in body['predictions'])


def test_predict_rejects_empty():
    assert client.post('/predict', json={'records': []}).status_code == 422
