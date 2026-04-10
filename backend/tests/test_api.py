import os
from pathlib import Path

os.environ['DATABASE_URL'] = f"sqlite:///{Path(__file__).with_name('test.db')}"
os.environ['SECRET_KEY'] = 'test-secret'

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.session import Base, get_db
from app.main import app

engine = create_engine(os.environ['DATABASE_URL'], connect_args={'check_same_thread': False})
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def auth_headers() -> dict[str, str]:
    email = 'user@example.com'
    password = 'password123'
    client.post('/api/v1/auth/register', json={'email': email, 'password': password})
    response = client.post('/api/v1/auth/login', json={'email': email, 'password': password})
    token = response.json()['access_token']
    return {'Authorization': f'Bearer {token}'}


def test_project_asset_crud_flow():
    headers = auth_headers()

    create_response = client.post(
        '/api/v1/projects',
        json={'title': 'Test Project', 'genre': 'Drama', 'description': 'Pilot'},
        headers=headers,
    )
    assert create_response.status_code == 201
    project_id = create_response.json()['id']

    list_response = client.get('/api/v1/projects', headers=headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    steps_response = client.get(f'/api/v1/projects/{project_id}/steps', headers=headers)
    assert steps_response.status_code == 200
    assert len(steps_response.json()) == 5

    asset_response = client.post(
        f'/api/v1/projects/{project_id}/assets',
        json={
            'step_code': 'outline',
            'asset_type': 'story-outline',
            'title': 'v1 outline',
            'content': {'beats': ['a', 'b']},
        },
        headers=headers,
    )
    assert asset_response.status_code == 201
    asset_id = asset_response.json()['id']

    update_asset_response = client.post(
        f'/api/v1/projects/{project_id}/assets',
        json={
            'step_code': 'outline',
            'asset_type': 'story-outline',
            'title': 'v2 outline',
            'content': {'beats': ['a', 'b', 'c']},
        },
        headers=headers,
    )
    assert update_asset_response.status_code == 201
    assert update_asset_response.json()['version'] == 2

    versions_response = client.get(
        f'/api/v1/projects/{project_id}/assets/{asset_id}/versions',
        headers=headers,
    )
    assert versions_response.status_code == 200
    assert [item['version'] for item in versions_response.json()] == [2, 1]

    delete_response = client.delete(f'/api/v1/projects/{project_id}', headers=headers)
    assert delete_response.status_code == 204
