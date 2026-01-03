import os
from PIL import Image


def compress_images(source_folder, quality=70, max_size=800):
    """
    遍历文件夹，压缩所有图片。
    quality: 图片质量 (1-100)，70 也就是压缩 30%
    max_size: 图片最长边限制为 800像素
    """
    print("🚀 开始给图片瘦身...")
    count = 0
    saved_space = 0

    for root, dirs, files in os.walk(source_folder):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                file_path = os.path.join(root, file)

                try:
                    # 打开图片
                    with Image.open(file_path) as img:
                        # 获取原始大小
                        original_size = os.path.getsize(file_path)

                        # 1. 修改尺寸 (如果太大)
                        if max(img.size) > max_size:
                            img.thumbnail((max_size, max_size))

                        # 2. 转换并保存 (转为 RGB 防止 PNG 透明底报错)
                        if img.mode in ("RGBA", "P"):
                            img = img.convert("RGB")

                        # 直接覆盖原文件 (保存为 JPG)
                        # 注意：这会把 png 变成 jpg 后缀，但 Streamlit 能识别
                        new_filename = os.path.splitext(file_path)[0] + ".jpg"
                        img.save(new_filename, "JPEG", quality=quality)

                        # 如果原文件是 png，删掉原来的 png，只留 jpg
                        if file.lower().endswith('.png'):
                            os.remove(file_path)

                        # 计算省了多少空间
                        new_size = os.path.getsize(new_filename)
                        saved_space += (original_size - new_size)
                        count += 1

                        if count % 20 == 0:
                            print(f"✅ 已处理 {count} 张图片...")

                except Exception as e:
                    print(f"⚠️ 跳过坏图: {file_path} ({e})")

    # 转换单位显示
    saved_mb = saved_space / (1024 * 1024)
    print(f"\n🎉 搞定！共处理 {count} 张图片。")
    print(f"📉 成功帮你把体积减小了：{saved_mb:.2f} MB！")


if __name__ == '__main__':
    # 只要运行这个，你的 images 文件夹体积就会大幅缩小
    compress_images("images")