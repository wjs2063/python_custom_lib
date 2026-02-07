import logging
import datetime
from apscheduler.schedulers.blocking import BlockingScheduler

# 1. 간단한 로깅 설정 (사용자의 root.py 설정을 불러와도 됩니다)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger("token_worker")

# 2. 실행할 작업 정의
def refresh_token_job(arg1, arg2):
    now = datetime.datetime.now()
    logger.info(f"[{now}] 토큰 갱신 작업을 수행합니다. (인자: {arg1}, {arg2})")


scheduler = BlockingScheduler()

# 4. 작업 등록 (interval 방식)
# - minutes=50: 50분마다 실행
# - next_run_time: 생성 즉시(now) 실행하도록 설정 (이게 없으면 50분 뒤에 첫 실행됨)
# - args: 작업 함수에 넘길 파라미터
scheduler.add_job(
    func=refresh_token_job,
    trigger='interval',
    seconds=5000,
    next_run_time=datetime.datetime.now(),
    args=["service_a", "v1"],
    id="token_refresh_001" # 작업 식별자 (관리용)
)

scheduler.start()
