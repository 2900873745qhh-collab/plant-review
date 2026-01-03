import streamlit as st
import os
import random
from PIL import Image

# --- 配置页面 ---
st.set_page_config(page_title="植物复习卡片", page_icon="🌿", layout="centered")

# --- 文件路径配置 ---
MASTERED_FILE = "mastered.txt"  # 用来存储已斩杀植物的文件


# --- 核心数据函数 ---

def get_mastered_list():
    """读取已掌握的植物名单"""
    if not os.path.exists(MASTERED_FILE):
        return []
    with open(MASTERED_FILE, "r", encoding="utf-8") as f:
        return [line.strip() for line in f.readlines() if line.strip()]


def mark_as_mastered(plant_name):
    """将植物加入已掌握名单"""
    # 先读取防止重复
    current_list = get_mastered_list()
    if plant_name not in current_list:
        with open(MASTERED_FILE, "a", encoding="utf-8") as f:
            f.write(plant_name + "\n")


def unmark_as_mastered(plant_name):
    """【撤销斩杀】将植物从已掌握名单中移除"""
    current_list = get_mastered_list()
    if plant_name in current_list:
        current_list.remove(plant_name)
        # 重新写入文件
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


# --- 界面逻辑与状态管理 ---

st.title("🌿 植物辨识 - 进阶复习")

# 初始化 Session State
if 'current_plant' not in st.session_state:
    st.session_state.current_plant = None
if 'current_image' not in st.session_state:
    st.session_state.current_image = None
if 'show_answer' not in st.session_state:
    st.session_state.show_answer = False
# 新增：历史记录栈，用来存 [ {name, image, was_killed} ]
if 'history' not in st.session_state:
    st.session_state.history = []

# 侧边栏
with st.sidebar:
    st.header("⚙️ 设置")
    mode = st.radio("选择范围：", ["全部复习", "只复习重点"])
    st.divider()
    mastered_count = len(get_mastered_list())
    st.metric("⚔️ 已斩杀数量", f"{mastered_count} 株")
    if st.button("🔄 重置所有进度"):
        reset_progress()
        st.session_state.history = []  # 重置时清空历史
        st.rerun()

# 获取题库
plants = get_active_plants(mode)


# --- 动作函数 ---

def save_current_to_history(was_killed=False):
    """把当前状态存入历史，以便返回"""
    if st.session_state.current_plant:
        st.session_state.history.append({
            "name": st.session_state.current_plant,
            "image": st.session_state.current_image,
            "was_killed": was_killed
        })


def next_question(record_history=True, was_killed=False):
    """切换下一题"""
    # 1. 保存当前到历史记录
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
    """返回上一题"""
    if not st.session_state.history:
        st.warning("已经是第一张了，回不去啦！")
        return

    # 1. 取出最后一条记录
    last_record = st.session_state.history.pop()

    # 2. 恢复状态
    st.session_state.current_plant = last_record["name"]
    st.session_state.current_image = last_record["image"]
    st.session_state.show_answer = True  # 回去的时候通常想确认答案，所以直接显示

    # 3. 关键：如果那条记录是被“斩杀”的，现在要“复活”它
    if last_record["was_killed"]:
        if unmark_as_mastered(last_record["name"]):
            st.toast(f"↩️ 已撤销斩杀：{last_record['name']} 回到题库中", icon="🛡️")


def kill_current_plant():
    """斩杀当前"""
    if st.session_state.current_plant:
        mark_as_mastered(st.session_state.current_plant)
        st.toast(f"⚔️ 已斩杀：{st.session_state.current_plant}！", icon="💀")
        # 斩杀后去下一题，并标记 was_killed=True
        next_question(record_history=True, was_killed=True)


# 首次加载
if st.session_state.current_plant is None and plants:
    next_question(record_history=False)

# --- 主显示区 ---

if not plants and not st.session_state.current_plant:
    st.success("🎉 全部通关！所有植物都已斩杀！")
    st.balloons()
    if st.button("⬅️ 回到刚才那张 (撤销最后一次斩杀)"):
        go_back()
        st.rerun()
else:
    # 进度提示
    st.caption(f"当前模式剩余：{len(plants)} 株 | 历史记录：{len(st.session_state.history)} 条")

    # 图片
    if st.session_state.current_image:
        try:
            image = Image.open(st.session_state.current_image)
            st.image(image, use_container_width=True)
        except:
            st.error("图片加载失败")
            next_question(record_history=False)
            st.rerun()

    st.divider()

    # 答案显示
    if st.session_state.show_answer:
        st.markdown(f"### ✅ {st.session_state.current_plant}")
    else:
        st.markdown("### ❓  *** (点击看答案) ***")

    # 按钮布局：改为 4 列，加入“上一个”
    c1, c2, c3, c4 = st.columns([1, 1, 1, 1])

    with c1:
        # 只有历史记录不为空时，才让点上一页，否则禁用
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
        # 斩杀按钮
        if st.button("⚔️ 斩杀", type="primary", use_container_width=True, help="移出题库，不再复习"):
            kill_current_plant()
            st.rerun()