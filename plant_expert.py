import requests
import re

# ==========================================
# ⚙️ 配置区域
# ==========================================

# ⚠️ 注意：Streamlit Cloud 云端无法使用 127.0.0.1 的本地魔法
# 但为了防止报错，我们保留这个变量，代码里有 try-except 会自动处理连接失败的情况
PROXIES = {
    "http": "http://127.0.0.1:15732",
    "https": "http://127.0.0.1:15732"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) PlantReviewApp/2.0"
}

# 📖 人工字典
CUSTOM_DICTIONARY = {
    "青苹果竹芋": "Goeppertia orbifolia",
    "发财树": "Pachira glabra",
    "红枫": "Acer palmatum",
    "圆叶刺轴榈": "Licuala grandis",
    "非洲凌霄": "Podranea ricasoliana",
    "橙钟花": "Tecoma alata",
    "黄钟花": "Tecoma stans",
    "硬骨凌霄": "Tecoma capensis",
    "蓝星花": "Oxypetalum coeruleum",
    "茶梅": "Camellia sasanqua"
}


# ==========================================
# 🛠️ 核心工具箱
# ==========================================

def translate_latin_to_chinese(latin_name):
    """
    【新功能】把拉丁名 (如 Rosaceae) 翻译成中文 (如 蔷薇科)
    """
    if not latin_name or latin_name == "未知":
        return latin_name

    url = "https://www.wikidata.org/w/api.php"
    params = {
        "action": "wbsearchentities",
        "search": latin_name,
        "language": "zh",
        "format": "json",
        "limit": 1
    }
    try:
        # 尝试直连 (云端环境)
        resp = requests.get(url, params=params, headers=HEADERS, timeout=3)
        data = resp.json()
        if data.get("search"):
            return data["search"][0].get("label", latin_name)
    except:
        # 如果直连失败，尝试代理 (本地环境)
        try:
            resp = requests.get(url, params=params, headers=HEADERS, timeout=3, proxies=PROXIES)
            data = resp.json()
            if data.get("search"):
                return data["search"][0].get("label", latin_name)
        except:
            pass

    return latin_name


def get_latin_from_wikidata(chinese_name):
    """中文 -> 拉丁"""
    url = "https://www.wikidata.org/w/api.php"
    params = {"action": "wbsearchentities", "search": chinese_name, "language": "zh", "format": "json", "limit": 1}
    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=3)
        data = resp.json()
        if not data.get("search"): return None
        entity_id = data["search"][0]["id"]

        ent_params = {"action": "wbgetentities", "ids": entity_id, "props": "claims", "format": "json"}
        ent_resp = requests.get(url, params=ent_params, headers=HEADERS, timeout=3)
        claims = ent_resp.json().get("entities", {}).get(entity_id, {}).get("claims", {})
        if "P225" in claims:
            return claims["P225"][0]["mainsnak"]["datavalue"]["value"]
    except:
        pass
    return None


def get_latin_from_inaturalist(chinese_name):
    """中文 -> 拉丁 (iNat)"""
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
    """GBIF 查详情"""
    try:
        r1 = requests.get("https://api.gbif.org/v1/species/search",
                          params={"q": query_name, "limit": 1}, headers=HEADERS, timeout=5)
        d1 = r1.json()
        if not d1['results']: return None
        sp = d1['results'][0]
        if sp.get('rank') in ['CLASS', 'ORDER', 'PHYLUM', 'KINGDOM']: return None

        key = sp.get('key')

        family_latin = sp.get('family', '未知')
        genus_latin = sp.get('genus', '未知')

        result = {
            "name_cn": query_name,
            "scientific_name": sp.get('scientificName', '未知'),
            "family": family_latin,
            "genus": genus_latin,
            "image_url": None
        }

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
    """Wiki 搜图"""
    url = "https://commons.wikimedia.org/w/api.php"
    params = {"action": "query", "generator": "search", "gsrsearch": f"{scientific_name} filetype:bitmap",
              "gsrlimit": 1, "prop": "imageinfo", "iiprop": "url", "format": "json"}
    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=5)
        pages = r.json().get("query", {}).get("pages", {})
        for _, val in pages.items(): return val.get("imageinfo", [{}])[0].get("url")
    except:
        pass
    return None


def search_bing_image(keyword):
    """Bing 搜图"""
    try:
        url = "https://www.bing.com/images/search"
        params = {"q": f"{keyword} plant", "first": 1, "count": 1}
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

    if plant_name in CUSTOM_DICTIONARY:
        latin_name = CUSTOM_DICTIONARY[plant_name]
        print(f" (字典: {latin_name})", end="")

    if not latin_name:
        latin_name = get_latin_from_wikidata(plant_name)
        if latin_name: print(f" (Wiki: {latin_name})", end="")

    if not latin_name:
        latin_name, fallback_image = get_latin_from_inaturalist(plant_name)
        if latin_name: print(f" (iNat: {latin_name})", end="")

    search_term = latin_name if latin_name else plant_name

    # 1. 查 GBIF
    final_info = _query_gbif(search_term)

    if not final_info:
        final_info = {
            "name_cn": plant_name,
            "scientific_name": search_term,
            "family": "未知",
            "genus": search_term.split()[0] if search_term else "未知",
            "image_url": None
        }
    else:
        final_info["name_cn"] = plant_name

    # 2. 补图
    if not final_info['image_url'] and latin_name:
        wiki_img = get_image_from_wikimedia(latin_name)
        if wiki_img: final_info['image_url'] = wiki_img

    if not final_info['image_url']:
        print(" -> 启用Bing...", end="")
        bing_query = latin_name if latin_name else f"{plant_name} 植物"
        bing_img = search_bing_image(bing_query)
        if bing_img: final_info['image_url'] = bing_img

    if not final_info['image_url'] and fallback_image:
        final_info['image_url'] = fallback_image

    # 3. 翻译科属 (这里调用了新函数)
    print(" -> 翻译科属...", end="")
    final_info['family_cn'] = translate_latin_to_chinese(final_info.get('family'))
    final_info['genus_cn'] = translate_latin_to_chinese(final_info.get('genus'))
    print(" 完成 ✅")

    return final_info