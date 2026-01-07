import requests
import re

# ==========================================
# ⚙️ 配置区域
# ==========================================

# 魔法配置 (你的端口 15732)
PROXIES = {
    "http": "http://127.0.0.1:15732",
    "https": "http://127.0.0.1:15732"
}

# 伪装头部 (非常重要！没有这个维基百科会拒绝连接)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) PlantReviewApp/1.0 (mailto:youremail@example.com)"
}

# 📖 人工字典 (你的保命符)
CUSTOM_DICTIONARY = {
    "青苹果竹芋": "Goeppertia orbifolia",
    "发财树": "Pachira glabra",
    "红枫": "Acer palmatum",
    "圆叶刺轴榈": "Licuala grandis",  # 帮你补上了
    "非洲凌霄": "Podranea ricasoliana",  # 帮你补上了
    "橙钟花": "Tecoma alata",  # 帮你补上了
    "黄钟花": "Tecoma stans",
    "硬骨凌霄": "Tecoma capensis",
    "蓝星花": "Oxypetalum coeruleum"
}


# ==========================================
# 搜索引擎模块
# ==========================================

def search_bing_image(keyword):
    """
    【核武器】Bing 搜图 (只搜学名，保证准确且有图)
    """
    try:
        url = "https://www.bing.com/images/search"
        # 搜索学名 + "plant" 确保万无一失
        params = {"q": f"{keyword} plant", "first": 1, "count": 1}
        # Bing 不需要代理通常也能连，如果连不上会自动跳过
        resp = requests.get(url, params=params, headers=HEADERS, timeout=5)

        # 使用正则提取图片链接 (Bing 的页面结构)
        # 这是一个简单的提取逻辑，通常能拿到第一张大图
        links = re.findall(r'murl&quot;:&quot;(.*?)&quot;', resp.text)
        if links:
            return links[0]
    except:
        pass
    return None


def get_latin_from_wikidata(chinese_name):
    """【翻译官 1】Wikidata"""
    url = "https://www.wikidata.org/w/api.php"
    params = {
        "action": "wbsearchentities", "search": chinese_name,
        "language": "zh", "format": "json", "limit": 1
    }
    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=5, proxies=PROXIES)
        data = resp.json()
        if not data.get("search"): return None
        entity_id = data["search"][0]["id"]

        ent_params = {"action": "wbgetentities", "ids": entity_id, "props": "claims", "format": "json"}
        ent_resp = requests.get(url, params=ent_params, headers=HEADERS, timeout=5, proxies=PROXIES)
        claims = ent_resp.json().get("entities", {}).get(entity_id, {}).get("claims", {})
        if "P225" in claims:
            return claims["P225"][0]["mainsnak"]["datavalue"]["value"]
    except:
        pass
    return None


def get_latin_from_inaturalist(chinese_name):
    """【翻译官 2】iNaturalist"""
    url = "https://api.inaturalist.org/v1/taxa"
    params = {"q": chinese_name, "per_page": 3, "locale": "zh-CN", "taxon_id": 47126}
    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=5)  # iNat 一般不用代理
        data = resp.json()
        if data['results']:
            for res in data['results']:
                if res['rank'] in ['species', 'variety', 'subspecies', 'hybrid']:
                    return res['name'], res.get('default_photo', {}).get('medium_url')
    except:
        pass
    return None, None


def _query_gbif(query_name):
    """【图库 A】GBIF"""
    try:
        r1 = requests.get("https://api.gbif.org/v1/species/search",
                          params={"q": query_name, "limit": 1}, headers=HEADERS, timeout=5)
        d1 = r1.json()
        if not d1['results']: return None
        sp = d1['results'][0]
        # 排除非物种
        if sp.get('rank') in ['CLASS', 'ORDER', 'PHYLUM', 'KINGDOM']: return None

        key = sp.get('key')
        result = {
            "name_cn": query_name,
            "scientific_name": sp.get('scientificName', '未知'),
            "family": sp.get('family', '未知'),
            "genus": sp.get('genus', '未知'),
            "image_url": None
        }

        # 搜图
        r2 = requests.get("https://api.gbif.org/v1/occurrence/search",
                          params={"taxonKey": key, "mediaType": "StillImage", "limit": 1},
                          headers=HEADERS, timeout=5)
        d2 = r2.json()
        if d2['results']:
            media = d2['results'][0].get('media', [])
            if media: result["image_url"] = media[0].get('identifier')
        return result
    except:
        return None


def get_image_from_wikimedia(scientific_name):
    """【图库 B】Wiki"""
    url = "https://commons.wikimedia.org/w/api.php"
    params = {
        "action": "query", "generator": "search",
        "gsrsearch": f"{scientific_name} filetype:bitmap",
        "gsrlimit": 1, "prop": "imageinfo", "iiprop": "url", "format": "json"
    }
    try:
        # Wiki 必须加 User-Agent 头，否则必挂
        r = requests.get(url, params=params, headers=HEADERS, timeout=5, proxies=PROXIES)
        pages = r.json().get("query", {}).get("pages", {})
        for _, val in pages.items():
            return val.get("imageinfo", [{}])[0].get("url")
    except:
        pass
    return None


# ==========================================
# 总指挥
# ==========================================

def fetch_plant_info(plant_name):
    latin_name = None
    fallback_image = None  # iNat 图

    print(f"    🔍 解析 [{plant_name}] ...", end="")

    # 1. 查字典
    if plant_name in CUSTOM_DICTIONARY:
        latin_name = CUSTOM_DICTIONARY[plant_name]
        print(f" (字典命中: {latin_name})", end="")

    # 2. 查 Wiki
    if not latin_name:
        latin_name = get_latin_from_wikidata(plant_name)
        if latin_name: print(f" (Wiki锁定: {latin_name})", end="")

    # 3. 查 iNat
    if not latin_name:
        latin_name, fallback_image = get_latin_from_inaturalist(plant_name)
        if latin_name: print(f" (iNat锁定: {latin_name})", end="")

    # 决定用什么名字去搜图
    search_term = latin_name if latin_name else plant_name

    # --- 构造基础信息 ---
    final_info = {
        "name_cn": plant_name,
        "scientific_name": search_term,
        "family": "暂未获取",
        "genus": search_term.split()[0] if search_term else "未知",
        "image_url": None
    }

    # --- 搜图大作战 ---

    # 尝试 A: GBIF
    gbif_data = _query_gbif(search_term)
    if gbif_data and gbif_data['image_url']:
        final_info.update(gbif_data)
        final_info['name_cn'] = plant_name
        print(" -> GBIF有图 ✅")
        return final_info

    # 尝试 B: Wiki (必须有学名)
    if not final_info['image_url'] and latin_name:
        wiki_img = get_image_from_wikimedia(latin_name)
        if wiki_img:
            final_info['image_url'] = wiki_img
            print(" -> Wiki有图 ✅")
            return final_info

    # 尝试 C: Bing (最后的救星)
    if not final_info['image_url']:
        print(" -> 专业库无图，启动Bing...", end="")
        # 如果有学名，用学名搜；没有学名，用中文+植物搜
        bing_query = latin_name if latin_name else f"{plant_name} 植物"
        bing_img = search_bing_image(bing_query)
        if bing_img:
            final_info['image_url'] = bing_img
            final_info['family'] = "来源: Bing搜索"
            print(" Bing有图 ✅")
            return final_info

    # 尝试 D: iNat 保底
    if not final_info['image_url'] and fallback_image:
        final_info['image_url'] = fallback_image
        print(" -> iNat保底 ✅")
        return final_info

    print(" ❌ 彻底无图")
    return None