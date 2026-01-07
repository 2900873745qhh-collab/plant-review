import streamlit as st
import os
import random
import shutil
import zipfile
import pandas as pd
from PIL import Image
from streamlit_gsheets import GSheetsConnection
import plant_expert

# --- 🎨 UI 美化 ---
st.set_page_config(page_title="百植斩 - 你的植物记忆神器", page_icon="⚔️", layout="centered")

st.markdown("""
    <style>
    .main-title { font-size: 3rem !important; font-weight: 800; color: #2E7D32; text-align: center; margin-bottom: 0px; font-family: 'Helvetica Neue', sans-serif; }
    .sub-title { font-size: 1.2rem; color: #666; text-align: center; margin-bottom: 30px; }
    .info-box { 
        background-color: #e8f5e9; 
        padding: 15px; 
        border-radius: 10px; 
        border-left: 5px solid #2E7D32; 
        margin-top: 10px; 
        text-align: left;
        font-size: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .stButton>button { border-radius: 20px; font-weight: bold; height: 50px; }
    .sidebar-help { font-size: 0.85rem; color: #666; margin-bottom: 15px; }
    </style>
""", unsafe_allow_html=True)

TEMP_DIR = "temp_upload"


def clear_temp_dir():
    if os.path.exists(TEMP_DIR): shutil.rmtree(TEMP_DIR)
    os.makedirs(TEMP_DIR, exist_ok=True)


# --- ☁️ 数据库 ---
def get_db_connection(): return st.connection("gsheets", type=GSheetsConnection)


def get_user_data(user_name):
    try:
        conn = get_db_connection()
        df = conn.read(worksheet="Sheet1", usecols=[0, 1], ttl=0)
        if df.empty: return []
        row = df[df["User"] == user_name]
        return row.iloc[0]["Mastered_Plants"].split(",") if not row.empty and pd.notna(
            row.iloc[0]["Mastered_Plants"]) and row.iloc[0]["Mastered_Plants"] else []
    except:
        return []


def sync_progress(user_name, plant_name, action="add"):
    conn = get_db_connection()
    df = conn.read(worksheet="Sheet1", usecols=[0, 1], ttl=0)
    if df.empty: df = pd.DataFrame(columns=["User", "Mastered_Plants"])
    if user_name not in df["User"].values:
        df = pd.concat([df, pd.DataFrame({"User": [user_name], "Mastered_Plants": [""]})], ignore_index=True)
    idx = df.index[df["User"] == user_name][0]
    curr = df.at[idx, "Mastered_Plants"].split(",") if pd.notna(df.at[idx, "Mastered_Plants"]) and df.at[
        idx, "Mastered_Plants"] else []
    if action == "add" and plant_name not in curr:
        curr.append(plant_name)
    elif action == "remove" and plant_name in curr:
        curr.remove(plant_name)
    df.at[idx, "Mastered_Plants"] = ",".join(curr)
    conn.update(worksheet="Sheet1", data=df)
    return len(curr)


# --- 🌱 内容源 ---
def get_local_plants(base_dir):
    lst = []
    if os.path.exists(base_dir):
        for n in os.listdir(base_dir):
            if os.path.isdir(os.path.join(base_dir, n)):
                fp = os.path.join(base_dir, n)
                imgs = [f for f in os.listdir(fp) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
                if imgs: lst.append({"name": n, "type": "local", "image_path": os.path.join(fp, random.choice(imgs)),
                                     "folder_path": fp})
    return lst


def get_api_plants(names): return [{"name": n, "type": "api"} for n in names]


# --- 🔄 初始化 ---
if 'quiz_list' not in st.session_state: st.session_state.quiz_list = []
if 'current_index' not in st.session_state: st.session_state.current_index = 0
if 'show_answer' not in st.session_state: st.session_state.show_answer = False
if 'current_plant_data' not in st.session_state: st.session_state.current_plant_data = None
if 'mastered_count' not in st.session_state: st.session_state.mastered_count = 0
if 'current_mode' not in st.session_state: st.session_state.current_mode = "1. 🏛️ 系统题库 (默认)"

# --- 📱 侧边栏 ---
with st.sidebar:
    st.markdown("## 👤 用户登录")
    user_name = st.text_input("斩杀者姓名：", placeholder="输入ID自动同步进度")
    if user_name:
        ml = get_user_data(user_name)
        st.session_state.mastered_count = len(ml)
        st.success(f"⚡ 进度同步！已斩杀：{len(ml)}")
        st.markdown("---")
        st.markdown("## 📂 模式选择")
        mode = st.radio("复习方式：", ["1. 🏛️ 系统题库 (默认)", "2. 🧠 智能搜图 (API)", "3. 📂 我的图片包 (ZIP)"], index=0)

        if mode.startswith("1"):
            st.caption("📝 使用服务器预置高清图库。")
            if st.session_state.current_mode != mode or not st.session_state.quiz_list:
                raw = get_local_plants("images/common") + get_local_plants("images/important")
                flt = [p for p in raw if p['name'] not in ml]
                if flt:
                    random.shuffle(flt)
                    st.session_state.quiz_list = flt
                    st.session_state.current_index = 0
                    st.session_state.current_mode = mode
                    st.session_state.current_plant_data = None
                    st.session_state.show_answer = False
                    st.rerun()

        elif mode.startswith("2"):
            st.caption("📝 上传 TXT 名单，自动联网搜图和资料。")
            txt = st.file_uploader("📄 上传名单 (txt)", type="txt")
            if txt and st.button("🚀 开始联网搜索", use_container_width=True):
                ns = [l.strip() for l in txt.getvalue().decode("utf-8").split('\n') if l.strip()]
                flt = [n for n in ns if n not in ml]
                st.session_state.quiz_list = get_api_plants(flt)
                random.shuffle(st.session_state.quiz_list)
                st.session_state.current_index = 0
                st.session_state.current_mode = mode
                st.session_state.current_plant_data = None
                st.session_state.show_answer = False
                st.rerun()

        elif mode.startswith("3"):
            st.caption("📝 上传 ZIP 图片包。")
            zipf = st.file_uploader("📦 上传图片包 (zip)", type="zip")
            if zipf and st.button("📂 解压加载", use_container_width=True):
                clear_temp_dir()
                with zipfile.ZipFile(zipf, 'r') as z:
                    z.extractall(TEMP_DIR)
                root = TEMP_DIR
                if len(os.listdir(TEMP_DIR)) == 1: root = os.path.join(TEMP_DIR, os.listdir(TEMP_DIR)[0])
                raw = get_local_plants(root)
                flt = [p for p in raw if p['name'] not in ml]
                random.shuffle(flt)
                st.session_state.quiz_list = flt
                st.session_state.current_index = 0
                st.session_state.current_mode = mode
                st.session_state.current_plant_data = None
                st.session_state.show_answer = False
                st.rerun()

# --- 🖥️ 主界面 ---
st.markdown('<p class="main-title">⚔️ 百植斩</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Plant Slasher - 你的植物记忆神器</p>', unsafe_allow_html=True)

if not user_name:
    st.info("👈 请先在左侧输入名字登录")
    st.stop()
if not st.session_state.quiz_list:
    st.success("🎉 恭喜！当前题库已全部斩杀！")
    if st.button("🔄 重置"):
        st.cache_data.clear()
        st.rerun()
    st.stop()

curr = st.session_state.quiz_list[st.session_state.current_index]

# --- 🧠 数据获取 (含中文翻译) ---
if (st.session_state.current_plant_data is None or
        st.session_state.current_plant_data.get('name_cn') != curr['name']):

    # 1. API 模式
    if curr['type'] == 'api':
        with st.spinner("🧬 正在连接全球数据库..."):
            info = plant_expert.fetch_plant_info(curr['name'])
            st.session_state.current_plant_data = info if info else {"error": True, "name_cn": curr['name']}

    # 2. 本地模式
    else:
        plant_data = {"local": True, "name_cn": curr['name'], "image_path": curr['image_path']}
        # 尝试读本地 info.txt
        info_path = os.path.join(curr['folder_path'], "info.txt")
        if os.path.exists(info_path):
            try:
                with open(info_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if "学名:" in line: plant_data["scientific_name"] = line.split(":", 1)[1].strip()
                        if "科:" in line: plant_data["family"] = line.split(":", 1)[1].strip()
                        if "属:" in line: plant_data["genus"] = line.split(":", 1)[1].strip()
            except:
                pass

        # 无论本地有没有读到，只要有拉丁名，就去网上查一下中文科属（如果没有info.txt，fetch_info会自动查）
        # 这里逻辑简化：如果没有中文科属，就现场查
        if "family_cn" not in plant_data:
            with st.spinner(f"正在翻译 {curr['name']} 的科属..."):
                # 如果本地已经有拉丁名，只查翻译
                if "scientific_name" in plant_data:
                    plant_data["family_cn"] = plant_expert.translate_latin_to_chinese(plant_data.get("family"))
                    plant_data["genus_cn"] = plant_expert.translate_latin_to_chinese(plant_data.get("genus"))
                else:
                    # 如果本地连拉丁名都没有，全套查
                    online_info = plant_expert.fetch_plant_info(curr['name'])
                    if online_info:
                        plant_data.update(online_info)
                        plant_data["local"] = True

        st.session_state.current_plant_data = plant_data

data = st.session_state.current_plant_data

# --- 🃏 卡片 ---
with st.container():
    c_img, c_info = st.columns([1.5, 1])
    with c_img:
        try:
            if data.get("error"):
                st.error("📡 暂无数据")
            elif data.get("local"):
                st.image(Image.open(data['image_path']), use_container_width=True)
            elif data.get("image_url"):
                st.image(data['image_url'], use_container_width=True)
            else:
                st.warning("🖼️ 无图片")
        except:
            st.error("图片加载失败")
    with c_info:
        st.write(f"#### 📝 剩余：{len(st.session_state.quiz_list)}")
        st.progress((st.session_state.mastered_count % 100) / 100)
        st.caption(f"已斩杀：{st.session_state.mastered_count}")
        st.markdown("---")

        if st.session_state.show_answer:
            st.markdown(f"## ✅ {data.get('name_cn')}")
            if data.get("family") or data.get("scientific_name"):
                # 优先显示中文，拉丁文在括号里
                fam = f"{data.get('family_cn', '未知')} ({data.get('family', '')})"
                gen = f"{data.get('genus_cn', '未知')} ({data.get('genus', '')})"
                sci = data.get('scientific_name', '未知')
                st.markdown(f"""
                <div class="info-box">
                <b>科 (Family):</b> {fam} <br>
                <b>属 (Genus):</b> {gen} <br>
                <b>学名:</b> <i>{sci}</i>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("🤖 暂无专业信息")
        else:
            st.markdown("### ❓  ?????")
            st.caption("看着图片，大声说出它的名字！")

st.markdown("---")
b1, b2, b3 = st.columns([1, 1, 1.2])
with b1:
    if st.button("👀 看答案", use_container_width=True):
        st.session_state.show_answer = True
        st.rerun()
with b2:
    if st.button("➡️ 下一个", use_container_width=True):
        st.session_state.current_index = (st.session_state.current_index + 1) % len(st.session_state.quiz_list)
        st.session_state.show_answer = False
        st.session_state.current_plant_data = None
        st.rerun()
with b3:
    if st.button("⚔️ 斩 杀", type="primary", use_container_width=True):
        st.session_state.quiz_list.pop(st.session_state.current_index)
        if st.session_state.current_index >= len(st.session_state.quiz_list): st.session_state.current_index = 0
        with st.spinner("同步云端..."):
            st.session_state.mastered_count = sync_progress(user_name, curr['name'], "add")
        st.toast(f"⚔️ 斩杀成功！", icon="🔥")
        st.session_state.show_answer = False
        st.session_state.current_plant_data = None
        st.rerun()