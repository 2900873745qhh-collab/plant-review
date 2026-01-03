import streamlit as st
import random
from PIL import Image
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# --- 配置页面 ---
st.set_page_config(page_title="植物复习卡片(云同步版)", page_icon="🌿", layout="centered")


# --- 核心数据函数 (改为数据库版) ---

def get_data_from_db():
    """从谷歌表格读取所有数据"""
    # 建立连接，ttl=0 表示不缓存，每次都强制从云端拉取最新数据
    conn = st.connection("gsheets", type=GSheetsConnection)
    try:
        # 读取表格数据，假设第一列是 User, 第二列是 Mastered_Plants
        df = conn.read(worksheet="Sheet1", usecols=[0, 1], ttl=0)
        # 如果表格是空的或者没有列名，初始化一个空的 DataFrame
        if df.empty:
            return pd.DataFrame(columns=["User", "Mastered_Plants"])
        return df
    except:
        # 如果出错（比如刚建表），返回空表
        return pd.DataFrame(columns=["User", "Mastered_Plants"])


def save_data_to_db(df):
    """把数据写回谷歌表格"""
    conn = st.connection("gsheets", type=GSheetsConnection)
    conn.update(worksheet="Sheet1", data=df)


def get_user_mastered_list(user_name, df):
    """获取指定用户的斩杀名单"""
    # 筛选出该用户的数据
    user_data = df[df["User"] == user_name]
    if user_data.empty:
        return []

    # 获取 Mastered_Plants 列，它是一个字符串，我们用逗号分隔存储
    # 例如: "银杏,牡丹,玫瑰"
    saved_string = user_data.iloc[0]["Mastered_Plants"]
    if pd.isna(saved_string) or saved_string == "":
        return []
    return saved_string.split(",")


def update_user_progress(user_name, plant_name, action="add"):
    """更新用户进度 (核心逻辑)"""
    df = get_data_from_db()

    # 检查用户是否存在
    if user_name not in df["User"].values:
        # 如果是新用户，加一行
        new_row = pd.DataFrame({"User": [user_name], "Mastered_Plants": [""]})
        df = pd.concat([df, new_row], ignore_index=True)

    # 获取当前名单
    current_list = get_user_mastered_list(user_name, df)

    if action == "add":
        if plant_name not in current_list:
            current_list.append(plant_name)
    elif action == "remove":
        if plant_name in current_list:
            current_list.remove(plant_name)

    # 将列表变回字符串 "a,b,c"
    new_string = ",".join(current_list)

    # 更新 DataFrame
    df.loc[df["User"] == user_name, "Mastered_Plants"] = new_string

    # 写回云端
    save_data_to_db(df)


# --- 辅助函数 ---
def get_active_plants(mode, user_name):
    base_dir = "images"
    target_dirs = ["common", "important"] if mode == "全部复习" else ["important"]

    # 获取该用户已掌握的名单
    df = get_data_from_db()
    mastered_list = get_user_mastered_list(user_name, df)
    mastered_set = set(mastered_list)

    plant_list = []
    import os
    if os.path.exists(base_dir):
        for folder in target_dirs:
            full_path = os.path.join(base_dir, folder)
            if os.path.exists(full_path):
                names = [name for name in os.listdir(full_path)
                         if os.path.isdir(os.path.join(full_path, name))]
                for name in names:
                    if name not in mastered_set:
                        plant_list.append({
                            "name": name,
                            "path": os.path.join(full_path, name)
                        })
    return plant_list, len(mastered_list)


def get_random_image(plant_path):
    import os
    if not os.path.exists(plant_path): return None
    files = [f for f in os.listdir(plant_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    return os.path.join(plant_path, random.choice(files)) if files else None


# --- 界面逻辑 ---
st.title("🌿 植物复习 - 云端同步终极版")

with st.sidebar:
    st.header("👤 自动同步")
    # 不再需要复杂的上传下载按钮了，只要名字对，进度就在
    user_name = st.text_input("请输入名字 (自动读取进度)：", placeholder="例如：小明")

    if not user_name:
        st.info("👈 请输入名字登录")
        st.stop()

    st.success(f"欢迎回来，{user_name}！进度已自动同步。")

    mode = st.radio("选择范围", ["全部复习", "只复习重点"])

    if st.button("🔄 刷新数据"):
        st.cache_data.clear()
        st.rerun()

# 初始化 Session
if 'current_plant' not in st.session_state: st.session_state.current_plant = None
if 'current_image' not in st.session_state: st.session_state.current_image = None
if 'show_answer' not in st.session_state: st.session_state.show_answer = False
if 'history' not in st.session_state: st.session_state.history = []

# 获取题目
plants, mastered_count = get_active_plants(mode, user_name)
st.sidebar.metric("⚔️ 已斩杀", f"{mastered_count} 株")


# 动作函数
def next_question(record_history=True, was_killed=False):
    if record_history and st.session_state.current_plant:
        st.session_state.history.append({
            "name": st.session_state.current_plant,
            "image": st.session_state.current_image,
            "was_killed": was_killed
        })
    st.session_state.show_answer = False
    if not plants:
        st.session_state.current_plant = None
        return
    selected = random.choice(plants)
    st.session_state.current_plant = selected['name']
    st.session_state.current_image = get_random_image(selected['path'])


def kill_current():
    if st.session_state.current_plant:
        # 写数据库
        with st.spinner("正在同步到云端..."):
            update_user_progress(user_name, st.session_state.current_plant, "add")
        st.toast(f"⚔️ {st.session_state.current_plant} 已同步！")
        next_question(was_killed=True)


def undo_kill():
    if not st.session_state.history: return
    last = st.session_state.history.pop()
    st.session_state.current_plant = last["name"]
    st.session_state.current_image = last["image"]
    st.session_state.show_answer = True
    if last["was_killed"]:
        with st.spinner("正在撤销..."):
            update_user_progress(user_name, last["name"], "remove")
        st.toast(f"↩️ 已撤销斩杀：{last['name']}")


# 首次加载
if st.session_state.current_plant is None and plants:
    next_question(record_history=False)

# 显示区
if not plants and not st.session_state.current_plant:
    st.success("🎉 全部通关！")
    st.balloons()
    if st.button("⬅️ 撤销"):
        undo_kill()
        st.rerun()
else:
    st.caption(f"剩余：{len(plants)}")
    if st.session_state.current_image:
        try:
            st.image(Image.open(st.session_state.current_image), use_container_width=True)
        except:
            next_question(False)
            st.rerun()
    st.divider()

    if st.session_state.show_answer:
        st.markdown(f"### ✅ {st.session_state.current_plant}")
    else:
        st.markdown("### ❓ *** 点击看答案 ***")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("⬅️ 上一个", disabled=len(st.session_state.history) == 0):
            undo_kill()  # 这里简化逻辑，上一个如果是斩杀的，自动撤销
            st.rerun()
    with c2:
        if st.button("👀 看答案"):
            st.session_state.show_answer = True
            st.rerun()
    with c3:
        if st.button("➡️ 下一个"):
            next_question()
            st.rerun()
    with c4:
        if st.button("⚔️ 斩杀", type="primary"):
            kill_current()
            st.rerun()