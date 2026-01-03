import streamlit as st
import os
import random
from PIL import Image
import io

# --- 配置页面 ---
st.set_page_config(page_title="植物复习卡片", page_icon="🌿", layout="centered")

# --- 界面逻辑：第一步先登录 ---
st.title("🌿 植物辨识 - 进阶复习")

# 在侧边栏输入名字
with st.sidebar:
    st.header("👤 用户设置")
    user_name = st.text_input("请输入你的名字开始：", placeholder="例如：小明")

    if not user_name:
        st.warning("👈 请先在侧边栏输入名字！")
        st.stop()  # 如果没输名字，程序就停在这里，不往下加载

    # 根据名字生成专属的文件名
    # 例如：mastered_小明.txt
    MASTERED_FILE = f"mastered_{user_name}.txt"
    st.success(f"当前用户：{user_name}")
    st.caption("⚠️ 云端注意：长时间不操作进度会丢失，请记得点击下方的‘下载进度’备份！")


# --- 核心数据函数 ---

def get_mastered_list():
    """读取已掌握的植物名单"""
    if not os.path.exists(MASTERED_FILE):
        return []
    with open(MASTERED_FILE, "r", encoding="utf-8") as f:
        return [line.strip() for line in f.readlines() if line.strip()]


def mark_as_mastered(plant_name):
    """将植物加入已掌握名单"""
    current_list = get_mastered_list()
    if plant_name not in current_list:
        with open(MASTERED_FILE, "a", encoding="utf-8") as f:
            f.write(plant_name + "\n")


def unmark_as_mastered(plant_name):
    """撤销斩杀"""
    current_list = get_mastered_list()
    if plant_name in current_list:
        current_list.remove(plant_name)
        with open(MASTERED_FILE, "w", encoding="utf-8") as f:
            for name in current_list:
                f.write(name + "\n")
        return True
    return False


def reset_progress():
    """重置进度"""
    if os.path.exists(MASTERED_FILE):
        os.remove(MASTERED_FILE)


def get_active_plants(mode):
    """获取当前模式下，还【没被斩杀】的植物"""
    base_dir = "images"
    target_dirs = []

    if mode == "全部复习":
        target_dirs = ["common", "important"]
    elif mode == "只复习重点":
        target_dirs = ["important"]

    mastered_set = set(get_mastered_list())
    plant_list = []

    # 遍历文件夹
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
    return plant_list


def get_random_image(plant_path):
    if not os.path.exists(plant_path):
        return None
    files = [f for f in os.listdir(plant_path)
             if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    if not files:
        return None
    return os.path.join(plant_path, random.choice(files))


# --- 侧边栏：存档与读档功能 ---
with st.sidebar:
    st.divider()
    st.header("💾 存档管理 (云端必用)")

    # 1. 下载进度
    if os.path.exists(MASTERED_FILE):
        with open(MASTERED_FILE, "r", encoding="utf-8") as f:
            st.download_button(
                label="⬇️ 下载我的进度 (备份)",
                data=f,
                file_name=MASTERED_FILE,
                mime="text/plain",
                help="复习完点一下，把进度存到本地，防止云端丢失"
            )

    # 2. 上传进度
    uploaded_file = st.file_uploader("⬆️ 上传之前的进度", type=["txt"])
    if uploaded_file is not None:
        # 读取上传的内容并覆盖当前用户的进度
        stringio = io.StringIO(uploaded_file.getvalue().decode("utf-8"))
        content = stringio.read()
        with open(MASTERED_FILE, "w", encoding="utf-8") as f:
            f.write(content)
        st.success("✅ 进度已恢复！")
        # 不需要rerun，下一步会自动刷新

    st.divider()

    # 3. 设置和重置
    mode = st.radio("选择范围：", ["全部复习", "只复习重点"])
    mastered_count = len(get_mastered_list())
    st.metric("⚔️ 已斩杀数量", f"{mastered_count} 株")

    if st.button("🔄 重置当前用户进度"):
        reset_progress()
        st.session_state.history = []
        st.rerun()

# --- 状态管理 ---
if 'current_plant' not in st.session_state:
    st.session_state.current_plant = None
if 'current_image' not in st.session_state:
    st.session_state.current_image = None
if 'show_answer' not in st.session_state:
    st.session_state.show_answer = False
if 'history' not in st.session_state:
    st.session_state.history = []

# 获取题库
plants = get_active_plants(mode)


# --- 动作函数 ---

def save_current_to_history(was_killed=False):
    if st.session_state.current_plant:
        st.session_state.history.append({
            "name": st.session_state.current_plant,
            "image": st.session_state.current_image,
            "was_killed": was_killed
        })


def next_question(record_history=True, was_killed=False):
    if record_history:
        save_current_to_history(was_killed)

    st.session_state.show_answer = False

    if not plants:
        st.session_state.current_plant = None
        return

    selected_plant = random.choice(plants)
    img_path = get_random_image(selected_plant['path'])

    st.session_state.current_plant = selected_plant['name']
    st.session_state.current_image = img_path


def go_back():
    if not st.session_state.history:
        st.warning("已经是第一张了")
        return
    last_record = st.session_state.history.pop()
    st.session_state.current_plant = last_record["name"]
    st.session_state.current_image = last_record["image"]
    st.session_state.show_answer = True

    if last_record["was_killed"]:
        if unmark_as_mastered(last_record["name"]):
            st.toast(f"↩️ 已撤销斩杀：{last_record['name']}", icon="🛡️")


def kill_current_plant():
    if st.session_state.current_plant:
        mark_as_mastered(st.session_state.current_plant)
        st.toast(f"⚔️ 已斩杀：{st.session_state.current_plant}", icon="💀")
        next_question(record_history=True, was_killed=True)


# 首次加载
if st.session_state.current_plant is None and plants:
    next_question(record_history=False)

# --- 主显示区 ---

if not plants and not st.session_state.current_plant:
    st.success(f"🎉 恭喜 {user_name}！全部通关！")
    st.balloons()
    if st.button("⬅️ 撤销最后一次斩杀"):
        go_back()
        st.rerun()
else:
    st.caption(f"当前题库剩余：{len(plants)} | 历史：{len(st.session_state.history)}")

    if st.session_state.current_image:
        try:
            image = Image.open(st.session_state.current_image)
            st.image(image, use_container_width=True)
        except:
            st.error("图片加载失败")
            next_question(record_history=False)
            st.rerun()

    st.divider()

    if st.session_state.show_answer:
        st.markdown(f"### ✅ {st.session_state.current_plant}")
    else:
        st.markdown("### ❓  *** (点击看答案) ***")

    c1, c2, c3, c4 = st.columns([1, 1, 1, 1])

    with c1:
        disabled = len(st.session_state.history) == 0
        if st.button("⬅️ 上一个", use_container_width=True, disabled=disabled):
            go_back()
            st.rerun()
    with c2:
        if st.button("👀 看答案", use_container_width=True):
            st.session_state.show_answer = True
            st.rerun()
    with c3:
        if st.button("➡️ 下一个", use_container_width=True):
            next_question()
            st.rerun()
    with c4:
        if st.button("⚔️ 斩杀", type="primary", use_container_width=True):
            kill_current_plant()
            st.rerun()