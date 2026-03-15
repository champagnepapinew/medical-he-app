from fastapi.testclient import TestClient

from app.main import app


def assert_ok(client: TestClient, path: str) -> None:
    response = client.get(path)
    assert response.status_code == 200, f"{path} returned {response.status_code}"


def main() -> None:
    client = TestClient(app)

    for path in ["/", "/patients", "/measurements", "/he", "/benchmark"]:
        assert_ok(client, path)

    bad_measurement = client.post(
        "/measurements",
        data={"patient_id": 1, "kind": "glucose", "value": "bledna-liczba", "taken_at": ""},
    )
    assert bad_measurement.status_code == 400

    good_measurement = client.post(
        "/measurements",
        data={"patient_id": 1, "kind": "glucose", "value": "98.5", "taken_at": ""},
        follow_redirects=False,
    )
    assert good_measurement.status_code == 303

    print("Smoke test OK")


if __name__ == "__main__":
    main()
