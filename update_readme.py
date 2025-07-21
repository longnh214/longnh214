import requests
from bs4 import BeautifulSoup
import re
import os
from datetime import datetime, timezone, timedelta


BLOG_URL = "https://longnh214.github.io/"

README_PATH = "README.md"

KST = timezone(timedelta(hours=9))


def get_latest_posts(url, num_posts=5):
    """
    블로그 URL에서 최신 포스트 목록(제목, 링크, 날짜)을 가져옵니다.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"블로그 접속 오류: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    posts = []
    
    post_cards = soup.find_all('article', class_='card-wrapper card')

    for card in post_cards:
        link_tag = card.find('a', class_='post-preview')
        link = link_tag.get('href') if link_tag else None

        if link and not link.startswith('http'):
            link = os.path.join(BLOG_URL, link.lstrip('/')).replace('\\', '/')

        title_tag = card.find('h1', class_='card-title')
        title = title_tag.get_text(strip=True) if title_tag else None

        date_tag = card.find('time')
        date_str = None
        if date_tag and 'data-ts' in date_tag.attrs:
            timestamp = int(date_tag['data-ts'])
            # 👉 KST로 변환하여 날짜 표시
            date_str = datetime.fromtimestamp(timestamp, tz=KST).strftime('%Y-%m-%d')
        elif date_tag:
            date_str = date_tag.get_text(strip=True)

        if title and link and date_str and link.startswith(BLOG_URL):
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
        print(f"ERROR: {README_PATH} 파일을 찾을 수 없습니다.")
        return

    start_marker = "---"
    end_marker = "---"

    if start_marker not in readme_content or end_marker not in readme_content:
        print(f"ERROR: {start_marker} 또는 {end_marker} 마커를 {README_PATH}에서 찾을 수 없습니다.")
        print("README.md에 마커를 추가해주세요.")
        return

    new_posts_content = [
        f"- [{title}]({link}) [{date_str}]" for title, link, date_str in posts
    ]
    new_posts_text = "\n".join(new_posts_content)

    updated_readme = re.sub(
        f'{start_marker}.*?{end_marker}',
        f'{start_marker}\n{new_posts_text}\n{end_marker}',
        readme_content,
        flags=re.DOTALL
    )

    if updated_readme == readme_content:
        print("README.md 내용에 변경 사항이 없습니다. 업데이트 건너뜁니다.")
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
