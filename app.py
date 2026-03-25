# streamlit 연결
import streamlit as st
# API 사용
import requests
# 데이터 표시용
import pandas as pd

# 기본 화면은 좌우로 좁습니다.
# '영화 | 리뷰' 형식으로 레이아웃을 꾸미기 위해 추가했습니다.
st.set_page_config(layout='wide')

# 영화 목록은 페이지 당 5개만 출력시키고 있습니다.
# query param을 통해 pagination을 구현하였습니다.
# 이는 session_state를 쓰지 않아 별도의 정보 저장을 하지 않으며
# 일반적인 웹 서비스에서 pagination을 구현하는 방식입니다.
if 'page' in st.query_params:
    page = int(st.query_params['page'])
else:
    page=0

# 최상단의 '헤더 바'를 구성합니다.
# 이는 '페이지 제목', '영화 추가 버튼', '새로고침 버튼'으로 구성됩니다.
c1, c2 = st.columns([4,3])
c1.header('영화 리뷰 감정 분석 사이트')

c2_1, c2_2 = c2.columns([2,1])
# 영화 추가 버튼은 '영화 정보를 입력하는 Form을 출력하는 popover입니다.
# 영화 등록 실패 시 에러 메시지를 다시 출력해줍니다.
# 일단은 단순히 '입력을 다시 검토하라'는 메시지만 출력시켰습니다.
with c2_1.popover('영화 추가'):
    with st.form(f'movie_form',width=750, clear_on_submit=True):
        st.header("영화 등록")
        title = st.text_input("영화 제목")
        release_date = st.date_input("개봉일")
        director = st.text_input("감독")
        genre = st.selectbox("장르", ("스릴러", "코미디", "로맨스", "추리", "드라마", "다큐"))
        poster = st.text_input("포스터 URL")
        submitted = st.form_submit_button("저장")
        error_text= None
        if submitted:
            inputs=(title,release_date,director,genre,poster,submitted)
            response = requests.post('https://adover-test.duckdns.org/movie',
                                     data={'title': title, 'release_date': release_date,
                                           'director': director, 'genre': genre,
                                           'poster': poster})
            if response.status_code == 200:
                st.rerun()
            else:
                error_text = st.text('잘못된 입력이 있었습니다.')

# 새로고침 버튼은 rerun을 합니다.
if c2_2.button('새로고침'):
    st.rerun()

# 전체 영화 리스트를 받습니다.
movie_list_response=requests.get(f'https://adover-test.duckdns.org/movie?page={page}').json()
print(movie_list_response)
movie_list = pd.DataFrame(movie_list_response['result'])
# 추가로 다음/이전 페이지의 존재 여부를 받습니다.
next_page = movie_list_response['next_page']
prev_page = movie_list_response['prev_page']

# 각 영화마다 한 줄씩 container로 작성합니다.
for idx, movie in movie_list.iterrows():
    line=st.container(width='stretch', height=350, border=False)
    # 영화 정보는 상대적으로 내용이 짧기에 4:6 비율로 줬습니다.
    c1,c2=line.columns([4,6], border=True)
    with c1:
        c1_1, c1_2 = c1.columns([3,5])
        c1_1.header(movie['title'])
        c1_1.text(f"개봉일: {movie['release_date']}")
        c1_1.text(f"감독: {movie['director']}")
        c1_1.text(f"장르: {movie['genre']}")
        c1_2.image(movie['poster'])
        # '리뷰 쓰기' 버튼은 '영화 추가' 버튼과 마찬가지로 popover입니다.
        # 등록 실패 시에도 form 초기화를 하는 것까지 동일합니다.
        with c1_1.popover('리뷰 쓰기'):
            with st.form(f'review_form_{idx}', width=500, clear_on_submit=True):
                writer = st.text_input("작성자")
                review_text = st.text_area("리뷰 내용", max_chars=500)
                submitted = st.form_submit_button("저장", key=f'review_write_{idx}')
                error_message = st.empty()
                if submitted:
                    try:
                        # 입력된 정보들을 전송합니다.
                        response = requests.post('https://adover-test.duckdns.org/review',
                                                data={
                                                    'movie_id': movie.name, 'writer': writer,
                                                    'review_text': review_text})
                        if response.status_code == 200:
                            st.rerun()
                        else:
                            t=response.json()
                            # 실패 시 에러 메시지를 출력합니다.
                            error_message.text(f"에러! {t['detail']}")
                    except Exception as e:
                        error_message.text("서버 통신 중 오류가 발생했습니다.")
    # 우측의 '리뷰 리스트' 출력 container입니다.
    # 영화 정보를 활용하여 데이터를 얻습니다.
    with c2:
        c2.header('최근 리뷰 목록')
        try:
            reviews = requests.get(f'https://adover-test.duckdns.org/review/{movie.name}').json()
            reviews = pd.DataFrame(reviews['result'])
            for ir, review in reviews.iterrows():
                c2_1, c2_2, c2_3 = c2.columns([2,5,2])
                c2_1.text(f"작성자: {review[0]}")
                c2_2.text(f"내용: {review[1]}")
                c2_3.text(f"평가: {review[2]}")
        except Exception as e:
            error_message.text("서버 통신 중 오류가 발생했습니다.")

# pagination용 버튼을 출력하기 위해 설정하였습니다.
# 이들 중 c1, c2가 실제 버튼이 들어가는 column입니다.
c,c1,c1_5,c2,c3 = st.columns([3,1,1,1,3])
if prev_page:
    if c1.button('이전 페이지'):
        st.switch_page('app.py',query_params={'page':page-1})
if next_page:
    if c2.button('다음 페이지'):
        st.switch_page('app.py',query_params={'page':page+1})