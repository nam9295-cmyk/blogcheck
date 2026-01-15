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
st.set_page_config(page_title="베리굿 블로그 판독기 v2.0", page_icon="🍫")

st.title("🍫 베리굿 블로그 판독기 v2.0")
st.markdown("""
**[정밀 분석기]** 네이버 블로그 ID를 입력하면  
**방문자 수, 최신글 상세 분석, 검색 노출 상태**까지 한눈에 볼 수 있어요!
""")

# --- 2. 서버용 강력한 드라이버 설정 (건드리지 마!) ---
@st.cache_resource
def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1")
    
    # 서버 경로 강제 지정 (packages.txt가 설치한 경로)
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
    """방문자 수 텍스트에서 숫자만 추출"""
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
    """날짜 텍스트를 파싱해서 datetime 객체로 변환"""
    try:
        # "2024. 1. 15." 또는 "2024.1.15" 형식 처리
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
    """날짜가 최근 1개월 이내인지 확인"""
    if not date_obj:
        return False
    one_month_ago = datetime.now() - timedelta(days=30)
    return date_obj >= one_month_ago


# --- 4. 블로그 기본 정보 + 최신글 URL 가져오기 ---
def get_blog_info(blog_id):
    """블로그 메인에서 기본 정보와 최신글 URL을 가져옴"""
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
        
        # 방문자 수 찾기
        visitor_selectors = [
            "div[class^='count__']", "div[class*='count']", 
            "span[class^='count__']", "span[class*='count']",
            ".count.total"
        ]
        
        for selector in visitor_selectors:
            try:
                elem = driver.find_element(By.CSS_SELECTOR, selector)
                text = elem.text.strip()
                if "오늘" in text or "전체" in text:
                    result["today_visitors"], result["total_visitors"] = parse_visitor_text(text)
                    break
            except:
                continue
        
        # 최신글 제목 및 URL 찾기
        post_selectors = [
            "a[class*='title']",
            "a.title",
            "div[class^='list__'] a",
            ".post_title a",
            "a[href*='/PostView']",
        ]
        
        for selector in post_selectors:
            try:
                elem = driver.find_element(By.CSS_SELECTOR, selector)
                href = elem.get_attribute("href")
                title = elem.text.strip()
                
                if href and ("blog.naver.com" in href or "/PostView" in href or blog_id in href):
                    if title and len(title) > 1:
                        result["latest_post_title"] = title
                    result["latest_post_url"] = href
                    break
            except:
                continue
        
        # 못 찾으면 XPath로 시도
        if not result["latest_post_url"]:
            try:
                elem = driver.find_element(By.XPATH, "//a[contains(@href, 'blog.naver.com') and contains(@href, '/')]")
                href = elem.get_attribute("href")
                if href and blog_id in href:
                    result["latest_post_url"] = href
                    if not result["latest_post_title"] or result["latest_post_title"] == "글 없음":
                        result["latest_post_title"] = elem.text.strip() or "제목 없음"
            except:
                pass
                
    except Exception as e:
        print(f"Error getting blog info: {e}")
        
    return result


# --- 5. 상세 페이지 분석 (핵심 업그레이드!) ---
def analyze_post_detail(post_url):
    """최신글 상세 페이지에 들어가서 정밀 분석"""
    driver = get_driver()
    result = {
        "publish_date": "확인 불가",
        "publish_date_obj": None,
        "char_count": 0,
        "image_count": 0,
        "like_count": "0",
        "comment_count": "0"
    }
    
    if not post_url:
        return result
    
    try:
        driver.get(post_url)
        time.sleep(3)  # 상세 페이지 로딩 대기
        
        # 1. 발행 날짜 추출
        date_selectors = [
            "span[class*='date']",
            ".date",
            "p[class*='date']",
            "span[class*='_postDate']",
            ".blog_date",
            "time",
        ]
        
        for selector in date_selectors:
            try:
                elem = driver.find_element(By.CSS_SELECTOR, selector)
                date_text = elem.text.strip()
                if date_text and re.search(r'\d{4}', date_text):
                    result["publish_date"] = date_text
                    result["publish_date_obj"] = parse_date(date_text)
                    break
            except:
                continue
        
        # 2. 본문 글자 수 (공백 제외)
        content_selectors = [
            "div[class*='post_ct']",
            "div[class*='content']",
            ".se-main-container",
            "#postViewArea",
            "article",
            ".post_content",
        ]
        
        for selector in content_selectors:
            try:
                elem = driver.find_element(By.CSS_SELECTOR, selector)
                text = elem.text.strip()
                # 공백 제외 글자 수
                char_count = len(text.replace(" ", "").replace("\n", "").replace("\t", ""))
                if char_count > result["char_count"]:
                    result["char_count"] = char_count
            except:
                continue
        
        # 3. 이미지 개수
        try:
            images = driver.find_elements(By.CSS_SELECTOR, "img")
            # 본문 이미지만 카운트 (아이콘 제외)
            valid_images = 0
            for img in images:
                src = img.get_attribute("src") or ""
                width = img.get_attribute("width") or "0"
                # 작은 아이콘 이미지 제외 (100px 이상만)
                try:
                    if int(width) >= 100 or "postfiles" in src or "blogfiles" in src:
                        valid_images += 1
                except:
                    if "postfiles" in src or "blogfiles" in src:
                        valid_images += 1
            result["image_count"] = valid_images
        except:
            pass
        
        # 4. 공감(하트) 수
        like_selectors = [
            "span[class*='like_cnt']",
            "em[class*='u_cnt']",
            ".sympathy_cnt",
            "span[class*='count']",
            ".like_count",
        ]
        
        for selector in like_selectors:
            try:
                elem = driver.find_element(By.CSS_SELECTOR, selector)
                text = elem.text.strip()
                numbers = re.findall(r'\d+', text)
                if numbers:
                    result["like_count"] = numbers[0]
                    break
            except:
                continue
        
        # 5. 댓글 수
        comment_selectors = [
            "span[class*='comment_cnt']",
            "em[class*='_count']",
            ".comment_count",
            "a[class*='comment'] span",
        ]
        
        for selector in comment_selectors:
            try:
                elem = driver.find_element(By.CSS_SELECTOR, selector)
                text = elem.text.strip()
                numbers = re.findall(r'\d+', text)
                if numbers:
                    result["comment_count"] = numbers[0]
                    break
            except:
                continue
                
    except Exception as e:
        print(f"Error analyzing post: {e}")
        
    return result


# --- 6. 검색 노출 확인 ---
def check_search_exposure(blog_id, post_title):
    """네이버 검색에서 해당 블로그가 노출되는지 확인"""
    if post_title == "글 없음" or not post_title:
        return False, "제목을 못 찾아서 검색 불가"
        
    driver = get_driver()
    try:
        encoded_query = urllib.parse.quote(f'"{post_title}"')
        search_url = f"https://m.search.naver.com/search.naver?where=m_view&query={encoded_query}"
        
        driver.get(search_url)
        time.sleep(2)
        
        page_source = driver.page_source
        
        if blog_id in page_source:
            return True, "검색 결과 상단 노출 중! ✨"
        else:
            return False, "검색 결과 1페이지에 없음"
            
    except Exception as e:
        return False, f"검색 중 에러: {e}"


# --- 7. UI 구성 ---
st.divider()

blog_id_input = st.text_input("🔍 조회할 블로그 ID", placeholder="예: verygood_choco")

if st.button("정밀 분석 시작 🚀", type="primary", use_container_width=True):
    if not blog_id_input:
        st.warning("아이디를 입력해주세요!")
    else:
        blog_id = blog_id_input.strip()
        
        # Step 1: 블로그 기본 정보 가져오기
        with st.spinner(f"📡 '{blog_id}' 블로그 기본 정보 수집 중..."):
            info = get_blog_info(blog_id)
        
        st.divider()
        st.subheader("📊 기본 정보")
        
        col1, col2 = st.columns(2)
        col1.metric("👤 오늘 방문자", info["today_visitors"])
        col2.metric("📈 전체 방문자", info["total_visitors"])
        
        # Step 2: 최신글 상세 분석
        st.divider()
        st.subheader("📝 최신글 정밀 분석")
        
        if info['latest_post_url']:
            st.info(f"**제목:** {info['latest_post_title']}")
            
            with st.spinner("🔬 최신글 상세 페이지 분석 중..."):
                post_detail = analyze_post_detail(info['latest_post_url'])
            
            # 분석 결과 표시
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("📅 발행일", post_detail["publish_date"][:10] if len(post_detail["publish_date"]) > 10 else post_detail["publish_date"])
            col2.metric("📝 글자 수", f"{post_detail['char_count']:,}자")
            col3.metric("🖼️ 이미지", f"{post_detail['image_count']}장")
            col4.metric("❤️ 공감", post_detail["like_count"])
            
            st.caption(f"💬 댓글: {post_detail['comment_count']}개")
            
            # 판독 기준 경고 표시
            st.divider()
            st.subheader("� 블로그 품질 판독")
            
            warnings = []
            
            # 글자 수 체크
            if post_detail['char_count'] < 1000:
                warnings.append(("⚠️ 글 내용이 좀 짧아요", f"현재 {post_detail['char_count']:,}자 (권장: 1,000자 이상)"))
            else:
                st.success(f"✅ 글 분량 충분 ({post_detail['char_count']:,}자)")
            
            # 이미지 개수 체크
            if post_detail['image_count'] < 5:
                warnings.append(("⚠️ 사진이 너무 적어요", f"현재 {post_detail['image_count']}장 (권장: 5장 이상)"))
            else:
                st.success(f"✅ 이미지 충분 ({post_detail['image_count']}장)")
            
            # 활동 주기 체크
            if post_detail['publish_date_obj']:
                if not is_within_one_month(post_detail['publish_date_obj']):
                    warnings.append(("💤 활동이 뜸한 블로거입니다", "최근 1개월 내 글이 없어요"))
                else:
                    st.success("✅ 활발히 활동 중인 블로거!")
            
            # 경고 표시
            for title, desc in warnings:
                st.warning(f"**{title}**\n\n{desc}")
            
            # Step 3: 검색 노출 확인
            st.divider()
            st.subheader("🔎 검색 노출 판독")
            
            with st.spinner("네이버 검색 결과 확인 중..."):
                is_exposed, msg = check_search_exposure(blog_id, info['latest_post_title'])
            
            if is_exposed:
                st.success(f"✅ **노출 합격!** {msg}")
                st.caption("👉 이 블로거는 검색 노출이 잘 되는 '건강한 블로그'입니다.")
                st.balloons()
            else:
                st.error(f"❌ **노출 실패** - {msg}")
                st.caption("👉 최신 글이 검색 결과에 안 뜹니다. 저품질이거나 누락된 블로그일 수 있습니다.")
                
        else:
            st.warning("⚠️ 최신 글을 찾지 못했습니다. (비공개거나 블로그 구조가 특이함)")

# 푸터
st.divider()
st.caption("🍫 Made with love by VeryGood | v2.0 정밀 분석기")