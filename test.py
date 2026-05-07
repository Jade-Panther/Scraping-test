import requests

def scientific_to_common(scientific_name):
    url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + scientific_name.replace(" ", "_")

    headers = {
        "User-Agent": "scientific-name-converter/1.0"
    }

    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        return None

    data = r.json()

    return data.get("title")


print(scientific_to_common("Accipiter striatus"))


import requests

def common_to_scientific(common_name):
    url = "https://www.wikidata.org/w/api.php"

    params = {
        "action": "wbsearchentities",
        "search": common_name,
        "language": "en",
        "format": "json",
        "limit": 10
    }

    headers = {
        "User-Agent": "common-to-scientific/1.0"
    }

    r = requests.get(url, params=params, headers=headers)
    data = r.json()

    if "search" not in data:
        return None

    for item in data["search"]:
        qid = item["id"]

        # fetch entity details
        entity_url = f"https://www.wikidata.org/wiki/Special:EntityData/{qid}.json"
        entity = requests.get(entity_url, headers=headers).json()

        ent = entity["entities"][qid]

        # P225 = taxon name (scientific name)
        claims = ent.get("claims", {})
        if "P225" in claims:
            return claims["P225"][0]["mainsnak"]["datavalue"]["value"]

    return None


print(common_to_scientific("white-tailed deer"))