import json
import requests
import operator

def ladda_ner_api(uri):
    response = requests.get(url = uri)
    data = response.text
    json_data = json.loads(data)
    return json_data

def hämta_yrkesutbildningar():
    uri = "https://susanavet2.skolverket.se/api/1.1/infos?vocational=true&page=0&size=20000000"
    json_data = ladda_ner_api(uri)
    return json_data

def hämta_utbildningstillfällen():
    uri = "https://susanavet2.skolverket.se/api/1.1/events?vocational=True&page=0&size=20000000"
    json_data = ladda_ner_api(uri)
    return json_data

def spara_aub_med_ssyk(utbildningar, utb_tillfällen):
    utb_id_orter = {}
    for i in utb_tillfällen["content"]:
        info = i["content"]["educationEvent"]
        if "location" in info:
            orter = []
            for l in info["location"]:
                if "town" in l:
                    orter.append(str(l["town"]))
            if orter:
                utb_id_orter[info["education"]] = orter
    utbildningsdata = {}
    for i in utbildningar["content"]:
        info = i["content"]["educationInfo"]
        id = info["identifier"]
        tillfällen = utb_id_orter.get(id)
        if tillfällen:
            if "subject" in info:
                ssyk = []
                for s in info["subject"]:
                    if s ["type"] == "AUB_Subject":
                        ssyk.append(s["code"])
                if ssyk:
                    ssyk = [str(i) for i in ssyk]
                    for s in ssyk:
                        if not s in utbildningsdata:
                            utbildningsdata[s] = []
                        data = {
                            "utbildningsnamn": info["title"]["string"][0]["content"],
                            "beskrivning": info["description"]["string"][0]["content"].replace("<![CDATA[", "").replace("]]>", ""),
                            "url": info["url"]["url"][0]["content"],
                            "ort": tillfällen[0]}
                        utbildningsdata[s].append(data)
    for key in utbildningsdata:
        utbildningsdata[key] = sorted(utbildningsdata[key], key = operator.itemgetter("ort"))
    return utbildningsdata

def import_aub_from_susa():
    yrkesutb = hämta_yrkesutbildningar()
    utb_tillfällen_data = hämta_utbildningstillfällen()
    bara_aub = spara_aub_med_ssyk(yrkesutb, utb_tillfällen_data)
    return bara_aub