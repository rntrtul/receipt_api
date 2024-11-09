from fastapi.testclient import TestClient

from .main import app

client = TestClient(app)

valid_receipt_target = {
    "retailer": "Target",
    "purchaseDate": "2022-01-01",
    "purchaseTime": "13:01",
    "items": [
        {"shortDescription": "Mountain Dew 12PK", "price": "6.49"},
        {"shortDescription": "Emils Cheese Pizza", "price": "12.25"},
        {"shortDescription": "Knorr Creamy Chicken", "price": "1.26"},
        {"shortDescription": "Doritos Nacho Cheese", "price": "3.35"},
        {"shortDescription": "   Klarbrunn 12-PK 12 FL OZ  ", "price": "12.00"},
    ],
    "total": "35.35",
}

valid_receipt_mm = {
    "retailer": "M&M Corner Market",
    "purchaseDate": "2022-03-20",
    "purchaseTime": "14:33",
    "items": [
        {"shortDescription": "Gatorade", "price": "2.25"},
        {"shortDescription": "Gatorade", "price": "2.25"},
        {"shortDescription": "Gatorade", "price": "2.25"},
        {"shortDescription": "Gatorade", "price": "2.25"},
    ],
    "total": "9.00",
}

invalid_receipt = {
    "retailer": "",
    "purchaseDate": "2022-01-01",
    "purchaseTime": "13:01",
    "items": [
        {"shortDescription": "Mountain Dew 12PK", "price": "6.49"},
        {"shortDescription": "Emils Cheese Pizza", "price": "12.25"},
        {"shortDescription": "Knorr Creamy Chicken", "price": "1.26"},
        {"shortDescription": "Doritos Nacho Cheese", "price": "3.35"},
        {"shortDescription": "   Klarbrunn 12-PK 12 FL OZ  ", "price": "12.00"},
    ],
}


def test_valid_receipt_valid_id():
    response = client.post("/receipts/process", json=valid_receipt_target)

    assert response.status_code == 200
    assert "id" in response.json()

    receipt_id = response.json()["id"]
    response = client.get(f"/receipts/{receipt_id}/points")

    assert response.status_code == 200
    assert "points" in response.json()
    assert response.json()["points"] == 28


def test_multiple_valid_receipts():
    response = client.post("/receipts/process", json=valid_receipt_target)
    target_id = response.json()["id"]

    response = client.post("/receipts/process", json=valid_receipt_mm)
    mm_id = response.json()["id"]

    mm_points_response = client.get(f"/receipts/{mm_id}/points")
    target_points_response = client.get(f"/receipts/{target_id}/points")

    assert mm_points_response.status_code == 200
    assert target_points_response.status_code == 200

    assert "points" in mm_points_response.json()
    assert "points" in target_points_response.json()

    assert mm_points_response.json()["points"] == 109
    assert target_points_response.json()["points"] == 28


def test_invalid_id():
    response = client.get(f"/receipts/1235/points")

    assert response.status_code == 404
    assert "description" in response.json()
    assert response.json()["description"] == "No receipt found for that id"


def test_invalid_receipt():
    response = client.post("/receipts/process", json=invalid_receipt)

    assert response.status_code == 400
    assert "description" in response.json()
    assert response.json()["description"] == "The receipt is invalid"


def test_invalid_valid_receipt():
    client.post("/receipts/process", json=invalid_receipt)

    valid_response = client.post("/receipts/process", json=valid_receipt_target)
    receipt_id = valid_response.json()["id"]
    response = client.get(f"/receipts/{receipt_id}/points")

    assert response.status_code == 200
    assert response.json()["points"] == 28
