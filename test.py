import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------------------------------------
# 기본 설정
# ---------------------------------------------
st.set_page_config(page_title="GC 함량 분석", layout="wide")

st.title("🧬 생물군별 GC 함량 및 유전체 크기 분석")
st.write("바이러스, 원핵생물, 진핵생물의 유전체 크기(Mb)와 GC 함량(%)의 관계를 시각화합니다.")

# ---------------------------------------------
# 데이터 불러오기
# ---------------------------------------------
@st.cache_data
def load_data():
    dfs = {}
    files = {
        "바이러스": "바이러스.csv",
        "원핵생물": "원핵생물.csv",
        "진핵생물": "진핵생물.csv"
    }
    for key, path in files.items():
        try:
            df = pd.read_csv(path)
            df["Group"] = key
            dfs[key] = df
        except Exception as e:
            st.warning(f"{key} 데이터 불러오기 실패: {e}")
    return dfs

dfs = load_data()

# ---------------------------------------------
# 컬럼명 한글로 변환
# ---------------------------------------------
NUM_COLS = {
    "size": ["Size(Mb)", "Size", "GenomeSize(Mb)", "Genome Size (Mb)"],
    "gc": ["GC%", "GC", "GC content", "GC_content"],
    "cds": ["CDS", "GeneCount", "Genes"]
}
TXT_COLS = {
    "org": ["#Organism Name", "Organism Name", "Organism", "Name"],
    "group": ["Organism Groups", "Group", "Taxon", "Taxonomic group"],
    "host": ["Host"]
}

def pick(cols, candidates):
    for c in candidates:
        if c in cols:
            return c
    return None

def normalize(df: pd.DataFrame) -> pd.DataFrame:
    cols = list(df.columns)
    rename_map = {}
    s = pick(cols, NUM_COLS["size"]);  rename_map[s] = "유전체 크기(Mb)" if s else None
    g = pick(cols, NUM_COLS["gc"]);    rename_map[g] = "GC 함량(%)" if g else None
    c = pick(cols, NUM_COLS["cds"]);   rename_map[c] = "유전자 수" if c else None
    o = pick(cols, TXT_COLS["org"]);   rename_map[o] = "생물명" if o else None
    gr = pick(cols, TXT_COLS["group"]);rename_map[gr] = "분류군" if gr else None
    h = pick(cols, TXT_COLS["host"]);  rename_map[h] = "숙주" if h else None
    rename_map = {k: v for k, v in rename_map.items() if k}
    df = df.rename(columns=rename_map)

    # 숫자형 변환
    for c in ["유전체 크기(Mb)", "GC 함량(%)", "유전자 수"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

# 모든 데이터프레임에 적용
for k in dfs.keys():
    dfs[k] = normalize(dfs[k])

# ---------------------------------------------
# 데이터 합치기
# ---------------------------------------------
if len(dfs) == 0:
    st.error("CSV 파일을 찾을 수 없습니다. test.py와 같은 폴더에 CSV 파일을 넣어주세요.")
    st.stop()

data = pd.concat(dfs.values(), ignore_index=True)

# ---------------------------------------------
# 사용자 입력
# ---------------------------------------------
st.sidebar.header("⚙️ 시각화 설정")
group_select = st.sidebar.multiselect("생물군 선택", ["바이러스", "원핵생물", "진핵생물"], default=["바이러스", "원핵생물", "진핵생물"])
logx = st.sidebar.checkbox("X축 로그 스케일 (유전체 크기)", value=False)

sub = data[data["Group"].isin(group_select)]

# ---------------------------------------------
# 그래프 1: 산점도
# ---------------------------------------------
st.subheader("📊 유전체 크기와 GC 함량의 관계")

hover_cols = [c for c in ["생물명", "분류군", "숙주", "유전자 수"] if c in sub.columns]

fig_scatter = px.scatter(
    sub,
    x="유전체 크기(Mb)",
    y="GC 함량(%)",
    color="Group",
    hover_data=hover_cols,
    labels={"유전체 크기(Mb)": "유전체 크기(Mb)", "GC 함량(%)": "GC 함량(%)"},
    title="생물군별 유전체 크기와 GC 함량"
)
if logx:
    fig_scatter.update_xaxes(type="log")
st.plotly_chart(fig_scatter, use_container_width=True)

# ---------------------------------------------
# 그래프 2: 박스플롯
# ---------------------------------------------
st.subheader("📦 GC 함량 분포 비교")

fig_box = px.box(
    sub,
    x="Group",
    y="GC 함량(%)",
    color="Group",
    labels={"Group": "생물군", "GC 함량(%)": "GC 함량(%)"},
    title="생물군별 GC 함량 분포 비교"
)
st.plotly_chart(fig_box, use_container_width=True)

# ---------------------------------------------
# 그래프 3: 히스토그램
# ---------------------------------------------
st.subheader("📈 유전체 크기 분포")

fig_hist = px.histogram(
    sub,
    x="유전체 크기(Mb)",
    color="Group",
    nbins=50,
    opacity=0.6,
    labels={"유전체 크기(Mb)": "유전체 크기(Mb)", "Group": "생물군"},
    title="생물군별 유전체 크기 분포"
)
if logx:
    fig_hist.update_xaxes(type="log")
st.plotly_chart(fig_hist, use_container_width=True)

# ---------------------------------------------
# 요약 통계
# ---------------------------------------------
st.subheader("📋 요약 통계")
if "유전체 크기(Mb)" in sub.columns and "GC 함량(%)" in sub.columns:
    st.write(sub[["Group", "유전체 크기(Mb)", "GC 함량(%)", "유전자 수"]].groupby("Group").describe().round(2))
else:
    st.warning("유전체 크기(Mb) 또는 GC 함량(%) 열을 찾을 수 없습니다.")
