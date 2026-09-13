from datetime import date
from fastapi.testclient import TestClient
from app.main import app

def login(client, email):
    response=client.post('/auth/login',json={'email':email,'password':'demo123'})
    assert response.status_code==200
    return {'Authorization':f"Bearer {response.json()['access_token']}"}

def test_employee_cannot_access_manager_directory_or_finder():
    with TestClient(app) as client:
        headers=login(client,'sarahwilson@talentreadiness.demo')
        assert client.get('/employees',headers=headers).status_code==403
        response=client.post('/replacement/find',headers=headers,json={'absent_employee_id':2,'project_id':1,'date':date.today().isoformat(),'required_hours':8})
        assert response.status_code==403

def test_absence_requires_existing_project_membership():
    with TestClient(app) as client:
        headers=login(client,'manager@talentreadiness.demo')
        response=client.post('/absences',headers=headers,json={'employee_id':10,'project_id':1,'date':'2030-01-01','reason':'test'})
        assert response.status_code==400

def test_public_signup_cannot_create_manager():
    with TestClient(app) as client:
        response=client.post('/auth/signup',json={'name':'Unsafe Manager','email':'unsafe@example.demo','password':'secure123','role':'manager'})
        assert response.status_code==403
