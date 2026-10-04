import pytest
import sys
import os

# Add the project root to the Python path so the app module can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_index_route(client):
    """Test that the index route returns a 200 HTTP status."""
    response = client.get('/')
    assert response.status_code == 200

def test_health_route_status_code(client):
    """Test that the /health route returns a 200 HTTP status."""
    response = client.get('/health')
    assert response.status_code == 200

def test_health_route_json(client):
    """Test that the /health route returns the correct JSON."""
    response = client.get('/health')
    json_data = response.get_json()
    assert json_data['status'] == 'healthy'
    assert json_data['version'] == 'v2'

def test_api_data_route(client):
    """Test that the /api/data route returns a 200 HTTP status."""
    response = client.get('/api/data')
    assert response.status_code == 200
