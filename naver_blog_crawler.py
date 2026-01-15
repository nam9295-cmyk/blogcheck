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
st.set_page_config(page_title="베리굿 블로그 판독기", page_icon="🍫", layout="wide")

# --- 하이브리드 UI 스타일링 (Input: Hacker / Output: Designer) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@400;600;700&display=swap');
    
    /* ===== 전역 설정 ===== */
    .stApp {
        background: linear-gradient(180deg, #0a0a0a 0%, #0E1117 30%, #1A1D24 100%);
    }
    
    /* Streamlit 기본 요소 숨기기 */
    #MainMenu, footer, header {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* ===== 터미널 입력 영역 스타일 ===== */
    .terminal-header {
        font-family: 'Courier New', monospace;
        color: #edc5c4;
        background: #0a0a0a;
        border: 1px solid #333;
        border-radius: 8px 8px 0 0;
        padding: 8px 15px;
        margin-bottom: 0;
        font-size: 0.75rem;
    }
    
    .terminal-header::before {
        content: "● ● ●";
        color: #555;
        margin-right: 15px;
        letter-spacing: 3px;
    }
    
    .terminal-body {
        font-family: 'Courier New', monospace;
        background: #0a0a0a;
        border: 1px solid #333;
        border-top: none;
        border-radius: 0 0 8px 8px;
        padding: 20px;
        margin-bottom: 30px;
    }
    
    .terminal-log {
        font-family: 'Courier New', monospace;
        color: #4a9c6d;
        font-size: 0.85rem;
        margin-bottom: 5px;
        opacity: 0.8;
    }
    
    .terminal-prompt {
        font-family: 'Courier New', monospace;
        color: #edc5c4;
        font-size: 1rem;
        margin-bottom: 10px;
    }
    
    /* 입력창 - 해커 스타일 */
    div[data-testid="stForm"] {
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
    }
    
    .stTextInput > div > div > input {
        font-family: 'Courier New', monospace !important;
        background: transparent !important;
        border: none !important;
        border-bottom: 2px solid #edc5c4 !important;
        border-radius: 0 !important;
        color: #edc5c4 !important;
        font-size: 1.1rem !important;
        padding: 10px 5px !important;
        caret-color: #edc5c4 !important;
    }
    
    .stTextInput > div > div > input:focus {
        box-shadow: none !important;
        border-bottom: 2px solid #fff !important;
    }
    
    .stTextInput > div > div > input::placeholder {
        color: #666 !important;
        font-family: 'Courier New', monospace !important;
    }
    
    .stTextInput > label {
        display: none !important;
    }
    
    /* 제출 버튼 숨기기 */
    .stFormSubmitButton {
        display: none !important;
    }
    
    /* 깜빡이는 커서 효과 */
    @keyframes blink {
        0%, 50% { opacity: 1; }
        51%, 100% { opacity: 0; }
    }
    
    .cursor-blink {
        display: inline-block;
        width: 10px;
        height: 18px;
        background: #edc5c4;
        animation: blink 1s infinite;
        vertical-align: middle;
        margin-left: 5px;
    }
    
    /* ===== 결과 영역 - 모던 대시보드 스타일 ===== */
    .result-section {
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* 제목 스타일 */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Pretendard', sans-serif !important;
        color: #edc5c4 !important;
        font-weight: 700 !important;
    }
    
    p, span, label, div {
        color: #edc5c4 !important;
    }
    
    /* 메트릭 카드 - 프리미엄 스타일 */
    div[data-testid="stMetric"] {
        background: linear-gradient(145deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid rgba(237, 197, 196, 0.3);
        border-radius: 16px;
        padding: 25px 20px;
        box-shadow: 0 8px 32px rgba(237, 197, 196, 0.1),
                    inset 0 1px 0 rgba(255,255,255,0.05);
        backdrop-filter: blur(10px);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    div[data-testid="stMetric"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px rgba(237, 197, 196, 0.2);
        border-color: rgba(237, 197, 196, 0.5);
    }
    
    div[data-testid="stMetric"] label {
        font-family: 'Pretendard', sans-serif !important;
        color: rgba(237, 197, 196, 0.7) !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        font-family: 'Pretendard', sans-serif !important;
        color: #edc5c4 !important;
        font-size: 2rem !important;
        font-weight: 700 !important;
    }
    
    /* 정보 박스 스타일 */
    div[data-testid="stAlert"] {
        font-family: 'Pretendard', sans-serif !important;
        background: linear-gradient(135deg, rgba(26,26,46,0.9) 0%, rgba(22,33,62,0.9) 100%) !important;
        border-radius: 12px !important;
        border-left: 4px solid #edc5c4 !important;
        backdrop-filter: blur(10px);
    }
    
    /* 구분선 스타일 */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, #edc5c4, transparent);
        margin: 30px 0;
    }
    
    /* 서브헤더 스타일 */
    .dashboard-header {
        font-family: 'Pretendard', sans-serif;
        color: #edc5c4;
        font-size: 1.3rem;
        font-weight: 700;
        margin: 25px 0 15px 0;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .dashboard-header::before {
        content: "";
        width: 4px;
        height: 24px;
        background: #edc5c4;
        border-radius: 2px;
    }
    
    /* 성공/경고/에러 메시지 */
    .stSuccess, .stWarning, .stError, .stInfo {
        font-family: 'Pretendard', sans-serif !important;
    }
    
    /* 스피너 */
    .stSpinner > div {
        border-top-color: #edc5c4 !important;
    }
    
    /* 분석 중 메시지 */
    .analyzing-msg {
        font-family: 'Courier New', monospace;
        color: #4a9c6d;
        font-size: 0.9rem;
        padding: 15px;
        background: #0a0a0a;
        border-radius: 8px;
        border: 1px solid #333;
    }
</style>
""", unsafe_allow_html=True)

# --- 터미널 UI (CSS로 완전 통합) ---
st.markdown("""
<style>
    /* ===== 터미널 컨테이너 시뮬레이션 ===== */
    /* 메인 컨테이너 배경을 터미널처럼 */
    section[data-testid="stMain"] > div > div > div > div:first-child {
        background: #0a0a0a;
        border-radius: 12px;
        border: 1px solid #444;
        padding: 0 !important;
        margin-bottom: 20px;
        overflow: hidden;
        box-shadow: 0 10px 40px rgba(0,0,0,0.5);
    }
    
    /* 터미널 헤더 */
    .term-header {
        background: linear-gradient(180deg, #3a3a3a 0%, #2a2a2a 100%);
        padding: 10px 15px;
        display: flex;
        align-items: center;
        gap: 8px;
        border-bottom: 1px solid #222;
        border-radius: 12px 12px 0 0;
    }
    
    .term-btn {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        display: inline-block;
    }
    .term-btn.red { background: #ff5f56; }
    .term-btn.yellow { background: #ffbd2e; }
    .term-btn.green { background: #27ca40; }
    
    .term-title {
        font-family: 'Courier New', monospace;
        color: #888;
        font-size: 0.8rem;
        margin-left: 10px;
    }
    
    /* 터미널 로그 영역 */
    .term-logs {
        font-family: 'Courier New', monospace;
        padding: 20px;
        background: #0a0a0a;
    }
    
    .term-line {
        color: #4a9c6d;
        font-size: 0.9rem;
        margin-bottom: 4px;
    }
    
    .term-divider {
        color: #edc5c4;
        opacity: 0.4;
        margin: 12px 0;
    }
    
    /* 프롬프트 + 입력 영역 */
    .term-input-area {
        background: #0a0a0a;
        padding: 0 20px 20px 20px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .term-prompt {
        font-family: 'Courier New', monospace;
        font-size: 1rem;
        white-space: nowrap;
        flex-shrink: 0;
    }
    
    /* 깜빡이는 블록 커서 */
    @keyframes cursor-blink {
        0%, 49% { opacity: 1; }
        50%, 100% { opacity: 0; }
    }
    
    .cursor-block {
        display: inline-block;
        width: 10px;
        height: 18px;
        background: #edc5c4;
        animation: cursor-blink 1s step-end infinite;
        vertical-align: middle;
        margin-left: 5px;
    }
    
    /* 폼 스타일 제거 */
    [data-testid="stForm"] {
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    
    /* 입력창 - 투명 인라인 */
    .stTextInput > div > div > input {
        font-family: 'Courier New', monospace !important;
        background: #0a0a0a !important;
        border: none !important;
        border-bottom: 2px solid #edc5c4 !important;
        border-radius: 0 !important;
        color: #edc5c4 !important;
        font-size: 1rem !important;
        padding: 8px 5px !important;
        caret-color: #edc5c4 !important;
    }
    
    .stTextInput > div > div > input:focus {
        box-shadow: none !important;
        outline: none !important;
        border-bottom: 2px solid #fff !important;
    }
    
    .stTextInput > div > div > input::placeholder {
        color: #666 !important;
    }
    
    .stTextInput > div > div {
        background: transparent !important;
        border: none !important;
    }
    
    .stTextInput > div {
        background: transparent !important;
    }
    
    .stTextInput label {
        display: none !important;
    }
    
    /* 버튼 숨기기 */
    .stFormSubmitButton {
        position: absolute !important;
        left: -9999px !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 터미널 UI 렌더링 ---
st.markdown("""
<div class="term-header">
    <span class="term-btn red"></span>
    <span class="term-btn yellow"></span>
    <span class="term-btn green"></span>
    <span class="term-title">blog_analyzer.py — zsh — 80×24</span>
</div>
<div class="term-logs">
    <div class="term-line">[INIT] System starting...</div>
    <div class="term-line">[LOAD] Selenium WebDriver... OK</div>
    <div class="term-line">[READY] Naver Blog Analyzer v2.1</div>
    <div class="term-divider">────────────────────────────────────────────────</div>
</div>
<div class="term-input-area">
    <span class="term-prompt">
        <span style="color:#4a9c6d;">베리굿@analyzer</span><span style="color:#fff;">:</span><span style="color:#5c8fdb;">~</span><span style="color:#fff;">$ </span>
    </span>
    <span class="cursor-block"></span>
</div>
""", unsafe_allow_html=True)

# 입력 폼 (터미널 아래에 통합)
with st.form("main_form", clear_on_submit=False):
    user_input = st.text_input("", placeholder="블로그 ID 입력 후 Enter...", label_visibility="collapsed")
    submitted = st.form_submit_button("분석", type="primary")

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

# --- 결과 출력 영역 ---
if submitted and user_input:
    blog_id = extract_blog_id(user_input)
    
    # 터미널 스타일 분석 시작 메시지
    st.markdown(f"""
    <div class="analyzing-msg">
        <span style="color: #4a9c6d;">[EXEC]</span> Analyzing blog: <span style="color: #edc5c4;">{blog_id}</span><br>
        <span style="color: #4a9c6d;">[INFO]</span> Fetching visitor data...<br>
        <span style="color: #4a9c6d;">[INFO]</span> Scanning latest post...<br>
        <span style="color: #4a9c6d;">[INFO]</span> Checking search exposure...
    </div>
    """, unsafe_allow_html=True)
    
    with st.spinner(""):
        info = get_blog_info(blog_id)
        
        # 구분선
        st.divider()
        
        # 결과 헤더
        st.markdown('<div class="dashboard-header">📊 방문자 통계</div>', unsafe_allow_html=True)
        
        # 방문자 메트릭 카드
        c1, c2 = st.columns(2)
        c1.metric("오늘 방문자", info["today_visitors"])
        c2.metric("전체 방문자", info["total_visitors"])
        
        if info['latest_post_url']:
            detail = analyze_post_detail(info['latest_post_url'])
            
            st.markdown('<div class="dashboard-header">📝 최신글 분석</div>', unsafe_allow_html=True)
            st.info(f"**제목:** {info['latest_post_title']}")
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("발행일", detail["publish_date"])
            c2.metric("글자수", f"{detail['char_count']:,}")
            c3.metric("이미지", f"{detail['image_count']}장")
            c4.metric("공감", detail["like_count"])
            
            # 품질 판독
            st.markdown('<div class="dashboard-header">🔍 품질 진단</div>', unsafe_allow_html=True)
            
            warns = []
            if detail['char_count'] < 1000: warns.append("글자 수 부족 (1,000자 미만)")
            if detail['image_count'] < 5: warns.append("이미지 부족 (5장 미만)")
            if not is_within_one_month(detail['publish_date_obj']): warns.append("최근 활동 뜸함")
            
            if warns:
                for w in warns: st.warning(f"⚠️ {w}")
            else:
                st.success("✅ 블로그 품질 합격점!")
                
            # 검색 노출 결과
            st.markdown('<div class="dashboard-header">🎯 검색 노출 분석</div>', unsafe_allow_html=True)
            
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
        
        # 완료 메시지
        st.markdown("""
        <div class="analyzing-msg" style="margin-top: 20px; border-color: #4a9c6d;">
            <span style="color: #4a9c6d;">[DONE]</span> Analysis completed successfully.<br>
            <span style="color: #666;">Ready for next query...</span>
        </div>
        """, unsafe_allow_html=True)