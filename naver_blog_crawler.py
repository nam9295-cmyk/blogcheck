import streamlit as st
import re
import time
import urllib.parse
import os
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# --- 1. 페이지 기본 설정 ---
st.set_page_config(page_title="베리굿 블로그 판독기", page_icon="🍫")

# --- 브랜드 컬러 스타일링 (#edc5c4 인디 핑크) ---
st.markdown("""
<style>
    /* 전체 배경 */
    .stApp {
        background: linear-gradient(180deg, #0E1117 0%, #1A1D24 100%);
    }
    
    /* 모든 텍스트 색상 - 인디 핑크 */
    h1, h2, h3, h4, h5, h6 {
        color: #edc5c4 !important;
        font-weight: 700 !important;
    }
    
    p, span, label, div {
        color: #edc5c4 !important;
    }
    
    /* 메트릭 카드 스타일 */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #262730 0%, #1E1E2E 100%);
        border: 1px solid #edc5c4;
        border-radius: 12px;
        padding: 20px 15px;
        box-shadow: 0 4px 15px rgba(237, 197, 196, 0.15);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    div[data-testid="stMetric"]:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 20px rgba(237, 197, 196, 0.25);
    }
    
    div[data-testid="stMetric"] label {
        color: #edc5c4 !important;
        font-size: 0.9rem !important;
    }
    
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #edc5c4 !important;
        font-size: 1.8rem !important;
        font-weight: 700 !important;
    }
    
    /* 버튼 스타일 - 인디 핑크 배경, 검정 글씨 */
    button[kind="primary"], .stButton > button {
        background: #edc5c4 !important;
        color: #000000 !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
        padding: 12px 20px !important;
        box-shadow: 0 4px 15px rgba(237, 197, 196, 0.4) !important;
        transition: all 0.3s ease !important;
    }
    
    button[kind="primary"]:hover, .stButton > button:hover {
        background: #d4a8a7 !important;
        color: #000000 !important;
        box-shadow: 0 6px 20px rgba(237, 197, 196, 0.6) !important;
        transform: translateY(-2px) !important;
    }
    
    /* 인풋 필드 스타일 */
    input[type="text"] {
        background-color: #262730 !important;
        border: 1px solid #edc5c4 !important;
        border-radius: 8px !important;
        color: #edc5c4 !important;
        padding: 12px !important;
    }
    
    input[type="text"]:focus {
        border-color: #edc5c4 !important;
        box-shadow: 0 0 0 2px rgba(237, 197, 196, 0.3) !important;
    }
    
    input[type="text"]::placeholder {
        color: #a08887 !important;
    }
    
    /* 정보 박스 스타일 */
    div[data-testid="stAlert"] {
        background-color: #1E1E2E !important;
        border-radius: 10px !important;
        border-left: 4px solid #edc5c4 !important;
    }
    
    /* 구분선 스타일 */
    hr {
        border-color: #edc5c4 !important;
        opacity: 0.3;
    }
    
    /* 성공/경고/에러 메시지 */
    .stSuccess > div {
        color: #edc5c4 !important;
    }
    
    .stWarning > div {
        color: #edc5c4 !important;
    }
    
    .stError > div {
        color: #edc5c4 !important;
    }
    
    /* 스피너 색상 */
    .stSpinner > div {
        border-top-color: #edc5c4 !important;
    }
    
    /* 폼 컨테이너 */
    div[data-testid="stForm"] {
        background: #1A1D24;
        border: 1px solid #edc5c4;
        border-radius: 15px;
        padding: 20px;
    }
    
    /* 로고 중앙 정렬 */
    .logo-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        margin-bottom: 20px;
    }
    
    /* 제목 줄바꿈 방지 */
    .main-title {
        white-space: nowrap;
        font-size: 2rem !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 로고 및 타이틀 ---
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    st.image("logo.png", width=200, use_container_width=False)


st.markdown("""
<h1 style='text-align: center; color: #edc5c4; font-size: 2.2rem; white-space: nowrap; margin-top: -10px;'>
베리굿 블로그 판독기
</h1>
<p style='text-align: center; color: #edc5c4; margin-top: 10px;'>
<b>[정밀 분석기]</b> 네이버 블로그 ID를 입력하면<br>
<b>방문자 수, 최신글 상세 분석, 검색 노출 상태</b>까지 한눈에 볼 수 있어요!
</p>
""", unsafe_allow_html=True)

# --- 2. 서버용 강력한 드라이버 설정 ---
@st.cache_resource
def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1")
    
    # 서버 경로 강제 지정
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
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except:
        driver = webdriver.Chrome(options=chrome_options)
        
    return driver

# --- 3. 유틸리티 함수들 ---
def parse_visitor_text(text):
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

def parse_date(date_text):
    try:
        clean_text = date_text.replace(" ", "").strip(".")
        parts = clean_text.split(".")
        if len(parts) >= 3:
            year = int(parts[0])
            month = int(parts[1])
            day = int(parts[2]) if parts[2] else 1
            return datetime(year, month, day)
    except:
        pass
    return None

def is_within_one_month(date_obj):
    if not date_obj: return False
    one_month_ago = datetime.now() - timedelta(days=30)
    return date_obj >= one_month_ago

# --- 4. 블로그 기본 정보 가져오기 ---
def get_blog_info(blog_id):
    driver = get_driver()
    result = {
        "today_visitors": "확인 불가",
        "total_visitors": "확인 불가", 
        "latest_post_title": "글 없음",
        "latest_post_url": None
    }
    
    try:
        url = f"https://m.blog.naver.com/{blog_id}"
        driver.get(url)
        time.sleep(2.5)
        
        # 방문자 수
        visitor_selectors = [".count.total", "div[class^='count__']", ".count"]
        for selector in visitor_selectors:
            try:
                elem = driver.find_element(By.CSS_SELECTOR, selector)
                text = elem.text.strip()
                if "오늘" in text or "전체" in text:
                    result["today_visitors"], result["total_visitors"] = parse_visitor_text(text)
                    break
            except:
                continue
        
        # 최신글 URL 찾기
        post_selectors = ["strong[class*='title__']", ".list_post_article a.title", "a.title"]
        for selector in post_selectors:
            try:
                elem = driver.find_element(By.CSS_SELECTOR, selector)
                title = elem.text.strip()
                href = elem.get_attribute("href")
                if not href:
                    parent = elem.find_element(By.XPATH, "./ancestor::a")
                    href = parent.get_attribute("href")
                
                if title and len(title) > 2 and "사진 개수" not in title:
                    if href and blog_id in href:
                        result["latest_post_title"] = title
                        result["latest_post_url"] = href
                        break
            except:
                continue
                
    except Exception as e:
        print(f"Error: {e}")
        
    return result

# --- 5. 상세 페이지 분석 (iframe 대응) ---
def analyze_post_detail(post_url):
    driver = get_driver()
    result = {
        "publish_date": "확인 불가",
        "publish_date_obj": None,
        "char_count": 0,
        "image_count": 0,
        "like_count": "0",
        "comment_count": "0"
    }
    
    if not post_url: return result
    is_in_iframe = False
    
    try:
        driver.get(post_url)
        time.sleep(3)
        
        # iframe 진입
        try:
            driver.switch_to.frame("mainFrame")
            is_in_iframe = True
            time.sleep(1)
        except:
            pass
        
        # 날짜 찾기
        date_selectors = [".se_publishDate", ".blog_date", ".date", ".fil5", "span[class*='date']"]
        for selector in date_selectors:
            try:
                elem = driver.find_element(By.CSS_SELECTOR, selector)
                date_text = elem.text.strip()
                if date_text:
                    result["publish_date"] = date_text
                    result["publish_date_obj"] = parse_date(date_text)
                    break
            except:
                continue
                
        # 본문 내용 (글자 수)
        try:
            content = driver.find_element(By.CSS_SELECTOR, ".se-main-container")
            text = content.text.strip()
        except:
            try:
                content = driver.find_element(By.CSS_SELECTOR, "#postViewArea")
                text = content.text.strip()
            except:
                text = ""
                try:
                    text = driver.find_element(By.TAG_NAME, "body").text
                except: pass

        result["char_count"] = len(text.replace(" ", "").replace("\n", ""))
        
        # 이미지 개수 (정밀 필터링 + 네이버 도메인 대응)
        try:
            if is_in_iframe:
                imgs = driver.find_elements(By.TAG_NAME, "img")
            else:
                imgs = driver.find_elements(By.CSS_SELECTOR, ".se-main-container img")
                if not imgs:
                    imgs = driver.find_elements(By.TAG_NAME, "img")
                
            valid_cnt = 0
            for img in imgs:
                src = img.get_attribute("src") or img.get_attribute("data-src") or ""
                cls = img.get_attribute("class") or ""
                
                # 제외: 스티커, 아이콘, 프로필
                if "sticker" in cls or "icon" in cls or "profile" in cls: continue
                if "l.blog.naver" in src: continue  # 좋아요 아이콘
                
                # 네이버 본문 이미지 도메인 체크
                valid_domains = ["postfiles", "blogfiles", "pstatic.net", "naver.net", "blogpfthumb"]
                if any(d in src for d in valid_domains):
                    valid_cnt += 1
            result["image_count"] = valid_cnt
        except:
            pass
            
        # 공감 수
        try:
            like = driver.find_element(By.CSS_SELECTOR, "em[class*='u_cnt']").text
            result["like_count"] = like
        except: pass
        
        # 댓글 수
        try:
            cmt = driver.find_element(By.CSS_SELECTOR, "em[class*='_count']").text
            result["comment_count"] = cmt
        except: pass

    except Exception as e:
        print(e)
    finally:
        if is_in_iframe:
            try: driver.switch_to.default_content()
            except: pass
            
    return result

# --- 6. 검색 노출 확인 (★ 엄격 모드 - 핵심 키워드만 검색) ---
def check_search_exposure(blog_id, post_title):
    if not post_title or post_title == "글 없음":
        return False, "제목 없음"
        
    driver = get_driver()
    try:
        # ★ 핵심 키워드만 추출 (처음 2~3단어만 사용해서 실제 경쟁력 테스트)
        clean_title = re.sub(r'[^\w\s가-힣]', ' ', post_title).strip()
        words = clean_title.split()
        
        # 의미 없는 단어 제거
        stopwords = ["더", "그", "이", "저", "및", "등", "를", "을", "의", "에", "로", "나", "하다", "하는", "합니다"]
        keywords = [w for w in words if w not in stopwords and len(w) > 1]
        
        # 핵심 키워드 2~3개만 사용 (너무 특정적이면 1위 뜨는 건 당연)
        if len(keywords) > 3:
            keywords = keywords[:3]
        
        search_query = " ".join(keywords)
        if not search_query:
            search_query = clean_title[:20]  # 폴백
            
        encoded_query = urllib.parse.quote(search_query)
        
        # VIEW 탭 기준 검색
        search_url = f"https://m.search.naver.com/search.naver?where=m_view&query={encoded_query}"
        driver.get(search_url)
        time.sleep(2)
        
        # 상위 검색 결과에서 블로그 링크 가져오기
        result_links = driver.execute_script("""
            var links = [];
            var allLinks = document.querySelectorAll('a[href*="blog.naver.com"]');
            for(var i=0; i<allLinks.length && links.length < 20; i++){
                var href = allLinks[i].href;
                if(href && !href.includes('ad.search') && !href.includes('ader.naver')){
                    if(links.indexOf(href) === -1) links.push(href);
                }
            }
            return links;
        """)
        
        if not result_links:
            if blog_id in driver.page_source:
                return False, "⚠️ 검색은 되나 상위권 아님"
            return False, "❌ 검색 결과 없음"
        
        # 순위 판독 (엄격 기준)
        for i, link in enumerate(result_links):
            if f"blog.naver.com/{blog_id}" in link:
                rank = i + 1
                if rank == 1:
                    return True, f"🏅 1위! 키워드({search_query}) 최적화"
                elif rank <= 3:
                    return True, f"✅ {rank}위 - 경쟁력 있음"
                elif rank <= 10:
                    return False, f"⚠️ {rank}위 - 상위권 진입 필요"
                else:
                    return False, f"❌ {rank}위 - 노출 약함"
                    
        return False, f"❌ 20위권 밖 (키워드: {search_query})"
        
    except Exception as e:
        return False, f"에러: {e}"

# --- 7. UI 구성 ---
def extract_blog_id(text):
    if not text: return ""
    if "blog.naver.com" in text:
        parts = text.split("/")
        for p in parts:
            if p and "http" not in p and "blog.naver" not in p:
                return p
    return text

st.divider()

with st.form("main_form"):
    user_input = st.text_input("🔍 블로그 ID 또는 주소 입력", placeholder="예: nam9295")
    submitted = st.form_submit_button("분석 시작 🚀", type="primary", use_container_width=True)

if submitted and user_input:
    blog_id = extract_blog_id(user_input)
    
    with st.spinner(f"'{blog_id}' 정밀 분석 중..."):
        info = get_blog_info(blog_id)
        
        st.divider()
        c1, c2 = st.columns(2)
        c1.metric("오늘 방문자", info["today_visitors"])
        c2.metric("전체 방문자", info["total_visitors"])
        
        if info['latest_post_url']:
            detail = analyze_post_detail(info['latest_post_url'])
            
            st.subheader("📝 최신글 분석")
            st.info(f"제목: {info['latest_post_title']}")
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("발행일", detail["publish_date"])
            c2.metric("글자수", f"{detail['char_count']:,}")
            c3.metric("이미지", detail["image_count"])
            c4.metric("공감", detail["like_count"])
            
            # 품질 판독
            warns = []
            if detail['char_count'] < 1000: warns.append("글자 수 부족 (1,000자 미만)")
            if detail['image_count'] < 5: warns.append("이미지 부족 (5장 미만)")
            if not is_within_one_month(detail['publish_date_obj']): warns.append("최근 활동 뜸함")
            
            if warns:
                for w in warns: st.warning(f"⚠️ {w}")
            else:
                st.success("✅ 블로그 품질 합격점!")
                
            # 검색 노출 (엄격)
            st.divider()
            is_good, msg = check_search_exposure(blog_id, info['latest_post_title'])
            if is_good:
                if "최적화" in msg:
                    st.success(msg)
                    st.balloons()
                else:
                    st.warning(msg)
            else:
                st.error(msg)
                
        else:
            st.warning("최신 글을 찾지 못했습니다.")