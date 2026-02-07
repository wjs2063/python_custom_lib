import logging
import logging
import traceback
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
# 1. 간단한 로깅 설정 (사용자의 root.py 설정을 불러와도 됩니다)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger("token_worker")

# 2. 실행할 작업 정의
def my_listener(event):
    """작업이 끝날 때마다 호출되는 리스너"""
    if event.exception:
        err_msg = traceback.format_exc()
        logger.error(f"❌ 작업 중 에러 발생: {event.exception}, {err_msg}")
    else:
        # 스케줄러에서 해당 작업을 찾아 다음 실행 시간을 가져옴
        job = scheduler.get_job(event.job_id)
        if job and job.next_run_time:
            next_run = job.next_run_time.strftime('%Y-%m-%d %H:%M:%S')
            logger.info(f"✅ [성공] 토큰 갱신 완료! 다음 실행 시각: {next_run}")

def refresh_token_job():
    # 실제 작업 내용
    raise ValueError("에러")
    logger.info(f"{datetime.now()}, 실행 되었습니다")

if __name__ == "__main__":
    scheduler = BlockingScheduler()

    # 작업 등록
    job_instance = scheduler.add_job(
        refresh_token_job,
        'interval',
        seconds=10,
        id="token_refresh_task",
        next_run_time=datetime.now()
    )

    # 2. 이벤트 리스너 등록 (작업 완료 시 my_listener 실행)
    scheduler.add_listener(my_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

    logger.info("🚀 스케줄러가 가동되었습니다.")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()