import json
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from trainyard.circular_list import DoublyCircularWagonList
from trainyard.http_server import create_request_handler
from trainyard.models import Wagon
from http.server import HTTPServer


class WagonApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.yard = DoublyCircularWagonList()
        cls.yard.append(Wagon("FC-01", "Grain", "North Yard", 25))
        cls.server = HTTPServer(
            ("127.0.0.1", 0), create_request_handler(cls.yard)
        )
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def setUp(self) -> None:
        self.yard.reset()
        self.yard.append(Wagon("FC-01", "Grain", "North Yard", 25))

    def request_json(
        self, method: str, path: str, payload: dict[str, object] | None = None
    ) -> tuple[int, dict[str, object]]:
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = Request(
            self.base_url + path,
            data=body,
            headers={"Content-Type": "application/json"} if body is not None else {},
            method=method,
        )
        try:
            response = urlopen(request)
        except HTTPError as error:
            response = error
        with response:
            return response.status, json.loads(response.read())

    def test_get_wagons_returns_current_node_and_totals(self) -> None:
        status, body = self.request_json("GET", "/api/wagons")
        self.assertEqual(status, 200)
        self.assertEqual(body["count"], 1)
        self.assertEqual(body["current_wagon"]["wagon_id"], "FC-01")

    def test_create_duplicate_and_delete_wagons(self) -> None:
        payload = {
            "wagon_id": "FC-02",
            "cargo": "Iron ore",
            "destination": "Foundry",
            "weight_tonnes": 40,
        }
        self.assertEqual(self.request_json("POST", "/api/wagons", payload)[0], 201)
        self.assertEqual(self.request_json("POST", "/api/wagons", payload)[0], 400)
        self.assertEqual(self.request_json("DELETE", "/api/wagons/FC-02")[0], 200)

    def test_navigation_moves_around_the_circular_list(self) -> None:
        self.yard.append(Wagon("FC-02", "Timber", "River Yard", 30))
        self.request_json("POST", "/api/navigation/previous")
        self.assertEqual(self.yard.current.wagon_id, "FC-02")
        self.request_json("POST", "/api/navigation/next")
        self.assertEqual(self.yard.current.wagon_id, "FC-01")

    def test_invalid_wagon_data_is_reported(self) -> None:
        status, body = self.request_json(
            "POST",
            "/api/wagons",
            {"wagon_id": "FC-02", "cargo": "", "destination": "Yard", "weight_tonnes": 20},
        )
        self.assertEqual(status, 400)
        self.assertIn("cargo", body["error"])


if __name__ == "__main__":
    unittest.main()
