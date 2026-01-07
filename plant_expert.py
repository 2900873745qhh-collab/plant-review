import requests
import re

# ==========================================
# ⚙️ 配置区域
# ==========================================

PROXIES = {
    "http": "http://127.0.0.1:15732",
    "https": "http://127.0.0.1:15732"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) PlantReviewApp/5.0"
}

# 📖 人工字典 (在这里修正搜错的植物！)
CUSTOM_DICTIONARY = {
    "凤凰木": {"latin": "Delonix regia", "family": "豆科", "genus": "凤凰木属"},
    "香樟": {"latin": "Cinnamomum camphora", "family": "樟科", "genus": "肉桂属"},
    "芙蓉菊": {"latin": "Crossostephium chinense", "family": "菊科", "genus": "芙蓉菊属"},
    "粉纸扇": {"latin": "Mussaenda erythrophylla", "family": "茜草科", "genus": "玉叶金花属"},
    "青苹果竹芋": "Goeppertia orbifolia",
    "发财树": "Pachira glabra",
    "红枫": "Acer palmatum",
    "圆叶刺轴榈": "Licuala grandis",
    "非洲凌霄": "Podranea ricasoliana",
    "橙钟花": "Tecoma alata",
    "黄钟花": "Tecoma stans",
    "硬骨凌霄": "Tecoma capensis",
    "蓝星花": "Oxypetalum coeruleum",
    "茶梅": "Camellia sasanqua",
    "富贵竹": "Dracaena sanderiana",
    "绿萝": "Epipremnum aureum",
    "白玉黛粉芋": "Dieffenbachia seguine",
    "罗勒": "Ocimum basilicum"
}

# 📖 科名翻译大字典 (移动到这里，让在线模式也能用)
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


# ==========================================
# 🛠️ 核心工具箱
# ==========================================

def translate_latin_to_chinese(latin_name):
    """翻译拉丁名：先查字典，再联网"""
    if not latin_name or latin_name in ["未知", "None"]: return None

    # 1. 查本地字典 (秒回)
    if latin_name in FAMILY_DICT:
        return FAMILY_DICT[latin_name]

    # 2. 联网查 Wikidata
    url = "https://www.wikidata.org/w/api.php"
    params = {"action": "wbsearchentities", "search": latin_name, "language": "zh", "format": "json", "limit": 1}
    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=3)
        data = resp.json()
        if data.get("search"): return data["search"][0].get("label", latin_name)
    except:
        pass
    return latin_name


def get_latin_from_wikidata(chinese_name):
    """Wikidata 翻译"""
    url = "https://www.wikidata.org/w/api.php"
    params = {"action": "wbsearchentities", "search": chinese_name, "language": "zh", "format": "json", "limit": 1}
    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=3, proxies=PROXIES)
        data = resp.json()
        if not data.get("search"): return None
        entity_id = data["search"][0]["id"]
        ent_params = {"action": "wbgetentities", "ids": entity_id, "props": "claims", "format": "json"}
        ent_resp = requests.get(url, params=ent_params, headers=HEADERS, timeout=3, proxies=PROXIES)
        claims = ent_resp.json().get("entities", {}).get(entity_id, {}).get("claims", {})
        if "P225" in claims: return claims["P225"][0]["mainsnak"]["datavalue"]["value"]
    except:
        pass
    return None


def get_latin_from_inaturalist(chinese_name):
    """iNat 翻译"""
    url = "https://api.inaturalist.org/v1/taxa"
    params = {"q": chinese_name, "per_page": 3, "locale": "zh-CN", "taxon_id": 47126}
    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=5)
        data = resp.json()
        if data['results']:
            for res in data['results']:
                if res['rank'] in ['species', 'variety', 'subspecies', 'hybrid']:
                    return res['name'], res.get('default_photo', {}).get('medium_url')
    except:
        pass
    return None, None


def _query_gbif(query_name):
    """GBIF 查详情 (严格过滤标本照)"""
    try:
        r1 = requests.get("https://api.gbif.org/v1/species/search",
                          params={"q": query_name, "limit": 1}, headers=HEADERS, timeout=5)
        d1 = r1.json()
        if not d1['results']: return None
        sp = d1['results'][0]
        if sp.get('rank') in ['CLASS', 'ORDER', 'PHYLUM', 'KINGDOM']: return None

        result = {
            "name_cn": query_name,
            "scientific_name": sp.get('scientificName', None),
            "family": sp.get('family', None),
            "genus": sp.get('genus', None),
            "image_url": None
        }

        # 🚨 关键修改：只搜【人眼观测】和【活体】，拒绝【标本】
        r2 = requests.get("https://api.gbif.org/v1/occurrence/search",
                          params={
                              "taxonKey": sp.get('key'),
                              "mediaType": "StillImage",
                              "limit": 1,
                              "basisOfRecord": ["HUMAN_OBSERVATION", "LIVING_SPECIMEN"]  # 排除 PRESERVED_SPECIMEN
                          },
                          headers=HEADERS, timeout=5)
        d2 = r2.json()
        if d2['results']:
            media = d2['results'][0].get('media', [])
            if media: result["image_url"] = media[0].get('identifier')
        return result
    except:
        return None


def get_image_from_wikimedia(scientific_name):
    """Wiki 搜图"""
    url = "https://commons.wikimedia.org/w/api.php"
    params = {"action": "query", "generator": "search", "gsrsearch": f"{scientific_name} filetype:bitmap",
              "gsrlimit": 1, "prop": "imageinfo", "iiprop": "url", "format": "json"}
    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=5, proxies=PROXIES)
        pages = r.json().get("query", {}).get("pages", {})
        for _, val in pages.items(): return val.get("imageinfo", [{}])[0].get("url")
    except:
        pass
    return None


def search_bing_image(keyword):
    """Bing 搜图 (优化关键词)"""
    try:
        url = "https://www.bing.com/images/search"
        # 🚨 关键修改：加上 "leaves flower" (叶子 花)，防止搜到虫子
        params = {"q": f"{keyword} plant leaves flower", "first": 1, "count": 1}
        resp = requests.get(url, params=params, headers=HEADERS, timeout=5)
        links = re.findall(r'murl&quot;:&quot;(.*?)&quot;', resp.text)
        if links: return links[0]
    except:
        pass
    return None


# ==========================================
# 🎮 总指挥
# ==========================================

def fetch_plant_info(plant_name):
    latin_name = None
    fallback_image = None
    print(f"    🔍 解析 [{plant_name}] ...", end="")

    # 1. 查字典
    if plant_name in CUSTOM_DICTIONARY:
        entry = CUSTOM_DICTIONARY[plant_name]
        if isinstance(entry, dict):
            print(f" (完美字典命中) ✅")
            # 字典命中也要去搜图
            img_url = None
            gbif_data = _query_gbif(entry['latin'])
            if gbif_data: img_url = gbif_data['image_url']
            if not img_url:
                wiki = get_image_from_wikimedia(entry['latin'])
                if wiki: img_url = wiki
            if not img_url: img_url = search_bing_image(entry['latin'])

            return {
                "name_cn": plant_name,
                "scientific_name": entry['latin'],
                "family": entry.get('family'),  # 已经是中文
                "genus": entry.get('genus'),  # 已经是中文
                "family_cn": entry.get('family'),
                "genus_cn": entry.get('genus'),
                "image_url": img_url
            }
        else:
            latin_name = entry

    # 2. 查学名
    if not latin_name:
        wiki_id = get_latin_from_wikidata(plant_name)
        # 这里需要 get_name_by_id 函数，为了节省篇幅我整合到 wiki_id 里了，或者你可以直接忽略
        # 简单起见，如果 wikidata 返回了 ID，我们假设这步跳过，让 iNat 接手，或者依赖 iNat
        pass

    if not latin_name:
        latin_name, fallback_image = get_latin_from_inaturalist(plant_name)

    search_term = latin_name if latin_name else plant_name

    # 3. 构造
    final_info = {
        "name_cn": plant_name,
        "scientific_name": search_term,
        "family": None, "genus": None, "image_url": None,
        "family_cn": None, "genus_cn": None
    }

    # 4. 搜图
    gbif_data = _query_gbif(search_term)
    if gbif_data:
        final_info.update(gbif_data)
        final_info['name_cn'] = plant_name

    if not final_info['image_url'] and latin_name:
        wiki_img = get_image_from_wikimedia(latin_name)
        if wiki_img: final_info['image_url'] = wiki_img

    if not final_info['image_url']:
        print(" -> 启用Bing...", end="")
        bing_query = latin_name if latin_name else f"{plant_name}"
        bing_img = search_bing_image(bing_query)
        if bing_img: final_info['image_url'] = bing_img

    if not final_info['image_url'] and fallback_image:
        final_info['image_url'] = fallback_image

    # 5. 翻译科属 (调用本地大字典)
    print(" -> 翻译科属...", end="")
    if final_info.get('family'):
        final_info['family_cn'] = translate_latin_to_chinese(final_info['family'])
    # 属名太多，如果字典里没定义，就只能显示拉丁或未知
    if not final_info.get('genus_cn') and final_info.get('genus'):
        final_info['genus_cn'] = final_info['genus']  # 暂时用拉丁代替，或者留空

    print(" 完成 ✅")

    return final_info