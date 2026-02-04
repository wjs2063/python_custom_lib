import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from exception.aggregate_root import (  # 예외 클래스가 정의된 위치에 맞게 수정하세요
    add_exceptions,
    NotFoundException,
    AuthTokenException,
    BadRequestException,
    AppBaseException
)
@pytest.fixture
def client(app):
    # raise_server_exceptions=False 설정을 해야 500 에러가 터지지 않고 응답으로 옵니다.
    return TestClient(app, raise_server_exceptions=False)
# 1. 테스트용 FastAPI 앱 설정
@pytest.fixture
def app():
    _app = FastAPI()
    add_exceptions(_app)

    # 테스트를 위한 임시 엔드포인트들
    @_app.get("/not-found")
    def trigger_not_found():
        raise NotFoundException()

    @_app.get("/auth-error")
    def trigger_auth_error():
        raise AuthTokenException(detail="Token expired")

    @_app.get("/unexpected-error")
    def trigger_unexpected():
        message = "Unexpected system failure"
        raise RuntimeError(message)

    return _app


# 2. 커스텀 도메인 예외 테스트 (Parametrize 활용)
@pytest.mark.parametrize("path, expected_status, expected_code, expected_msg", [
    ("/not-found", 404, 44, "해당 정보를 찾을 수 없습니다"),
    ("/auth-error", 401, 50, "유효하지않은 토큰입니다."),
])
def test_custom_exceptions(client, path, expected_status, expected_code, expected_msg):
    response = client.get(path)

    assert response.status_code == expected_status
    data = response.json()
    assert data["code"] == expected_code
    assert data["message"] == expected_msg

# 3. 의도치 않은 시스템 예외(Exception) 테스트
def test_unexpected_exception(client):
    response = client.get("/unexpected-error")

    assert response.status_code == 500
    data = response.json()
    assert data["code"] == 99  # 우리가 설정한 기본 에러 코드
    assert data["message"] == "Internal Server Error"

# 4. 런타임에 동적으로 메시지를 변경하는 경우 테스트
def test_dynamic_exception_message(app, client):
    @app.get("/dynamic-error")
    def trigger_dynamic():
        raise BadRequestException(message="커스텀 메시지", detail="상세 내용")

    response = client.get("/dynamic-error")
    assert response.status_code == 400
    assert response.json()["message"] == "커스텀 메시지"