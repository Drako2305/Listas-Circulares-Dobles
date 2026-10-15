import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

from trainyard.circular_list import DoublyCircularWagonList, DuplicateWagonError
from trainyard.models import Wagon

WEB_ROOT = Path(__file__).resolve().parent.parent / "web"
MAX_REQUEST_BYTES = 16_384


def create_demo_yard() -> DoublyCircularWagonList:
    yard = DoublyCircularWagonList()
    sample_wagons = (
        Wagon("FC-204", "Grain", "Port of North", 54.5),
        Wagon("FC-118", "Iron ore", "Foundry East", 71.2),
        Wagon("FC-362", "Timber", "River Terminal", 38.0),
        Wagon("FC-075", "Fertilizer", "Valley Depot", 46.8),
    )
    for wagon in sample_wagons:
        yard.append(wagon)
    return yard


def create_request_handler(yard: DoublyCircularWagonList) -> type[BaseHTTPRequestHandler]:
    class WagonRequestHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            path = urlsplit(self.path).path
            if path == "/api/wagons":
                self._send_json(200, self._yard_snapshot())
                return
            if path == "/api/health":
                self._send_json(200, {"status": "ok"})
                return

            static_files = {
                "/": ("index.html", "text/html; charset=utf-8"),
                "/static/styles.css": ("static/styles.css", "text/css; charset=utf-8"),
                "/static/app.js": ("static/app.js", "text/javascript; charset=utf-8"),
            }
            asset = static_files.get(path)
            if asset is None:
                self._send_json(404, {"error": "Resource not found."})
                return

            file_path = WEB_ROOT / asset[0]
            try:
                content = file_path.read_bytes()
            except FileNotFoundError:
                self._send_json(404, {"error": "Frontend asset is not available yet."})
                return
            self.send_response(200)
            self.send_header("Content-Type", asset[1])
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)

        def do_POST(self) -> None:
            path = urlsplit(self.path).path
            if path == "/api/wagons":
                self._create_wagon()
                return
            if path in ("/api/navigation/next", "/api/navigation/previous"):
                direction = path.rsplit("/", 1)[1]
                current = yard.move(direction)
                self._send_json(200, {"current_wagon": current.to_dict() if current else None})
                return
            self._send_json(404, {"error": "Resource not found."})

        def do_DELETE(self) -> None:
            path = urlsplit(self.path).path
            prefix = "/api/wagons/"
            if not path.startswith(prefix):
                self._send_json(404, {"error": "Resource not found."})
                return

            wagon_id = unquote(path[len(prefix):])
            try:
                removed = yard.remove(wagon_id)
            except KeyError:
                self._send_json(404, {"error": f"Wagon {wagon_id} was not found."})
                return
            self._send_json(200, {"removed_wagon": removed.to_dict()})

        def _create_wagon(self) -> None:
            try:
                payload = self._read_json()
                wagon = Wagon(
                    wagon_id=payload["wagon_id"],
                    cargo=payload["cargo"],
                    destination=payload["destination"],
                    weight_tonnes=payload["weight_tonnes"],
                )
                yard.append(wagon)
            except DuplicateWagonError as error:
                self._send_json(409, {"error": str(error)})
                return
            except (KeyError, TypeError, ValueError) as error:
                self._send_json(400, {"error": str(error)})
                return
            self._send_json(201, {"wagon": wagon.to_dict()})

        def _read_json(self) -> dict[str, object]:
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
            except ValueError as error:
                raise ValueError("Content-Length must be a valid integer.") from error
            if content_length <= 0 or content_length > MAX_REQUEST_BYTES:
                raise ValueError("Request body must be between 1 and 16384 bytes.")

            payload = json.loads(self.rfile.read(content_length))
            if not isinstance(payload, dict):
                raise ValueError("Request body must be a JSON object.")
            return payload

        def _yard_snapshot(self) -> dict[str, object]:
            wagons = [wagon.to_dict() for wagon in yard.wagons()]
            return {
                "wagons": wagons,
                "current_wagon": yard.current.to_dict() if yard.current else None,
                "count": len(yard),
                "total_weight_tonnes": round(
                    sum(wagon.weight_tonnes for wagon in yard.wagons()), 2
                ),
            }

        def _send_json(self, status: int, payload: dict[str, object]) -> None:
            content = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)

        def log_message(self, format_string: str, *args: object) -> None:
            print(f"[{self.log_date_time_string()}] {format_string % args}")

    return WagonRequestHandler


def create_server(host: str = "127.0.0.1", port: int = 8000) -> HTTPServer:
    return HTTPServer((host, port), create_request_handler(create_demo_yard()))


def main() -> None:
    server = create_server()
    print(f"Freight Wagon Yard is running at http://{server.server_address[0]}:{server.server_port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
