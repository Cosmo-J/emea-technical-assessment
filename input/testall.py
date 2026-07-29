# written with an LLM

import json
import urllib.error
import urllib.request
import uuid
from pathlib import Path


URL = "http://localhost:8080/restate/call/OrderIngestion/submitOrder"

SCRIPT_DIR = Path(__file__).resolve().parent
JSON_FILES = sorted(SCRIPT_DIR.glob("*.json"))


def submit_json_file(path: Path) -> None:
    try:
        with path.open("r", encoding="utf-8") as file:
            payload = json.load(file)

        encoded_payload = json.dumps(payload).encode("utf-8")

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "idempotency-key": str(uuid.uuid4()),
        }

        request = urllib.request.Request(
            URL,
            data=encoded_payload,
            headers=headers,
            method="POST",
        )

        with urllib.request.urlopen(request, timeout=30) as response:
            response_body = response.read().decode("utf-8", errors="replace")

            print(f"[SUCCESS] {path.name} (HTTP {response.status})")

            if response_body:
                print(f"          Response: {response_body}")

    except json.JSONDecodeError as error:
        print(
            f"[FAILED]  {path.name} -> Invalid JSON at "
            f"line {error.lineno}, column {error.colno}: {error.msg}"
        )

    except urllib.error.HTTPError as error:
        response_body = error.read().decode("utf-8", errors="replace")

        print(f"[FAILED]  {path.name} -> HTTP {error.code}: {error.reason}")

        if response_body:
            print(f"          Response: {response_body}")

    except urllib.error.URLError as error:
        print(f"[FAILED]  {path.name} -> Connection error: {error.reason}")

    except TimeoutError:
        print(f"[FAILED]  {path.name} -> Request timed out")

    except Exception as error:
        print(f"[ERROR]   {path.name} -> {type(error).__name__}: {error}")


def main() -> None:
    if not JSON_FILES:
        print(f"No JSON files found in: {SCRIPT_DIR}")
        return

    print(f"Endpoint: {URL}")
    print(f"Directory: {SCRIPT_DIR}")
    print(f"Found {len(JSON_FILES)} JSON file(s)\n")

    for path in JSON_FILES:
        submit_json_file(path)


if __name__ == "__main__":
    main()
