# export_openapi.py
import json
from main import app # FastAPI 인스턴스 임포트

def export_json():
    openapi_schema = app.openapi()
    with open("openapi.json", "w") as f:
        json.dump(openapi_schema, f, indent=2)

if __name__ == "__main__":
    export_json()