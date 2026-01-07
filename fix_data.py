import os
import plant_expert
import time

# ==========================================
# 📖 本地科名翻译字典 (不用联网，秒翻！)
# ==========================================
FAMILY_DICT = {
    "Acanthaceae": "爵床科", "Aceraceae": "槭树科", "Agavaceae": "龙舌兰科", "Aizoaceae": "番杏科",
    "Amaranthaceae": "苋科", "Amaryllidaceae": "石蒜科", "Anacardiaceae": "漆树科", "Annonaceae": "番荔枝科",
    "Apiaceae": "伞形科", "Apocynaceae": "夹竹桃科", "Aquifoliaceae": "冬青科", "Araceae": "天南星科",
    "Araliaceae": "五加科", "Araucariaceae": "南洋杉科", "Arecaceae": "棕榈科", "Aristolochiaceae": "马兜铃科",
    "Asparagaceae": "天门冬科", "Asphodelaceae": "阿福花科", "Asteraceae": "菊科", "Balsaminaceae": "凤仙花科",
    "Begoniaceae": "秋海棠科", "Berberidaceae": "小檗科", "Betulaceae": "桦木科", "Bignoniaceae": "紫葳科",
    "Boraginaceae": "紫草科", "Brassicaceae": "十字花科", "Bromeliaceae": "凤梨科", "Buxaceae": "黄杨科",
    "Cactaceae": "仙人掌科", "Campanulaceae": "桔梗科", "Cannabaceae": "大麻科", "Capparaceae": "白花菜科",
    "Caprifoliaceae": "忍冬科", "Caryophyllaceae": "石竹科", "Casuarinaceae": "木麻黄科", "Celastraceae": "卫矛科",
    "Chenopodiaceae": "藜科", "Chloranthaceae": "金粟兰科", "Clusiaceae": "藤黄科", "Combretaceae": "使君子科",
    "Commelinaceae": "鸭跖草科", "Compositae": "菊科", "Convolvulaceae": "旋花科", "Cornaceae": "山茱萸科",
    "Crassulaceae": "景天科", "Cruciferae": "十字花科", "Cucurbitaceae": "葫芦科", "Cupressaceae": "柏科",
    "Cycadaceae": "苏铁科", "Cyperaceae": "莎草科", "Dilleniaceae": "五桠果科", "Dioscoreaceae": "薯蓣科",
    "Dipsacaceae": "川续断科", "Dipterocarpaceae": "龙脑香科", "Dracaenaceae": "龙血树科", "Ebenaceae": "柿科",
    "Elaeagnaceae": "胡颓子科", "Ericaceae": "杜鹃花科", "Euphorbiaceae": "大戟科", "Fabaceae": "豆科",
    "Fagaceae": "壳斗科", "Flacourtiaceae": "大风子科", "Gentianaceae": "龙胆科", "Geraniaceae": "牻牛儿苗科",
    "Gesneriaceae": "苦苣苔科", "Ginkgoaceae": "银杏科", "Gramineae": "禾本科", "Guttiferae": "藤黄科",
    "Hamamelidaceae": "金缕梅科", "Hydrangeaceae": "绣球花科", "Hypericaceae": "金丝桃科", "Iridaceae": "鸢尾科",
    "Juglandaceae": "胡桃科", "Labiatae": "唇形科", "Lamiaceae": "唇形科", "Lauraceae": "樟科",
    "Leguminosae": "豆科", "Liliaceae": "百合科", "Linaceae": "亚麻科", "Loganiaceae": "马钱科",
    "Loranthaceae": "桑寄生科", "Lythraceae": "千屈菜科", "Magnoliaceae": "木兰科", "Malpighiaceae": "金虎尾科",
    "Malvaceae": "锦葵科", "Marantaceae": "竹芋科", "Melastomataceae": "野牡丹科", "Meliaceae": "楝科",
    "Menispermaceae": "防己科", "Moraceae": "桑科", "Musaceae": "芭蕉科", "Myricaceae": "杨梅科",
    "Myrsinaceae": "紫金牛科", "Myrtaceae": "桃金娘科", "Nelumbonaceae": "莲科", "Nyctaginaceae": "紫茉莉科",
    "Nymphaeaceae": "睡莲科", "Oleaceae": "木犀科", "Onagraceae": "柳叶菜科", "Orchidaceae": "兰科",
    "Orobanchaceae": "列当科", "Oxalidaceae": "酢浆草科", "Paeoniaceae": "芍药科", "Palmae": "棕榈科",
    "Pandanaceae": "露兜树科", "Papaveraceae": "罂粟科", "Passifloraceae": "西番莲科", "Pedaliaceae": "胡麻科",
    "Phyllanthaceae": "叶下珠科", "Pinaceae": "松科", "Piperaceae": "胡椒科", "Pittosporaceae": "海桐花科",
    "Plantaginaceae": "车前科", "Plumbaginaceae": "白花丹科", "Poaceae": "禾本科", "Podocarpaceae": "罗汉松科",
    "Polemoniaceae": "花荵科", "Polygalaceae": "远志科", "Polygonaceae": "蓼科", "Polypodiaceae": "水龙骨科",
    "Pontederiaceae": "雨久花科", "Portulacaceae": "马齿苋科", "Primulaceae": "报春花科", "Proteaceae": "山龙眼科",
    "Pteridaceae": "凤尾蕨科", "Punicaceae": "石榴科", "Ranunculaceae": "毛茛科", "Rhamnaceae": "鼠李科",
    "Rosaceae": "蔷薇科", "Rubiaceae": "茜草科", "Rutaceae": "芸香科", "Salicaceae": "杨柳科",
    "Sapindaceae": "无患子科", "Sapotaceae": "山榄科", "Saxifragaceae": "虎耳草科", "Scrophulariaceae": "玄参科",
    "Solanaceae": "茄科", "Strelitziaceae": "旅人蕉科", "Sterculiaceae": "梧桐科", "Taxaceae": "红豆杉科",
    "Taxodiaceae": "杉科", "Theaceae": "山茶科", "Thymelaeaceae": "瑞香科", "Tiliaceae": "椴树科",
    "Tropaeolaceae": "旱金莲科", "Typhaceae": "香蒲科", "Ulmaceae": "榆科", "Umbelliferae": "伞形科",
    "Urticaceae": "荨麻科", "Valerianaceae": "败酱科", "Verbenaceae": "马鞭草科", "Violaceae": "堇菜科",
    "Vitaceae": "葡萄科", "Zingiberaceae": "姜科", "Zygophyllaceae": "蒺藜科"
}


def contains_chinese(text):
    if not text: return False
    for char in text:
        if '\u4e00' <= char <= '\u9fff': return True
    return False


def translate_family_local(latin_family):
    """先查本地字典，没有再联网"""
    if not latin_family: return "未知"
    # 1. 查字典
    if latin_family in FAMILY_DICT:
        return FAMILY_DICT[latin_family]
    # 2. 没查到，尝试去 Wikidata 翻译 (作为补充)
    print(f" (本地字典未收录 {latin_family}，尝试联网翻译)...", end="")
    online = plant_expert.translate_latin_to_chinese(latin_family)
    return online if online else latin_family


def fix_metadata(base_folder):
    if not os.path.exists(base_folder): return

    plant_names = [d for d in os.listdir(base_folder) if os.path.isdir(os.path.join(base_folder, d))]
    total = len(plant_names)
    print(f"🚀 强力清洗 {base_folder}，共 {total} 个...")

    for index, name in enumerate(plant_names):
        plant_dir = os.path.join(base_folder, name)
        info_path = os.path.join(plant_dir, "info.txt")

        print(f"[{index + 1}/{total}] {name} ...", end="", flush=True)

        # 1. 查数据
        info = plant_expert.fetch_plant_info(name)

        if info:
            # --- 强力汉化流程 ---

            # 1. 学名
            sci = info.get('scientific_name')
            if not sci or "Bing" in sci: sci = "未知"

            # 2. 科 (优先用 info 里的中文，没有就查本地字典，再没有就联网)
            fam = info.get('family_cn')
            if not fam or not contains_chinese(fam):
                fam_latin = info.get('family')
                fam = translate_family_local(fam_latin)

            # 3. 属 (优先用 info 里的中文，没有就联网)
            gen = info.get('genus_cn')
            if not gen or not contains_chinese(gen):
                gen_latin = info.get('genus')
                # 属太多了，没法做全字典，只能靠联网
                if gen_latin and gen_latin != "未知":
                    print(f" (翻译属: {gen_latin})...", end="")
                    trans = plant_expert.translate_latin_to_chinese(gen_latin)
                    if trans:
                        gen = trans
                    else:
                        gen = gen_latin  # 实在翻译不了就留拉丁

            # 4. 写入
            try:
                with open(info_path, "w", encoding="utf-8") as f:
                    f.write(f"中文名: {name}\n")
                    f.write(f"学名: {sci}\n")
                    f.write(f"科: {fam if fam else '未知'}\n")
                    f.write(f"属: {gen if gen else '未知'}\n")
                print(f" ✅ (科: {fam})")
            except:
                print(" ❌ 写入失败")
        else:
            print(" ⚠️ 查无资料")
            with open(info_path, "w", encoding="utf-8") as f:
                f.write(f"中文名: {name}\n学名: 未知\n科: 未知\n属: 未知\n")

        time.sleep(0.1)


if __name__ == '__main__':
    print("🔥 启动离线字典增强版清洗...")
    fix_metadata(os.path.join('images', 'common'))
    fix_metadata(os.path.join('images', 'important'))
    print("\n🎉 清洗完成！")4

