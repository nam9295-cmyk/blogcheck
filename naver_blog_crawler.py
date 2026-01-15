"""
네이버 블로그 기본 정보 크롤러
- Selenium과 webdriver_manager를 사용하여 네이버 모바일 블로그에서 정보를 추출합니다.
- 최신 글 제목으로 네이버 검색 노출 여부를 확인합니다.
"""

import re
import time
import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


def parse_visitor_text(text: str) -> tuple:
    """
    방문자 수 텍스트를 파싱합니다.
    예: "오늘 1,234 전체 12,345,678" -> ("1,234", "12,345,678")
    
    Args:
        text: 방문자 수 텍스트
        
    Returns:
        (오늘 방문자 수, 전체 방문자 수) 튜플
    """
    today = "정보를 찾을 수 없음"
    total = "정보를 찾을 수 없음"
    
    try:
        # 모든 숫자(콤마 포함)를 추출
        numbers = re.findall(r'[\d,]+', text)
        
        if len(numbers) >= 2:
            # "오늘 X 전체 Y" 형식 - 첫 번째가 오늘, 두 번째가 전체
            today = numbers[0]
            total = numbers[1]
        elif len(numbers) == 1:
            # 숫자가 하나만 있는 경우
            if "오늘" in text:
                today = numbers[0]
            elif "전체" in text:
                total = numbers[0]
    except Exception:
        pass
    
    return today, total


def create_driver():
    """Selenium WebDriver를 생성합니다."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1")
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)


def get_blog_info(blog_id: str) -> dict:
    """
    네이버 블로그에서 기본 정보를 크롤링합니다.
    
    Args:
        blog_id: 네이버 블로그 ID
        
    Returns:
        블로그 정보가 담긴 딕셔너리
    """
    driver = create_driver()
    
    result = {
        "blog_id": blog_id,
        "total_visitors": "정보를 찾을 수 없음",
        "today_visitors": "정보를 찾을 수 없음",
        "latest_post_title": "정보를 찾을 수 없음"
    }
    
    try:
        url = f"https://m.blog.naver.com/{blog_id}"
        driver.get(url)
        time.sleep(3)
        
        # 방문자 수 추출 - 다양한 선택자 시도
        visitor_selectors = [
            "div[class^='count__']",
            "div[class*='count']",
            "span[class^='count__']",
            "span[class*='count']",
        ]
        
        for selector in visitor_selectors:
            try:
                visitor_element = driver.find_element(By.CSS_SELECTOR, selector)
                visitor_text = visitor_element.text.strip()
                if "오늘" in visitor_text or "전체" in visitor_text:
                    result["today_visitors"], result["total_visitors"] = parse_visitor_text(visitor_text)
                    break
            except Exception:
                continue
        
        # XPath 폴백
        if result["today_visitors"] == "정보를 찾을 수 없음":
            try:
                visitor_element = driver.find_element(By.XPATH, "//*[contains(text(), '오늘') or contains(text(), '전체')]")
                visitor_text = visitor_element.text.strip()
                result["today_visitors"], result["total_visitors"] = parse_visitor_text(visitor_text)
            except Exception:
                pass
        
        # 최신 게시글 제목 추출 - 다양한 선택자 시도
        title_selectors = [
            "strong.title",
            "span.title",
            ".title",
            "div[class^='list__'] strong[class^='title__']",
            "div[class^='list__'] span[class^='title__']",
            "div[class^='list__'] [class^='title__']",
            "[class^='title__']",
            "a[class*='title']",
            ".post_title",
            ".tit_wrap .title",
            ".list_post_article .title",
        ]
        
        for selector in title_selectors:
            try:
                title_element = driver.find_element(By.CSS_SELECTOR, selector)
                title_text = title_element.text.strip()
                if title_text and len(title_text) > 0:
                    result["latest_post_title"] = title_text
                    break
            except Exception:
                continue
        
        # XPath 폴백 - 게시글 목록에서 첫 번째 제목 찾기
        if result["latest_post_title"] == "정보를 찾을 수 없음":
            try:
                # 제목에 해당하는 strong 또는 span 요소 찾기
                title_element = driver.find_element(By.XPATH, "//strong[contains(@class, 'title')] | //span[contains(@class, 'title')]")
                title_text = title_element.text.strip()
                if title_text:
                    result["latest_post_title"] = title_text
            except Exception:
                pass
    
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
    
    finally:
        driver.quit()
    
    return result


def check_search_exposure(blog_id: str, post_title: str) -> tuple:
    """
    네이버 검색에서 블로그 글의 노출 여부를 확인합니다.
    
    Args:
        blog_id: 블로그 ID
        post_title: 검색할 게시글 제목
        
    Returns:
        (노출 여부, 순위 또는 메시지) 튜플
    """
    if post_title == "정보를 찾을 수 없음" or not post_title:
        return False, "게시글 제목을 찾을 수 없어 검색할 수 없습니다."
    
    driver = create_driver()
    
    try:
        # 네이버 검색 URL 생성
        encoded_query = urllib.parse.quote(post_title)
        search_url = f"https://m.search.naver.com/search.naver?where=m_view&query={encoded_query}"
        
        driver.get(search_url)
        time.sleep(3)
        
        # 스크롤해서 동적 콘텐츠 로딩
        driver.execute_script("window.scrollTo(0, 500);")
        time.sleep(2)
        
        # JavaScript로 모든 링크 추출 (렌더링된 DOM에서)
        try:
            all_links = driver.execute_script("""
                var links = [];
                var anchors = document.querySelectorAll('a[href*="blog.naver.com"]');
                anchors.forEach(function(a) {
                    if (a.href && a.href.includes('blog.naver.com')) {
                        links.push(a.href);
                    }
                });
                return links;
            """)
        except Exception:
            all_links = []
        
        # 광고 링크 제외
        blog_links = [
            link for link in all_links 
            if 'ader.naver.com' not in link 
            and 'ad.search.naver.com' not in link
            and 'm.blog.naver.com' in link
        ]
        
        # 중복 제거하면서 순서 유지
        seen = set()
        unique_links = []
        for link in blog_links:
            if link not in seen:
                seen.add(link)
                unique_links.append(link)
        
        # 상위 5개에서 해당 블로그 ID 확인
        for i, link in enumerate(unique_links[:5]):
            if blog_id in link:
                return True, i + 1  # 순위 반환 (1-indexed)
        
        # 백업: 페이지 소스에서 직접 검색
        page_source = driver.page_source
        
        # 블로그 ID가 포함된 링크 패턴 검색
        blog_pattern = rf'blog\.naver\.com/{re.escape(blog_id)}'
        if re.search(blog_pattern, page_source):
            # 해당 블로그가 페이지에 존재함 -> 순위 계산
            # 모든 블로그 링크 찾기
            all_blog_matches = re.findall(r'm\.blog\.naver\.com/([a-zA-Z0-9_-]+)/\d+', page_source)
            # 중복 제거하면서 순서 유지
            seen_ids = []
            for bid in all_blog_matches:
                if bid not in seen_ids:
                    seen_ids.append(bid)
            
            # 해당 블로그 ID의 순위 찾기
            for i, bid in enumerate(seen_ids[:5]):
                if bid == blog_id:
                    return True, i + 1
            
            # 5위 밖이지만 페이지에 있음
            if blog_id in seen_ids:
                rank = seen_ids.index(blog_id) + 1
                if rank > 5:
                    return False, f"상위 5개 밖 ({rank}위)"
        
        return False, "상위 5개 결과에 블로그가 없습니다."
    
    except Exception as e:
        return False, f"검색 오류: {e}"
    
    finally:
        driver.quit()


def print_blog_info(info: dict, exposure_result: tuple = None) -> None:
    """
    블로그 정보를 보기 좋게 출력합니다.
    
    Args:
        info: 블로그 정보 딕셔너리
        exposure_result: 검색 노출 결과 튜플 (노출여부, 순위/메시지)
    """
    print("\n" + "=" * 50)
    print("📊 네이버 블로그 기본 정보")
    print("=" * 50)
    print(f"🔹 블로그 ID      : {info['blog_id']}")
    print(f"🔹 전체 방문자 수  : {info['total_visitors']}")
    print(f"🔹 오늘 방문자 수  : {info['today_visitors']}")
    print(f"🔹 최신 게시글    : {info['latest_post_title']}")
    print("=" * 50)
    
    # 검색 노출 결과 출력
    if exposure_result:
        print("\n" + "-" * 50)
        print("🔍 검색 노출 판독 결과")
        print("-" * 50)
        is_exposed, rank_or_msg = exposure_result
        if is_exposed:
            print(f"✅ 노출 잘됨 (합격) - 검색 결과 {rank_or_msg}위")
        else:
            print(f"❌ 노출 안됨 (주의 요망) - {rank_or_msg}")
        print("-" * 50)
    
    print()


def main():
    """메인 함수"""
    print("\n🌐 네이버 블로그 기본 정보 크롤러 + 불량 판독기")
    print("-" * 50)
    print("💡 종료하려면 'q' 또는 'quit'을 입력하세요.\n")
    
    while True:
        # 사용자로부터 블로그 ID 입력받기
        blog_id = input("📝 조회할 블로그 ID를 입력하세요: ").strip()
        
        # 종료 명령어 확인
        if blog_id.lower() in ['q', 'quit']:
            print("\n👋 프로그램을 종료합니다. 감사합니다!")
            break
        
        if not blog_id:
            print("❌ 블로그 ID가 입력되지 않았습니다. 다시 입력해주세요.\n")
            continue
        
        print(f"\n🔍 '{blog_id}' 블로그 정보를 가져오는 중...")
        
        # 블로그 정보 가져오기
        info = get_blog_info(blog_id)
        
        # 검색 노출 확인
        exposure_result = None
        if info["latest_post_title"] != "정보를 찾을 수 없음":
            print(f"🔎 '{info['latest_post_title']}' 검색 노출 확인 중...")
            exposure_result = check_search_exposure(blog_id, info["latest_post_title"])
        
        # 결과 출력
        print_blog_info(info, exposure_result)
        
        # 구분선 출력 (다음 조회와 구분)
        print("\n" + "-" * 50)
        print("-" * 50 + "\n")


if __name__ == "__main__":
    main()
