import os
import tempfile
from pathlib import Path

os.environ['CITYFIX_DB'] = str(Path(tempfile.mkdtemp()) / 'test.sqlite3')
os.environ['CITYFIX_UPLOADS'] = str(Path(tempfile.mkdtemp()) / 'uploads')

from fastapi.testclient import TestClient
from main import app


def test_create_list_update():
    with TestClient(app) as client:
        r = client.get('/api/issues')
        assert r.status_code == 200
        assert len(r.json()) >= 3
        new = client.post('/api/issues', data={
            'title': 'Broken bench', 'description': 'Bench is broken in the park.',
            'category': 'Other', 'latitude': '43.24', 'longitude': '76.95'
        })
        assert new.status_code == 201, new.text
        issue = new.json()
        assert issue['status'] == 'New'
        changed = client.patch(f"/api/issues/{issue['id']}/status", json={'status': 'Resolved'})
        assert changed.status_code == 200
        assert changed.json()['status'] == 'Resolved'
        assert client.patch(f"/api/issues/{issue['id']}/status", json={'status':'Wrong'}).status_code == 400
