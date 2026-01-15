import streamlit as st
import re
import time
import urllib.parse
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# --- 1. 페이지 설정 ---
st.set_page_config(page_title="베리굿 블로그 판독기", page_icon="🍫")

st.title("🍫 베리굿 블로그 판독기")
st.write("네이버 블로그 ID를 입력하면 '방문자 수'와 '검색 노출 여부'를 판단해줍니다.")

# --- 2. 핵심 도구: 서버용 크롬 드라이버 설정 ---
@st.cache_resource
def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1")
    
    # [중요] Streamlit Cloud 서버 경로 강제 지정 (packages.txt가 설치한 경로)
    possible_paths = [
        "/usr/bin/chromium", 
        "/usr/bin/chromium-browser",
        "/usr/bin/google-chrome-stable"
    ]
    
    binary_location = None
    for path in possible_paths:
        if os.path.exists(path):
            binary_location = path
            break
            
    if binary_location:
        chrome_options.binary_location = binary_location
    
    # 드라이버 생성 시도
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except:
        driver = webdriver.Chrome(options=chrome_options)
        
    return driver

# --- 3. 기능 함수들 (John이 가져온 로직 그대로 활용) ---

def parse_visitor_text(text: str) -> tuple:
    today = "0"
    total = "0"
    try:
        numbers = re.findall(r'[\d,]+', text)
        if len(numbers) >= 2:
            today = numbers[0]
            total = numbers[1]
        elif len(numbers) == 1:
            if "오늘" in text: today = numbers[0]
            elif "전체" in text: total = numbers[0]
    except:
        pass
    return today, total

def get_blog_info(blog_id):
    driver = get_driver()
    result = {
        "today_visitors": "확인 불가",
        "total_visitors": "확인 불가", 
        "latest_post_title": "글 없음"
    }
    
    try:
        url = f"https://m.blog.naver.com/{blog_id}"
        driver.get(url)
        time.sleep(2)
        
        # 방문자 수 찾기 (여러 선택자 시도)
        visitor_selectors = ["div[class^='count__']", "div[class*='count']", ".count.total"]
        for selector in visitor_selectors:
            try:
                elem = driver.find_element(By.CSS_SELECTOR, selector)
                text = elem.text.strip()
                if "오늘" in text or "전체" in text:
                    result["today_visitors"], result["total_visitors"] = parse_visitor_text(text)
                    break
            except:
                continue
                
        # 제목 찾기
        title_selectors = ["strong.title", ".postlist .title", "span.title", ".tit_wrap .title"]
        for selector in title_selectors:
            try:
                elem = driver.find_element(By.CSS_SELECTOR, selector)
                text = elem.text.strip()
                if text:
                    result["latest_post_title"] = text
                    break
            except:
                continue
                
    except Exception as e:
        st.error(f"블로그 접속 중 에러: {e}")
        
    return result

def check_search_exposure(blog_id, post_title):
    if post_title == "글 없음" or not post_title:
        return False, "제목이 없어서 검색 불가"
        
    driver = get_driver()
    try:
        encoded_query = urllib.parse.quote(f'"{post_title}"') # 정확도를 위해 따옴표 추가
        search_url = f"https://m.search.naver.com/search.naver?where=m_view&query={encoded_query}"
        
        driver.get(search_url)
        time.sleep(2)
        
        # 페이지 소스에서 내 블로그 아이디 찾기 (가장 확실한 방법)
        page_source = driver.page_source
        if blog_id in page_source:
            # 상단에 있는지 대략적 확인 (뷰탭 구조상 정확한 순위는 복잡하지만, 상단 노출 여부는 파악 가능)
            return True, "검색 결과 상단 노출 중! (합격)"
        else:
            return False, "검색 결과 1페이지에 없음 (주의)"
            
    except Exception as e:
        return False, f"검색 중 에러: {e}"

# --- 4. 메인 화면 (사용자 입력 부분) ---

blog_id_input = st.text_input("조회할 블로그 ID", placeholder="예: nam9295")

if st.button("분석 시작 🚀", type="primary"):
    if not blog_id_input:
        st.warning("아이디를 입력해주세요!")
    else:
        with st.spinner(f"'{blog_id_input}' 님의 블로그를 샅샅이 뒤지는 중..."):
            # 1. 블로그 정보 가져오기
            info = get_blog_info(blog_id_input)
            
            # 2. 결과 보여주기
            st.divider()
            col1, col2 = st.columns(2)
            col1.metric("오늘 방문자", info["today_visitors"])
            col1.metric("전체 방문자", info["total_visitors"])
            
            st.info(f"📝 최신 글: {info['latest_post_title']}")
            
            # 3. 검색 노출 테스트 (제목이 있을 때만)
            if info['latest_post_title'] != "글 없음":
                is_exposed, msg = check_search_exposure(blog_id_input, info['latest_post_title'])
                
                if is_exposed:
                    st.success(f"✅ {msg}")
                    st.balloons() # 축하 풍선!
                else:
                    st.error(f"❌ {msg}")
                    st.write("👉 이 블로그는 최신 글이 검색에 반영되지 않고 있습니다.")