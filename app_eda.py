import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------
# Firebase 설정
# ---------------------
firebase_config = {
    "apiKey": "AIzaSyCswFmrOGU3FyLYxwbNPTp7hvQxLfTPIZw",
    "authDomain": "sw-projects-49798.firebaseapp.com",
    "databaseURL": "https://sw-projects-49798-default-rtdb.firebaseio.com",
    "projectId": "sw-projects-49798",
    "storageBucket": "sw-projects-49798.firebasestorage.app",
    "messagingSenderId": "812186368395",
    "appId": "1:812186368395:web:be2f7291ce54396209d78e"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firestore = firebase.database()
storage = firebase.storage()

# ---------------------
# 세션 상태 초기화
# ---------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

# ---------------------
# 홈 페이지 클래스
# ---------------------
class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 Home")
        if st.session_state.get("logged_in"):
            st.success(f"{st.session_state.get('user_email')}님 환영합니다.")

        st.markdown("""
        ---
        **Population Trends Dataset**  
        - 파일명: `population_trends.csv`  
        - 설명: 대한민국의 연도별 지역 인구, 출생아수, 사망자수 정보를 포함한 데이터  
        - 주요 변수:  
          - `연도`: 연도 (정수형)  
          - `지역`: 행정 구역 이름  
          - `인구`: 해당 지역의 전체 인구 수  
          - `출생아수(명)`: 출생한 아기 수  
          - `사망자수(명)`: 사망자 수  
        """)

# ---------------------
# 로그인 페이지 클래스
# ---------------------
class Login:
    def __init__(self):
        st.title("🔐 로그인")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user['idToken']

                user_info = firestore.child("users").child(email.replace(".", "_")).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name", "")
                    st.session_state.user_gender = user_info.get("gender", "선택 안함")
                    st.session_state.user_phone = user_info.get("phone", "")
                    st.session_state.profile_image_url = user_info.get("profile_image_url", "")

                st.success("로그인 성공!")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("로그인 실패")

# ---------------------
# 회원가입 페이지 클래스
# ---------------------
class Register:
    def __init__(self, login_page_url):
        st.title("📝 회원가입")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        name = st.text_input("성명")
        gender = st.selectbox("성별", ["선택 안함", "남성", "여성"])
        phone = st.text_input("휴대전화번호")

        if st.button("회원가입"):
            try:
                auth.create_user_with_email_and_password(email, password)
                firestore.child("users").child(email.replace(".", "_")).set({
                    "email": email,
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "role": "user",
                    "profile_image_url": ""
                })
                st.success("회원가입 성공! 로그인 페이지로 이동합니다.")
                time.sleep(1)
                st.switch_page(login_page_url)
            except Exception:
                st.error("회원가입 실패")

# ---------------------
# 비밀번호 찾기 페이지 클래스
# ---------------------
class FindPassword:
    def __init__(self):
        st.title("🔎 비밀번호 찾기")
        email = st.text_input("이메일")
        if st.button("비밀번호 재설정 메일 전송"):
            try:
                auth.send_password_reset_email(email)
                st.success("비밀번호 재설정 이메일을 전송했습니다.")
                time.sleep(1)
                st.rerun()
            except:
                st.error("이메일 전송 실패")

# ---------------------
# 사용자 정보 수정 페이지 클래스
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 사용자 정보")

        email = st.session_state.get("user_email", "")
        new_email = st.text_input("이메일", value=email)
        name = st.text_input("성명", value=st.session_state.get("user_name", ""))
        gender = st.selectbox(
            "성별",
            ["선택 안함", "남성", "여성"],
            index=["선택 안함", "남성", "여성"].index(st.session_state.get("user_gender", "선택 안함"))
        )
        phone = st.text_input("휴대전화번호", value=st.session_state.get("user_phone", ""))

        uploaded_file = st.file_uploader("프로필 이미지 업로드", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            file_path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(file_path).put(uploaded_file, st.session_state.id_token)
            image_url = storage.child(file_path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = image_url
            st.image(image_url, width=150)
        elif st.session_state.get("profile_image_url"):
            st.image(st.session_state.profile_image_url, width=150)

        if st.button("수정"):
            st.session_state.user_email = new_email
            st.session_state.user_name = name
            st.session_state.user_gender = gender
            st.session_state.user_phone = phone

            firestore.child("users").child(new_email.replace(".", "_")).update({
                "email": new_email,
                "name": name,
                "gender": gender,
                "phone": phone,
                "profile_image_url": st.session_state.get("profile_image_url", "")
            })

            st.success("사용자 정보가 저장되었습니다.")
            time.sleep(1)
            st.rerun()

# ---------------------
# 로그아웃 페이지 클래스
# ---------------------
class Logout:
    def __init__(self):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.id_token = ""
        st.session_state.user_name = ""
        st.session_state.user_gender = "선택 안함"
        st.session_state.user_phone = ""
        st.session_state.profile_image_url = ""
        st.success("로그아웃 되었습니다.")
        time.sleep(1)
        st.rerun()

# ---------------------
# EDA 페이지 클래스
# ---------------------
class EDA:
    def __init__(self):
        st.title("📊 Population Trends EDA")
        uploaded = st.file_uploader("Upload population_trends.csv", type="csv")
        if not uploaded:
            st.info("Please upload population_trends.csv file.")
            return

        df = pd.read_csv(uploaded)

        # ----------------------
        # 안전한 데이터 전처리
        # ----------------------
        try:
            df.loc[df['지역'] == '세종', ['인구', '출생아수(명)', '사망자수(명)']] = \
                df.loc[df['지역'] == '세종', ['인구', '출생아수(명)', '사망자수(명)']].replace('-', '0')

            for col in ['인구', '출생아수(명)', '사망자수(명)']:
                df[col] = df[col].astype(str).str.replace(',', '', regex=False).astype(int)
        except Exception as e:
            st.error(f"⚠️ 데이터 전처리 중 오류 발생: {e}")
            return

        # ----------------------
        # 탭 UI 구성
        # ----------------------
        tabs = st.tabs(["기초 통계", "연도별 추이", "지역별 분석", "변화량 분석", "시각화"])

        # 탭 1: 기초 통계
        with tabs[0]:
            st.header("📋 Descriptive Stats")
            buffer = io.StringIO()
            df.info(buf=buffer)
            st.text(buffer.getvalue())
            st.subheader("Data Description")
            st.dataframe(df.describe())

        # 탭 2: 연도별 추이
        with tabs[1]:
            st.header("📈 Total Population Trend")
            national_df = df[df['지역'] == '전국']

            fig, ax = plt.subplots()
            sns.lineplot(data=national_df, x='연도', y='인구', marker='o', ax=ax)
            ax.set_title("Population Trend")
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")

            # 인구 예측 (단순 선형 예측)
            recent = national_df.sort_values(by='연도').tail(3)
            delta = (recent['출생아수(명)'] - recent['사망자수(명)']).mean()
            latest_year = recent['연도'].max()
            latest_pop = national_df[national_df['연도'] == latest_year]['인구'].values[0]
            future_year = 2035
            estimated_pop = int(latest_pop + (future_year - latest_year) * delta)
            ax.plot(future_year, estimated_pop, 'ro')
            ax.text(future_year, estimated_pop, f"  {future_year}: {estimated_pop:,}", color='red')

            st.pyplot(fig)

        # 탭 3: 지역별 분석
        with tabs[2]:
            st.header("🏙️ Regional Change")
            latest_year = df['연도'].max()
            base_year = latest_year - 5
            base = df[df['연도'] == base_year].set_index('지역')['인구']
            latest = df[df['연도'] == latest_year].set_index('지역')['인구']

            delta_df = pd.DataFrame({
                'change': (latest - base).drop('전국', errors='ignore') / 1000  # 단위 천 명
            })
            delta_df['change_rate'] = ((latest - base) / base * 100).drop('전국', errors='ignore')
            delta_df = delta_df.sort_values(by='change', ascending=False)

            # 지역명 영어로 번역 (예시)
            region_map = {"서울": "Seoul", "부산": "Busan", "대구": "Daegu", "인천": "Incheon",
                          "광주": "Gwangju", "대전": "Daejeon", "울산": "Ulsan", "세종": "Sejong",
                          "경기": "Gyeonggi", "강원": "Gangwon", "충북": "Chungbuk", "충남": "Chungnam",
                          "전북": "Jeonbuk", "전남": "Jeonnam", "경북": "Gyeongbuk", "경남": "Gyeongnam",
                          "제주": "Jeju"}
            delta_df.index = delta_df.index.map(region_map.get)

            fig, ax = plt.subplots(figsize=(10, 6))
            sns.barplot(x='change', y=delta_df.index, data=delta_df, ax=ax)
            ax.set_title("5-Year Population Change (k)")
            ax.set_xlabel("Change (thousands)")
            for i, v in enumerate(delta_df['change']):
                ax.text(v, i, f"{v:,.1f}", va='center')
            st.pyplot(fig)

            st.subheader("5-Year Change Rate (%)")
            fig2, ax2 = plt.subplots(figsize=(10, 6))
            sns.barplot(x='change_rate', y=delta_df.index, data=delta_df, ax=ax2)
            ax2.set_xlabel("Change Rate (%)")
            for i, v in enumerate(delta_df['change_rate']):
                ax2.text(v, i, f"{v:.1f}%", va='center')
            st.pyplot(fig2)

            st.markdown("> 지역 간 인구 변화의 격차가 크게 나타나며, 수도권은 증가세, 지방은 감소세가 두드러집니다.")

        # 탭 4: 증감량 테이블
        with tabs[3]:
            st.header("📋 Top 100 Changes")
            temp = df[df['지역'] != '전국'].sort_values(by=['지역', '연도'])
            temp['증감'] = temp.groupby('지역')['인구'].diff()
            top = temp.sort_values(by='증감', ascending=False).head(100)
            top_display = top[['연도', '지역', '인구', '증감']].copy()
            top_display['증감'] = top_display['증감'].fillna(0).astype(int)
            top_display['증감_fmt'] = top_display['증감'].apply(lambda x: f"{x:+,}")

            def highlight(val):
                color = 'background-color: #d0f0fd' if val > 0 else 'background-color: #ffd6d6'
                return color

            styled = top_display.style.format({'증감': "{:,}"}).applymap(lambda v: highlight(v), subset=['증감'])
            st.dataframe(styled)

        # 탭 5: 누적 시각화
        with tabs[4]:
            st.header("📊 Stacked Area Chart")
            pivot = df[df['지역'] != '전국'].pivot(index='연도', columns='지역', values='인구')
            pivot = pivot.fillna(0)
            pivot.columns = pivot.columns.map(region_map.get)

            fig, ax = plt.subplots(figsize=(12, 6))
            pivot.plot.area(ax=ax, colormap='tab20')
            ax.set_title("Population by Region")
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")
            st.pyplot(fig)


# ---------------------
# 페이지 객체 생성
# ---------------------
Page_Login    = st.Page(Login,    title="Login",    icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW   = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="My Info", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout,   title="Logout",  icon="🔓", url_path="logout")
Page_EDA      = st.Page(EDA,      title="EDA",     icon="📊", url_path="eda")

# ---------------------
# 네비게이션 실행
# ---------------------
if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]

selected_page = st.navigation(pages)
selected_page.run()
