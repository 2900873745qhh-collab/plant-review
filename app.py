import streamlit as st
import os
import random
import shutil
import zipfile
import pandas as pd
from PIL import Image
from streamlit_gsheets import GSheetsConnection
import plant_expert

# --- 🎨 UI 配置 ---
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
    .source-tag { font-size: 0.8rem; color: #888; margin-top: 5px; text-align: right; display: block; }
    .stButton>button { border-radius: 20px; font-weight: bold; height: 50px; }
    </style>
""", unsafe_allow_html=True)

TEMP_DIR = "temp_upload"


def clear_temp_dir():
    if os.path.exists(TEMP_DIR): shutil.rmtree(TEMP_DIR)
    os.makedirs(TEMP_DIR, exist_ok=True)


def contains_chinese(text):
    if not text: return False
    for char in text:
        if '\u4e00' <= char <= '\u9fff': return True
    return False


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


# --- 🌱 内容源处理 ---

def get_local_plants(base_dir):
    """读取本地文件夹"""
    lst = []
    if os.path.exists(base_dir):
        for n in os.listdir(base_dir):
            if os.path.isdir(os.path.join(base_dir, n)):
                fp = os.path.join(base_dir, n)
                imgs = [f for f in os.listdir(fp) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
                if imgs: lst.append({"name": n, "type": "local", "image_path": os.path.join(fp, random.choice(imgs)),
                                     "folder_path": fp})
    return lst


def parse_txt_content(content):
    """
    🌟 智能解析 TXT 内容
    支持格式：
    1. 仅名字: 玫瑰
    2. 带详情: 玫瑰#蔷薇科#蔷薇属#Rosa rugosa
    """
    lines = [l.strip() for l in content.split('\n') if l.strip()]
    plant_objects = []

    for line in lines:
        parts = line.split('#')  # 使用 # 作为分隔符
        name = parts[0].strip()

        # 基础对象
        obj = {"name": name, "type": "api", "user_info": {}}

        # 如果用户提供了额外信息，存入 user_info
        # 顺序约定：名字 # 科 # 属 # 学名
        if len(parts) > 1 and parts[1].strip(): obj["user_info"]["family_cn"] = parts[1].strip()
        if len(parts) > 2 and parts[2].strip(): obj["user_info"]["genus_cn"] = parts[2].strip()
        if len(parts) > 3 and parts[3].strip(): obj["user_info"]["scientific_name"] = parts[3].strip()

        plant_objects.append(obj)

    return plant_objects


# --- 🔄 状态管理 ---
if 'quiz_list' not in st.session_state: st.session_state.quiz_list = []
if 'current_index' not in st.session_state: st.session_state.current_index = 0
if 'show_answer' not in st.session_state: st.session_state.show_answer = False
if 'current_plant_data' not in st.session_state: st.session_state.current_plant_data = None
if 'mastered_count' not in st.session_state: st.session_state.mastered_count = 0
if 'current_mode' not in st.session_state: st.session_state.current_mode = "1. 🏛️ 系统题库 (默认)"
if 'history' not in st.session_state: st.session_state.history = []


# --- 🎮 动作函数 ---
def save_to_history():
    st.session_state.history.append({
        "index": st.session_state.current_index,
        "data": st.session_state.current_plant_data,
        "show_answer": True
    })


def go_back():
    if st.session_state.history:
        last = st.session_state.history.pop()
        st.session_state.current_index = last["index"]
        st.session_state.current_plant_data = last["data"]
        st.session_state.show_answer = last["show_answer"]


def go_next():
    save_to_history()
    st.session_state.current_index = (st.session_state.current_index + 1) % len(st.session_state.quiz_list)
    st.session_state.show_answer = False
    st.session_state.current_plant_data = None


def do_master(user_name, plant_name):
    save_to_history()
    st.session_state.quiz_list.pop(st.session_state.current_index)
    if st.session_state.current_index >= len(st.session_state.quiz_list): st.session_state.current_index = 0
    with st.spinner("同步云端..."):
        st.session_state.mastered_count = sync_progress(user_name, plant_name, "add")
    st.toast(f"⚔️ 斩杀成功！", icon="🔥")
    st.session_state.show_answer = False
    st.session_state.current_plant_data = None


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

        if mode != st.session_state.current_mode: st.session_state.history = []

        if mode.startswith("1"):
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
            st.caption("📝 上传 TXT 名单。支持自动搜索，也支持自定义详情。")
            st.caption("💡 **自定义格式**：`植物名#科#属#拉丁名`")
            st.caption("例如：`凤凰木#豆科#凤凰木属#Delonix regia`")

            txt = st.file_uploader("📄 上传名单 (txt)", type="txt")
            if txt and st.button("🚀 开始复习", use_container_width=True):
                # 调用新的解析函数
                raw_objects = parse_txt_content(txt.getvalue().decode("utf-8"))
                flt = [obj for obj in raw_objects if obj['name'] not in ml]

                st.session_state.quiz_list = flt
                random.shuffle(st.session_state.quiz_list)
                st.session_state.current_index = 0
                st.session_state.current_mode = mode
                st.session_state.current_plant_data = None
                st.session_state.show_answer = False
                st.session_state.history = []
                st.rerun()

        elif mode.startswith("3"):
            st.caption("📝 上传 ZIP 图片包。如果包内包含 info.txt，将直接使用。")
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
                st.session_state.history = []
                st.rerun()

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

# --- 🧠 核心数据获取 (终极逻辑) ---
if (st.session_state.current_plant_data is None or
        st.session_state.current_plant_data.get('name_cn') != curr['name']):

    plant_data = {"name_cn": curr['name']}

    # 🌟 1. 智能搜图 (API) 模式
    if curr['type'] == 'api':
        user_provided = curr.get("user_info", {})

        # 如果用户提供了学名，这非常宝贵！我们用它来搜图，准度Max！
        # 但我们不需要再去查文本资料了，因为用户已经提供了
        if user_provided.get("scientific_name"):
            with st.spinner(f"正在根据学名 [{user_provided['scientific_name']}] 搜图..."):
                # 只搜图，不覆盖文本
                # 这里的 fetch_plant_info 会优先用学名搜
                info = plant_expert.fetch_plant_info(user_provided['scientific_name'])

                # 构造数据：用户提供的文本 + 网上搜到的图
                plant_data.update(user_provided)  # 文本信用户的
                if info and info.get('image_url'):
                    plant_data['image_url'] = info['image_url']  # 图用网上的
                else:
                    plant_data['error'] = False  # 即使没图也不算错，只要有文本就行

        # 如果用户啥都没提供，那就全网裸搜
        else:
            with st.spinner("🧬 正在连接全球数据库..."):
                info = plant_expert.fetch_plant_info(curr['name'])
                if info:
                    plant_data.update(info)
                else:
                    plant_data["error"] = True

    # 🌟 2. 本地/ZIP 模式
    else:
        plant_data["local"] = True
        plant_data["image_path"] = curr['image_path']
        info_path = os.path.join(curr['folder_path'], "info.txt")

        # 读取本地文件
        if os.path.exists(info_path):
            try:
                with open(info_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if ":" in line:
                            key, val = line.split(":", 1)
                            key, val = key.strip(), val.strip()
                            if "Bing" in val or "未知" in val: continue
                            if "学名" in key and contains_chinese(val): continue
                            if "学名" in key: plant_data["scientific_name"] = val
                            if "科" in key: plant_data["family_cn"] = val  # 本地info里通常直接是中文
                            if "属" in key: plant_data["genus_cn"] = val
            except:
                pass

        # 补漏逻辑
        # 如果本地文件里有有效数据，我们就不联网了！
        has_data = plant_data.get("family_cn") or plant_data.get("scientific_name")

        if not has_data:
            with st.spinner(f"正在云端补全 {curr['name']} 的科属信息..."):
                # 先查字典
                if curr['name'] in plant_expert.CUSTOM_DICTIONARY:
                    entry = plant_expert.CUSTOM_DICTIONARY[curr['name']]
                    if isinstance(entry, dict):
                        plant_data.update({
                            "scientific_name": entry['latin'],
                            "family_cn": entry['family'],
                            "genus_cn": entry['genus']
                        })

                # 再查网
                if not plant_data.get("scientific_name"):
                    online_info = plant_expert.fetch_plant_info(curr['name'])
                    if online_info: plant_data.update(online_info)

    st.session_state.current_plant_data = plant_data

data = st.session_state.current_plant_data

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

            # 显示逻辑
            fam_cn = data.get('family_cn')
            fam_la = data.get('family')
            gen_cn = data.get('genus_cn')
            gen_la = data.get('genus')
            sci_nm = data.get('scientific_name')

            # 来源标注
            source_tag = "数据来源: 未知"
            if data.get('user_info'):
                source_tag = "数据来源: 用户上传"
            elif fam_cn:
                source_tag = "数据来源: Wikidata/人工校验"
            elif fam_la:
                source_tag = "数据来源: GBIF (未汉化)"

            # 只要有数据就显示
            if fam_cn or fam_la or gen_cn or sci_nm:
                f_show = fam_cn if fam_cn else (fam_la if fam_la else "未知")
                g_show = gen_cn if gen_cn else (gen_la if gen_la else "未知")
                s_show = sci_nm if sci_nm and not contains_chinese(sci_nm) else "未知"

                # 如果有拉丁，加括号显示
                if fam_la and fam_cn != fam_la: f_show += f" ({fam_la})"
                if gen_la and gen_cn != gen_la: g_show += f" ({gen_la})"

                st.markdown(f"""
                <div class="info-box">
                <b>科 (Family):</b> {f_show} <br>
                <b>属 (Genus):</b> {g_show} <br>
                <b>学名:</b> <i>{s_show}</i>
                <span class="source-tag">{source_tag}</span>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("🤖 暂无专业科属数据")
        else:
            st.markdown("### ❓  ?????")
            st.caption("看着图片，大声说出它的名字！")

st.markdown("---")
b1, b2, b3, b4 = st.columns([1, 1, 1, 1.2])
with b1:
    disable_back = len(st.session_state.history) == 0
    if st.button("⬅️ 上一个", use_container_width=True, disabled=disable_back):
        go_back()
        st.rerun()
with b2:
    if st.button("👀 看答案", use_container_width=True):
        st.session_state.show_answer = True
        st.rerun()
with b3:
    if st.button("➡️ 下一个", use_container_width=True):
        go_next()
        st.rerun()
with b4:
    if st.button("⚔️ 斩 杀", type="primary", use_container_width=True):
        do_master(user_name, curr['name'])
        st.rerun()