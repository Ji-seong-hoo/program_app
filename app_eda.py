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
            st.info("Please upload population_trends.csv.")
            return

        df = pd.read_csv(uploaded)

        # ---------------------------
        # 기본 전처리
        # ---------------------------
        df = df.replace('-', 0)
        df.loc[df['지역'] == '세종', ['인구', '출생아수(명)', '사망자수(명)']] = df.loc[df['지역'] == '세종', ['인구', '출생아수(명)', '사망자수(명)']].replace('-', 0)
        df[['인구', '출생아수(명)', '사망자수(명)']] = df[['인구', '출생아수(명)', '사망자수(명)']].astype(int)

        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "기초 통계", "연도별 추이", "지역별 분석", "변화량 분석", "시각화"
        ])

        # ---------------------------
        # Tab 1: 기초 통계
        # ---------------------------
        with tab1:
            st.subheader("📄 DataFrame Info")
            buffer = io.StringIO()
            df.info(buf=buffer)
            st.text(buffer.getvalue())

            st.subheader("📈 Summary Statistics")
            st.dataframe(df.describe())

        # ---------------------------
        # Tab 2: 연도별 추이
        # ---------------------------
        with tab2:
            st.subheader("📊 Total Population Trend")
            nationwide = df[df['지역'] == '전국']

            fig, ax = plt.subplots()
            ax.plot(nationwide['연도'], nationwide['인구'], marker='o')
            ax.set_title("Total Population Over Time")
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")

            recent = nationwide.sort_values('연도', ascending=False).head(3)
            avg_change = ((recent['출생아수(명)'] - recent['사망자수(명)']).mean())
            projected_2035 = nationwide[nationwide['연도'] == nationwide['연도'].max()]['인구'].values[0] + avg_change * (2035 - nationwide['연도'].max())
            ax.axhline(projected_2035, color='red', linestyle='--')
            ax.text(nationwide['연도'].max() + 1, projected_2035, f"2035: {int(projected_2035):,}", color='red')
            st.pyplot(fig)

        # ---------------------------
        # Tab 3: 지역별 인구 변화량 분석
        # ---------------------------
        with tab3:
            st.subheader("📊 Population Change by Region")
            latest_year = df['연도'].max()
            prev_year = latest_year - 5
            region_df = df[df['지역'] != '전국']
            diff = region_df[region_df['연도'] == latest_year].set_index('지역')['인구'] - \
                   region_df[region_df['연도'] == prev_year].set_index('지역')['인구']
            change_rate = (diff / region_df[region_df['연도'] == prev_year].set_index('지역')['인구']) * 100

            bar_df = pd.DataFrame({
                'Change': diff / 1000,
                'ChangeRate': change_rate
            }).sort_values('Change', ascending=False)

            fig, ax = plt.subplots()
            sns.barplot(x=bar_df['Change'], y=bar_df.index, ax=ax)
            ax.set_title("Top Regions by Population Change (Thousands)")
            ax.set_xlabel("Change (K)")
            for i, v in enumerate(bar_df['Change']):
                ax.text(v + 5, i, f"{v:,.1f}", va='center')
            st.pyplot(fig)

            st.subheader("📉 Change Rate by Region")
            fig2, ax2 = plt.subplots()
            sns.barplot(x=bar_df['ChangeRate'], y=bar_df.index, ax=ax2)
            ax2.set_title("Population Change Rate by Region (%)")
            ax2.set_xlabel("Change Rate (%)")
            for i, v in enumerate(bar_df['ChangeRate']):
                ax2.text(v + 0.5, i, f"{v:.1f}%", va='center')
            st.pyplot(fig2)
            st.markdown("This chart compares absolute and relative population changes over 5 years by region.")

        # ---------------------------
        # Tab 4: 증감률 상위 사례
        # ---------------------------
        with tab4:
            st.subheader("📈 Top Population Increases/Decreases")
            df_sorted = df[df['지역'] != '전국'].sort_values(['지역', '연도'])
            df_sorted['Change'] = df_sorted.groupby('지역')['인구'].diff()

            top_changes = df_sorted.sort_values('Change', key=abs, ascending=False).head(100)
            top_changes['인구'] = top_changes['인구'].apply(lambda x: f"{int(x):,}")
            top_changes['Change_fmt'] = top_changes['Change'].apply(lambda x: f"{int(x):,}" if pd.notnull(x) else "")

            def highlight_change(val):
                if pd.isnull(val): return ''
                color = 'background-color: lightcoral' if float(val.replace(',', '')) < 0 else 'background-color: lightblue'
                return color

            st.dataframe(
                top_changes[['연도', '지역', '인구', 'Change_fmt']].style.applymap(highlight_change, subset=['Change_fmt'])
                .format({"Change_fmt": "{}"})
                .set_properties(**{'text-align': 'center'})
            )

        # ---------------------------
        # Tab 5: 시각화 - 누적 영역 그래프
        # ---------------------------
        with tab5:
            st.subheader("📊 Population Pivot & Area Chart")
            pivot_df = df[df['지역'] != '전국'].pivot(index='연도', columns='지역', values='인구')

            fig, ax = plt.subplots(figsize=(10, 6))
            pivot_df.plot.area(ax=ax, colormap='tab20')
            ax.set_title("Population by Region Over Time")
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")
            st.pyplot(fig)
            st.markdown("This area chart visualizes regional population distributions over the years.")



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