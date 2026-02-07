import os
import sys
import yaml
import logging
import logging.config
from pathlib import Path

def init_logging():
    # 1. 프로젝트 루트 경로를 sys.path에 추가 (src를 찾기 위함)
    # 현재 파일 위치: python_lib_dev/src/shared/utils/logger/root.py
    # 프로젝트 루트: python_lib_dev/
    root_path = Path(__file__)
    sys.path.append(str(root_path))

    # 2. YAML 파일 경로 설정
    yaml_path = Path(__file__).parent / "log_config.yaml"
    with open(yaml_path, "r") as f:
        config = yaml.safe_load(f)
        # 3. 설정 주입
        logging.config.dictConfig(config)

init_logging()
log = logging.getLogger("application")



if __name__ == "__main__":
    init_logging()

    # 테스트용 로거 생성
    log = logging.getLogger("uvicorn.access")
    log.info("정상적으로 JSON 로그가 출력됩니다.")