import pytest
from app.app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True  # nosemgrep
    with app.test_client() as c:
        yield c

def test_health(client):
    r = client.get('/health')
    assert r.status_code == 200
    assert r.get_json().get('status') == 'ok'

def test_login_success(client):
    r = client.post('/login', json={'username':'admin','password':'password'})
    assert r.status_code == 200
    assert 'token' in r.get_json()

def test_login_fail(client):
    r = client.post('/login', json={'username':'x','password':'y'})
    assert r.status_code == 401

def test_notes_flow(client):
    # verify we can add and list notes
    r = client.get('/notes')
    assert r.status_code == 200
    before = len(r.get_json().get('notes'))
    r = client.post('/notes', json={'note':'hello'})
    assert r.status_code == 201
    r = client.get('/notes')
    assert 'hello' in r.get_json().get('notes')
