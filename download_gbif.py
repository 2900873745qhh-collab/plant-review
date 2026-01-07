import os
import requests
import plant_expert  # 引用之前的专家模块
import time


def download_image(url, save_path):
    """下载单张图片"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(response.content)
            return True
    except:
        return False
    return False


def process_list(txt_filename, output_subfolder):
    """读取名单并从 GBIF 下载"""

    if not os.path.exists(txt_filename):
        print(f"❌ 找不到文件: {txt_filename}")
        return

    # 创建主文件夹
    base_output = os.path.join("images", output_subfolder)
    os.makedirs(base_output, exist_ok=True)

    with open(txt_filename, 'r', encoding='utf-8') as f:
        plant_names = [line.strip() for line in f.readlines() if line.strip()]

    total = len(plant_names)
    print(f"🚀 开始处理 {txt_filename}，共 {total} 个...")

    for index, name in enumerate(plant_names):
        # 打印进度，end="" 表示不换行，方便后面接结果
        print(f"[{index + 1}/{total}] {name} : ", end="", flush=True)

        # 1. 检查是否已下载
        plant_dir = os.path.join(base_output, name)
        if os.path.exists(plant_dir) and len(os.listdir(plant_dir)) > 0:
            print("✅ 已存在")
            continue

        # 2. 调用专家模块 (核心逻辑：搜不到直接返回 None)
        info = plant_expert.fetch_plant_info(name)

        # --- 佛系跳过逻辑 ---
        if not info:
            print("💨 搜不到，跳过")  # 中文名没匹配上
            continue

        if not info.get('image_url'):
            print("💨 无图片，跳过")  # 搜到了物种，但数据库里没图
            continue
        # -------------------

        # 3. 只有搜到了且有图，才创建文件夹
        os.makedirs(plant_dir, exist_ok=True)

        # 4. 下载
        save_path = os.path.join(plant_dir, "1.jpg")
        success = download_image(info['image_url'], save_path)

        if success:
            print(f"✅ 成功 (学名: {info['scientific_name']})")

            # 顺便存个身份证，以后复习用
            with open(os.path.join(plant_dir, "info.txt"), "w", encoding="utf-8") as f:
                f.write(f"中文名: {info['name_cn']}\n")
                f.write(f"学名: {info['scientific_name']}\n")
                f.write(f"科: {info['family']}\n")
                f.write(f"属: {info['genus']}\n")
        else:
            print("❌ 下载失败，跳过")
            # 如果下载失败，把空文件夹删了，保持整洁
            try:
                os.rmdir(plant_dir)
            except:
                pass

        # 稍微歇一下
        time.sleep(0.2)


if __name__ == '__main__':
    # 记得先清空 images 文件夹再运行，效果最好
    process_list('plants.txt', 'common')
    process_list('重点.txt', 'important')

    print("\n🎉 处理完成！没下载下来的就是 GBIF 里没有的。")