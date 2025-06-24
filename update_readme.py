import requests
from bs4 import BeautifulSoup
import re
import os
from datetime import datetime

# GitHub 블로그 URL 설정 (당신의 블로그 URL로 변경하세요!)
# 예: "https://your-username.github.io/your-blog-repo/"
# 또는 사용자 페이지라면 "https://your-username.github.io/"
BLOG_URL = "https://longnh214.github.io/"

# GitHub Special Repository의 README.md 경로 (예: GitHub 프로필 README)
# 이 스크립트는 GitHub Actions에서 실행되므로, 현재 워크스페이스의 README.md를 타겟팅합니다.
README_PATH = "README.md"

def get_latest_posts(url, num_posts=5):
    """
    블로그 URL에서 최신 포스트 목록(제목, 링크, 날짜)을 가져옵니다.
    """
    try:
        response = requests.get(url)
        response.raise_for_status() # HTTP 오류 발생 시 예외 발생
    except requests.exceptions.RequestException as e:
        print(f"블로그 접속 오류: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')

    posts = []
    # 각 포스트는 <article class="card-wrapper card">로 묶여 있다고 가정
    # 이 요소를 찾아서 반복합니다.
    post_cards = soup.find_all('article', class_='card-wrapper card')

    for card in post_cards:
        # 1. 링크 추출: <a href="/posts/Java_String/" ...>
        link_tag = card.find('a', class_='post-preview')
        link = link_tag.get('href') if link_tag else None

        # 상대 경로를 절대 경로로 변환
        if link and not link.startswith('http'):
            # os.path.join을 사용하여 깔끔하게 경로 조합
            # replace('\\', '/')는 Windows 환경에서 경로 구분자가 \로 나오는 것을 방지
            link = os.path.join(BLOG_URL, link.lstrip('/')).replace('\\', '/')

        # 2. 제목 추출: <h1 class="card-title ..."> 아래의 텍스트
        title_tag = card.find('h1', class_='card-title')
        title = title_tag.get_text(strip=True) if title_tag else None

        # 3. 날짜 추출: <time data-ts="..." data-df="ll"> 날짜 </time>
        date_tag = card.find('time')
        date_str = None
        if date_tag and 'data-df' in date_tag.attrs:
            # data-ts가 Unix timestamp (epoch time)이므로 이를 활용
            timestamp = int(date_tag['data-ts'])
            # datetime 객체로 변환 후 원하는 형식으로 포매팅 (예: YYYY-MM-DD)
            date_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
        elif date_tag:
            # data-ts가 없을 경우, 태그의 텍스트에서 직접 날짜 추출 시도
            # 예: "May 14, 2025" -> 2025-05-14 (추가 파싱 로직 필요)
            # 여기서는 data-ts가 있다고 가정하고 진행합니다.
            date_str = date_tag.get_text(strip=True)


        if title and link and date_str and link.startswith(BLOG_URL):
            # 중복 방지를 위해 (제목, 링크, 날짜) 튜플로 저장
            if (title, link, date_str) not in posts:
                posts.append((title, link, date_str))
        
        if len(posts) >= num_posts:
            break
            
    return posts[:num_posts]

def update_readme(posts):
    """
    README.md 파일의 특정 섹션을 최신 포스트 목록으로 업데이트합니다.
    제목과 날짜를 조합하여 표시합니다.
    """
    try:
        with open(README_PATH, 'r', encoding='utf-8') as f:
            readme_content = f.read()
    except FileNotFoundError:
        print(f"ERROR: {README_PATH} 파일을 찾을 수 없습니다. GitHub Actions에서 올바른 경로를 확인하세요.")
        return

    start_marker = ""
    end_marker = ""

    if start_marker not in readme_content or end_marker not in readme_content:
        print(f"ERROR: {start_marker} 또는 {end_marker} 마커를 {README_PATH}에서 찾을 수 없습니다.")
        print("README.md에 마커를 추가해주세요.")
        return

    new_posts_content = []
    # 제목 [날짜] 형태로 표시
    for title, link, date_str in posts:
        new_posts_content.append(f"- [{title}]({link}) [{date_str}]") # <-- 날짜 추가
    
    new_posts_text = "\n".join(new_posts_content)

    updated_readme = re.sub(
        f'{start_marker}.*?{end_marker}',
        f'{start_marker}\n{new_posts_text}\n{end_marker}',
        readme_content,
        flags=re.DOTALL
    )

    if updated_readme == readme_content:
        print("README.md 내용에 변경 사항이 없습니다. 업데이트 건너뜝니다.")
        return

    with open(README_PATH, 'w', encoding='utf-8') as f:
        f.write(updated_readme)
    print(f"{len(posts)}개의 최신 포스트로 {README_PATH} 업데이트 완료!")


if __name__ == "__main__":
    print("최신 블로그 포스트 가져오기 시작...")
    latest_posts = get_latest_posts(BLOG_URL, num_posts=5)
    
    if latest_posts:
        print("최신 포스트:", latest_posts)
        update_readme(latest_posts)
    else:
        print("최신 포스트를 가져오지 못했습니다. README.md를 업데이트하지 않습니다.")
