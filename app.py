import streamlit as st
import os
import random
import shutil
import zipfile
import pandas as pd
from PIL import Image
from streamlit_gsheets import GSheetsConnection
import plant_expert  # 引用专家模块

# --- 🎨 UI 美化配置 ---
st.set_page_config(page_title="百植斩 - 你的植物记忆神器", page_icon="⚔️", layout="centered")

# 注入自定义 CSS 让界面更像 APP
st.markdown("""
    <style>
    /* 标题样式 */
    .main-title {
        font-size: 3rem !important;
        font-weight: 800;
        color: #2E7D32; /* 植物绿 */
        text-align: center;
        margin-bottom: 0px;
        font-family: 'Helvetica Neue', sans-serif;
    }
    .sub-title {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 30px;
    }
    /* 卡片容器样式 */
    .plant-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
        margin-bottom: 20px;
    }
    /* 按钮样式微调 */
    .stButton>button {
        border-radius: 20px;
        font-weight: bold;
        height: 50px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 临时文件处理 ---
TEMP_DIR = "temp_upload"


def clear_temp_dir():
    if os.path.exists(TEMP_DIR): shutil.rmtree(TEMP_DIR)
    os.makedirs(TEMP_DIR, exist_ok=True)


# --- ☁️ 数据库核心 (Google Sheets) ---
def get_db_connection():
    return st.connection("gsheets", type=GSheetsConnection)


def get_user_data(user_name):
    """获取用户斩杀数据"""
    try:
        conn = get_db_connection()
        df = conn.read(worksheet="Sheet1", usecols=[0, 1], ttl=0)
        if df.empty: return []
        user_row = df[df["User"] == user_name]
        if user_row.empty: return []
        saved_str = user_row.iloc[0]["Mastered_Plants"]
        if pd.isna(saved_str) or saved_str == "": return []
        return saved_str.split(",")
    except:
        return []


def sync_progress(user_name, plant_name, action="add"):
    """同步进度到云端"""
    conn = get_db_connection()
    df = conn.read(worksheet="Sheet1", usecols=[0, 1], ttl=0)
    if df.empty: df = pd.DataFrame(columns=["User", "Mastered_Plants"])

    if user_name not in df["User"].values:
        new_row = pd.DataFrame({"User": [user_name], "Mastered_Plants": [""]})
        df = pd.concat([df, new_row], ignore_index=True)

    # 获取当前列表
    user_idx = df.index[df["User"] == user_name][0]
    current_str = df.at[user_idx, "Mastered_Plants"]
    current_list = current_str.split(",") if pd.notna(current_str) and current_str else []

    if action == "add" and plant_name not in current_list:
        current_list.append(plant_name)
    elif action == "remove" and plant_name in current_list:
        current_list.remove(plant_name)

    df.at[user_idx, "Mastered_Plants"] = ",".join(current_list)
    conn.update(worksheet="Sheet1", data=df)
    return len(current_list)


# --- 🌱 内容源获取 ---
def get_local_plants(base_dir):
    plant_list = []
    if os.path.exists(base_dir):
        names = [name for name in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, name))]
        for name in names:
            full_path = os.path.join(base_dir, name)
            files = [f for f in os.listdir(full_path) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
            if files:
                plant_list.append(
                    {"name": name, "type": "local", "image_path": os.path.join(full_path, random.choice(files))})
    return plant_list


def get_api_plants(name_list):
    return [{"name": name, "type": "api"} for name in name_list]


# --- 🔄 状态初始化 ---
if 'quiz_list' not in st.session_state: st.session_state.quiz_list = []
if 'current_index' not in st.session_state: st.session_state.current_index = 0
if 'show_answer' not in st.session_state: st.session_state.show_answer = False
if 'current_plant_data' not in st.session_state: st.session_state.current_plant_data = None
if 'mastered_count' not in st.session_state: st.session_state.mastered_count = 0

# --- 📱 侧边栏 ---
with st.sidebar:
    st.markdown("## 👤 登录")
    user_name = st.text_input("斩杀者姓名：", placeholder="输入ID自动同步进度")

    if user_name:
        # 获取云端进度
        mastered_list = get_user_data(user_name)
        st.session_state.mastered_count = len(mastered_list)
        st.success(f"⚡ 已连接云端！累计斩杀：{len(mastered_list)}")

        st.markdown("---")
        st.markdown("## 📂 选择题库")
        mode = st.radio("模式：", ["1. 自带图库 (本地)", "2. 智能搜图 (GBIF API)", "3. 图片包 (ZIP)"])

        if mode.startswith("1") and st.button("🔄 加载系统图库", use_container_width=True):
            raw_list = get_local_plants("images/common") + get_local_plants("images/important")
            # 过滤掉已斩杀的
            st.session_state.quiz_list = [p for p in raw_list if p['name'] not in mastered_list]
            random.shuffle(st.session_state.quiz_list)
            st.session_state.current_index = 0
            st.rerun()

        elif mode.startswith("2"):
            txt_file = st.file_uploader("上传名单 (txt)", type="txt")
            if txt_file and st.button("🚀 启动智能复习", use_container_width=True):
                names = [line.strip() for line in txt_file.getvalue().decode("utf-8").split('\n') if line.strip()]
                # 过滤
                st.session_state.quiz_list = [get_api_plants([n])[0] for n in names if n not in mastered_list]
                random.shuffle(st.session_state.quiz_list)
                st.session_state.current_index = 0
                st.rerun()

        elif mode.startswith("3"):
            zip_file = st.file_uploader("上传图片包 (zip)", type="zip")
            if zip_file and st.button("📂 解压加载", use_container_width=True):
                clear_temp_dir()
                with zipfile.ZipFile(zip_file, 'r') as z:
                    z.extractall(TEMP_DIR)
                # 简单查找根目录
                root = TEMP_DIR
                if len(os.listdir(TEMP_DIR)) == 1: root = os.path.join(TEMP_DIR, os.listdir(TEMP_DIR)[0])
                raw_list = get_local_plants(root)
                st.session_state.quiz_list = [p for p in raw_list if p['name'] not in mastered_list]
                random.shuffle(st.session_state.quiz_list)
                st.session_state.current_index = 0
                st.rerun()

# --- 🖥️ 主界面 ---
st.markdown('<p class="main-title">⚔️ 百植斩</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Plant Slasher - 你的植物记忆神器</p>', unsafe_allow_html=True)

if not user_name:
    st.info("👈 请先在左侧输入名字登录，开启你的斩杀之旅！")
    st.stop()

if not st.session_state.quiz_list:
    st.success(f"🎉 恭喜！当前题库的植物已全部被你【斩杀】殆尽！")
    st.balloons()
    if st.button("🔄 想复习已斩杀的？点击重置"):
        st.cache_data.clear()  # 清除缓存
        st.rerun()
    st.stop()

# 获取当前题目
curr = st.session_state.quiz_list[st.session_state.current_index]

# 智能获取详情 (API模式)
if curr['type'] == 'api':
    if (st.session_state.current_plant_data is None or
            st.session_state.current_plant_data.get('name_cn') != curr['name']):
        with st.spinner("🧬 正在连接全球植物数据库..."):
            info = plant_expert.fetch_plant_info(curr['name'])
            st.session_state.current_plant_data = info if info else {"error": True, "name_cn": curr['name']}
    data = st.session_state.current_plant_data
else:
    st.session_state.current_plant_data = {"local": True, "name_cn": curr['name'], "image_path": curr['image_path']}
    data = st.session_state.current_plant_data

# --- 卡片展示区 ---
with st.container():
    col_img, col_info = st.columns([1.5, 1])

    with col_img:
        # 图片展示逻辑
        try:
            if data.get("error"):
                st.error("📡 暂无该植物数据")
            elif data.get("local"):
                st.image(Image.open(data['image_path']), use_container_width=True)
            elif data.get("image_url"):
                st.image(data['image_url'], use_container_width=True)
            else:
                st.warning("🖼️ 数据库暂无图片")
        except:
            st.error("图片加载失败")

    with col_info:
        st.write(f"#### 📝 剩余：{len(st.session_state.quiz_list)} 株")
        st.progress((st.session_state.mastered_count % 100) / 100)

        st.markdown("---")
        if st.session_state.show_answer:
            st.markdown(f"### ✅ {data.get('name_cn')}")

            if not data.get("local") and not data.get("error"):
                st.info(f"""
                **科名**: {data.get('family')}  
                **属名**: {data.get('genus')}  
                **学名**: *{data.get('scientific_name')}*
                """)
        else:
            st.markdown("### ❓  ?????")
            st.caption("看着图片，大声说出它的名字！")

st.markdown("---")

# --- 操控按钮区 ---
c1, c2, c3 = st.columns([1, 1, 1.2])

with c1:
    if st.button("👀 看答案", use_container_width=True):
        st.session_state.show_answer = True
        st.rerun()

with c2:
    if st.button("➡️ 下一个 (跳过)", use_container_width=True):
        st.session_state.current_index = (st.session_state.current_index + 1) % len(st.session_state.quiz_list)
        st.session_state.show_answer = False
        st.session_state.current_plant_data = None
        st.rerun()

with c3:
    # 斩杀逻辑
    if st.button("⚔️ 斩 杀 (Master)", type="primary", use_container_width=True):
        # 1. 移出当前题库
        st.session_state.quiz_list.pop(st.session_state.current_index)
        if st.session_state.current_index >= len(st.session_state.quiz_list):
            st.session_state.current_index = 0

        # 2. 同步云端
        with st.spinner("正在同步云端..."):
            new_count = sync_progress(user_name, curr['name'], "add")
            st.session_state.mastered_count = new_count

        st.toast(f"⚔️ 斩杀成功！再见，{curr['name']}！", icon="🔥")

        # 3. 重置状态
        st.session_state.show_answer = False
        st.session_state.current_plant_data = None
        st.rerun()