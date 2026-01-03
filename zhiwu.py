
import os
from icrawler.builtin import BingImageCrawler


def download_from_file(txt_filename, output_subfolder):
    """
    读取 txt 文件，下载图片到 images 下的指定子文件夹
    """
    # 检查文件是否存在
    if not os.path.exists(txt_filename):
        print(f"❌ 错误：找不到文件 {txt_filename}，请确认它在项目根目录下。")
        return

    print(f"📂 开始处理文件：{txt_filename} ...")

    # 读取文件内容
    with open(txt_filename, 'r', encoding='utf-8') as f:
        # 读取每一行，去掉首尾空格
        plant_names = [line.strip() for line in f.readlines() if line.strip()]

    total = len(plant_names)
    print(f"📝 共发现 {total} 个植物名称，准备开始下载...")

    # 遍历每一个植物名字
    for index, name in enumerate(plant_names):
        print(f"[{index + 1}/{total}] 正在下载：{name}")

        # 设定保存路径：images/子文件夹/植物名
        # 例如：images/important/银杏
        save_path = os.path.join('images', output_subfolder, name)

        # 如果文件夹不存在，会自动创建（icrawler 会处理，但为了保险我们也可以不管）

        # 使用 Bing 搜索引擎下载（比 Google 稳定不需要梯子）
        crawler = BingImageCrawler(storage={'root_dir': save_path})

        # 开始下载，keyword是关键词，max_num是下载数量（这里设为3张）
        # overwrite=True 表示如果不小心重复下载会覆盖，防止占用空间
        # 修改后的代码 (加上 " 植物" 后缀)：
        crawler.crawl(keyword=name + " 植物 花", max_num=3, overwrite=True)

    print(f"✅ {txt_filename} 处理完成！\n")


# --- 主程序入口 ---
if __name__ == '__main__':
    # 1. 下载 plants.txt 到 images/common 文件夹
    download_from_file('plants.txt', 'common')

    # 2. 下载 重点.txt 到 images/important 文件夹
    download_from_file('重点.txt', 'important')

    print("🎉 所有图片下载任务结束！请去 images 文件夹查看结果。")