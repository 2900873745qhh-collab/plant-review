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
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) PlantReviewApp/4.0"
}

# 📖 人工字典 (优先级最高，用于修正顽固分子)
# 如果这里写了，程序就绝对听你的
CUSTOM_DICTIONARY = {
    "青苹果竹芋": {"latin": "Goeppertia orbifolia", "family": "竹芋科", "genus": "肖竹芋属"},
    "发财树": {"latin": "Pachira glabra", "family": "锦葵科", "genus": "瓜栗属"},
    "红枫": {"latin": "Acer palmatum", "family": "无患子科", "genus": "槭属"},
    "圆叶刺轴榈": {"latin": "Licuala grandis", "family": "棕榈科", "genus": "轴榈属"},
    "白玉黛粉芋": {"latin": "Dieffenbachia seguine", "family": "天南星科", "genus": "花叶万年青属"},
    "绿萝": {"latin": "Epipremnum aureum", "family": "天南星科", "genus": "麒麟叶属"},
    "罗勒": {"latin": "Ocimum basilicum", "family": "唇形科", "genus": "罗勒属"}
}


# ==========================================
# 🧬 核心功能：科属补全计划 (新增)
# ==========================================

def enrich_taxonomy_from_inat(latin_name):
    """
    【家谱调查】拿着拉丁学名，去 iNaturalist 查它的中文科属
    """
    if not latin_name or latin_name == "未知": return None, None

    url = "https://api.inaturalist.org/v1/taxa"
    params = {
        "q": latin_name,
        "rank": "species",  # 或者是 variety
        "locale": "zh-CN",  # 🚨 关键：告诉它我要中文名
        "per_page": 1
    }

    try:
        # iNat 不需要代理，直接连
        resp = requests.get(url, params=params, headers=HEADERS, timeout=5)
        data = resp.json()

        if data['results']:
            result = data['results'][0]
            family_cn = None
            genus_cn = None

            # iNat 会返回一个 ancestors (祖先) 列表，里面包含了科和属
            if 'ancestors' in result:
                for ancestor in result['ancestors']:
                    if ancestor['rank'] == 'family':
                        # 优先取中文俗名，没有则取拉丁名
                        family_cn = ancestor.get('preferred_common_name', ancestor['name'])
                    if ancestor['rank'] == 'genus':
                        genus_cn = ancestor.get('preferred_common_name', ancestor['name'])

            return family_cn, genus_cn

    except Exception as e:
        print(f"科属补全失败: {e}")
        pass

    return None, None


# ==========================================
# 🛠️ 基础工具箱 (保持原样或微调)
# ==========================================

def translate_latin_to_chinese(latin_name):
    """Wikidata 简单翻译 (备用)"""
    if not latin_name or latin_name in ["未知", "None"]: return None
    url = "https://www.wikidata.org/w/api.php"
    params = {"action": "wbsearchentities", "search": latin_name, "language": "zh", "format": "json", "limit": 1}
    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=3, proxies=PROXIES)
        data = resp.json()
        if data.get("search"): return data["search"][0].get("label", latin_name)
    except:
        pass
    return latin_name


def get_latin_from_wikidata(chinese_name):
    url = "https://www.wikidata.org/w/api.php"
    params = {"action": "wbsearchentities", "search": chinese_name, "language": "zh", "format": "json", "limit": 1}
    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=3, proxies=PROXIES)
        data = resp.json()
        if data.get("search"): return data["search"][0].get("id")  # 返回ID方便后续查
    except:
        pass
    return None


def get_name_by_id(entity_id):
    """根据 Wiki ID 查学名 P225"""
    url = "https://www.wikidata.org/w/api.php"
    params = {"action": "wbgetentities", "ids": entity_id, "props": "claims", "format": "json"}
    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=3, proxies=PROXIES)
        claims = resp.json().get("entities", {}).get(entity_id, {}).get("claims", {})
        if "P225" in claims: return claims["P225"][0]["mainsnak"]["datavalue"]["value"]
    except:
        pass
    return None


def get_latin_from_inaturalist(chinese_name):
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
    try:
        r1 = requests.get("https://api.gbif.org/v1/species/search", params={"q": query_name, "limit": 1},
                          headers=HEADERS, timeout=5)
        d1 = r1.json()
        if not d1['results']: return None
        sp = d1['results'][0]
        if sp.get('rank') in ['CLASS', 'ORDER', 'PHYLUM', 'KINGDOM']: return None

        result = {
            "name_cn": query_name,
            "scientific_name": sp.get('scientificName', None),
            "family": sp.get('family', None),  # 这里只有拉丁文
            "genus": sp.get('genus', None),  # 这里只有拉丁文
            "image_url": None
        }

        r2 = requests.get("https://api.gbif.org/v1/occurrence/search",
                          params={"taxonKey": sp.get('key'), "mediaType": "StillImage", "limit": 1}, headers=HEADERS,
                          timeout=5)
        d2 = r2.json()
        if d2['results']:
            media = d2['results'][0].get('media', [])
            if media: result["image_url"] = media[0].get('identifier')
        return result
    except:
        return None


def get_image_from_wikimedia(scientific_name):
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

    # 1. 查字典 (字典里现在可以直接定义科属，一步到位)
    if plant_name in CUSTOM_DICTIONARY:
        entry = CUSTOM_DICTIONARY[plant_name]
        # 如果字典里不仅有拉丁，还有科属，直接返回！
        if isinstance(entry, dict):
            print(f" (完美字典命中) ✅")
            # 尝试去搜个图
            img_url = None
            gbif_data = _query_gbif(entry['latin'])
            if gbif_data: img_url = gbif_data['image_url']
            if not img_url: img_url = search_bing_image(entry['latin'])

            return {
                "name_cn": plant_name,
                "scientific_name": entry['latin'],
                "family": entry.get('family'),  # 字典里已经是中文了
                "genus": entry.get('genus'),  # 字典里已经是中文了
                "family_cn": entry.get('family'),
                "genus_cn": entry.get('genus'),
                "image_url": img_url
            }
        else:
            latin_name = entry  # 旧版字典格式兼容

    # 2. 查学名
    if not latin_name:
        wiki_id = get_latin_from_wikidata(plant_name)
        if wiki_id: latin_name = get_name_by_id(wiki_id)

    if not latin_name:
        latin_name, fallback_image = get_latin_from_inaturalist(plant_name)

    search_term = latin_name if latin_name else plant_name

    # 3. 构造基础数据
    final_info = {
        "name_cn": plant_name,
        "scientific_name": search_term,
        "family": None, "genus": None, "image_url": None,
        "family_cn": None, "genus_cn": None
    }

    # 4. 搜图 (GBIF -> Wiki -> Bing)
    gbif_data = _query_gbif(search_term)
    if gbif_data:
        final_info.update(gbif_data)
        final_info['name_cn'] = plant_name

    if not final_info['image_url'] and latin_name:
        wiki_img = get_image_from_wikimedia(latin_name)
        if wiki_img: final_info['image_url'] = wiki_img

    if not final_info['image_url']:
        bing_img = search_bing_image(search_term + " plant")
        if bing_img: final_info['image_url'] = bing_img

    if not final_info['image_url'] and fallback_image:
        final_info['image_url'] = fallback_image

    # ----------------------------------------------------
    # 🌟 关键步骤：去 iNaturalist 查中文家谱
    # ----------------------------------------------------
    if final_info['scientific_name'] and final_info['scientific_name'] != "未知":
        print(" -> 查家谱...", end="")
        fam_cn, gen_cn = enrich_taxonomy_from_inat(final_info['scientific_name'])

        # 只有当查到了新的中文名，才覆盖原来的
        if fam_cn: final_info['family_cn'] = fam_cn
        if gen_cn: final_info['genus_cn'] = gen_cn

        # 如果原来 family 是拉丁文，现在没查到中文，就尝试用 Wikidata 简单翻译
        if not final_info['family_cn'] and final_info['family']:
            final_info['family_cn'] = translate_latin_to_chinese(final_info['family'])
        if not final_info['genus_cn'] and final_info['genus']:
            final_info['genus_cn'] = translate_latin_to_chinese(final_info['genus'])

    print(" 完成 ✅")
    return final_info