from atlassian import Confluence
from dotenv import load_dotenv
import os
import json
load_dotenv(verbose=True)

email = os.getenv("EMAIL")
confluence_email = os.getenv('CONFLUENCE_EMAIL')
api_token = os.getenv("CONFLUENCE_API_TOKEN")

confluence = Confluence(
    url=f'https://{email}.atlassian.net',
    username=confluence_email,
    password=api_token)




def get_standalone_redoc():
    # 1. openapi.json 파일 로드
    with open("openapi.json", "r", encoding="utf-8") as f:
        openapi_data = json.load(f)

    # 2. JSON 데이터를 자바스크립트용으로 직렬화 (한글 보존)
    spec_json = json.dumps(openapi_data, ensure_ascii=False)

    # 3. HTML 매크로 스토리지 포맷 생성
    # 설정을 최소화하여 Redoc 기본 엔진으로 렌더링합니다.
    full_html = f"""
    <ac:structured-macro ac:name="html" ac:schema-version="1">
      <ac:parameter ac:name="atlassian-macro-output-type">BLOCK</ac:parameter>
      <ac:plain-text-body>
        <![CDATA[
        <div id="redoc-container"></div>

        <script src="https://cdn.jsdelivr.net/npm/redoc@latest/bundles/redoc.standalone.js"></script>

        <script>
          (function() {{
            const spec = {spec_json};

            // 다른 옵션 없이 기본 초기화
            Redoc.init(spec, {{}}, document.getElementById('redoc-container'));
          }})();
        </script>
        ]]>
      </ac:plain-text-body>
    </ac:structured-macro>
    """
    return full_html

def update_docs(page_id:int):
    # 새 HTML 내용 생성
    new_html = get_standalone_redoc()

    # 현재 페이지의 제목을 가져옴 (제목 유지 목적)
    page_details = confluence.get_page_by_id(page_id)
    title = page_details['title']

    # 2. 페이지 업데이트 (라이브러리가 내부적으로 버전을 체크하고 +1 해서 올림)
    status = confluence.update_page(
        page_id=page_id,
        title=title,
        body=new_html,
        parent_id=None,
        type='page',
        representation='storage',
        always_update=True
    )

    if 'id' in status:
        print(f"성공: 컨플루언스 페이지가 업데이트되었습니다. (ID: {status['id']})")
    else:
        print("실패: 업데이트에 실패했습니다.")

update_docs(65855)