import streamlit as st
import re
import json
import math
import requests
from matplotlib import pyplot as plt
from matplotlib_venn import venn2
from wordcloud import WordCloud
import datetime
from google.cloud import storage
from google.oauth2 import service_account
from aub_susa import import_aub_from_susa

@st.cache_data
def import_data(filename):
    with open(filename) as file:
        content = file.read()
    output = json.loads(content)
    return output

def show_initial_information():
    st.logo("af-logotyp-rgb-540px.jpg")
    st.title(":primary[Yrkesinfo]")
    initial_text = "Ett försöka att erbjuda information/stöd för arbetsförmedlare när det kommer till att välja <em>rätt</em> yrke och underlätta relaterade informerade bedömningar och beslut när det kommer till GYR-Y (Geografisk och yrkesmässig rörlighet - Yrke). Informationen är taxonomi-, statistik- och annonsdriven. 1180 yrkesbenämningar bedöms ha tillräckligt annonsunderlag för pålitliga beräkningar. Resterande yrkesbenämningar kompletteras med beräkningar på yrkesgruppsnivå."
    st.markdown(f"<p style='font-size:12px;'>{initial_text}</p>", unsafe_allow_html=True)

def initiate_session_state():
    if "occupationdata" not in st.session_state:
        st.session_state.occupationdata = import_data("all_valid_occupations_with_info_v25.json")
    if "valid_occupations" not in st.session_state:
        st.session_state.valid_occupations = import_data("valid_occupations.json")
    if "valid_occupations_no_educational_req" not in st.session_state:
        st.session_state.valid_occupations_no_educational_req = import_data("valid_occupations_no_educational_req.json")
    if "adwords" not in st.session_state:
        st.session_state.adwords = import_data("all_wordclouds_v25.json")
    if "ad_data_historical" not in st.session_state:
        st.session_state.ad_data_historical = import_data("ssyk_region_kommun_annonser_2024.json")
    if "ad_data_platsbanken" not in st.session_state:
        st.session_state.ad_data_platsbanken = import_data("platsbanken.json")
    if "competence_descriptions" not in st.session_state:
        st.session_state.competence_descriptions = import_data("kompetens_beskrivning.json")
    if "labour_flow" not in st.session_state:
        st.session_state.labour_flow = import_data("labour_flow_data.json")
    if "forecast" not in st.session_state:
        st.session_state.forecast = import_data("barometer_regional.json")
    if "ssyk_salary" not in st.session_state:
        st.session_state.ssyk_salary = import_data("ssyk_salary.json")
    if "aub_data" not in st.session_state:
        st.session_state.aub_data = import_aub_from_susa()
    if "regions" not in st.session_state:
        st.session_state.regions = import_data("region_name_id.json")
    if "locations_id" not in st.session_state:
        st.session_state.locations_id = import_data("ort_namn_id.json")
    if "geodata" not in st.session_state:
        st.session_state.geodata = import_data("ort_ort_relevans.json")
    if "municipality_id_namn" not in st.session_state:
        st.session_state.municipality_id_namn = import_data("kommun_id_namn.json")
    if "occupation_id_dk_preflabel" not in st.session_state:
        st.session_state.occupation_id_dk_preflabel = import_data("occupation_id_dk_preflabel.json")
    if "adwords_occupation" not in st.session_state:
        st.session_state.adwords_occupation = {}
    if "credentials" not in st.session_state:
        credentials_dict = st.secrets["gcp_service_account"]
        st.session_state.credentials = service_account.Credentials.from_service_account_info(credentials_dict)
    if "valid_occupation_names" not in st.session_state:
        st.session_state.valid_occupation_names = sorted(list(st.session_state.valid_occupations.keys()))
    if "valid_occupations_names_no_educational_req" not in st.session_state:
        st.session_state.valid_occupations_names_no_educational_req = sorted(list(st.session_state.valid_occupations_no_educational_req.keys()))
    if "valid_locations" not in st.session_state:
        st.session_state.valid_locations = list(st.session_state.locations_id.keys())

def load_feedback():
    """Ladda befintlig feedback från GCS."""
    storage_client = storage.Client(credentials = st.session_state.credentials, project = st.session_state.credentials.project_id)
    bucket = storage_client.bucket("androjons_bucket")
    blob = bucket.blob("feedback.json")

    if blob.exists():
        data = blob.download_as_text()
        return json.loads(data)
    else:
        return []

def save_feedback(feedback_data):
    """Spara feedback till GCS."""
    storage_client = storage.Client(credentials = st.session_state.credentials, project = st.session_state.credentials.project_id)
    bucket = storage_client.bucket("androjons_bucket")
    blob = bucket.blob("feedback.json")
    json_string = json.dumps(feedback_data, indent = 2, ensure_ascii = False)
    json_bytes = json_string.encode("utf-8")
    blob.upload_from_string(json_bytes, content_type = "application/json; charset=utf-8")

@st.dialog("Återkoppling")
def dialog_(selected_occupation, tab_name, questions, selected_location = None):
    stars = st.feedback("stars", key = f"{tab_name}_stars")
    answers = {}
    for q in questions:
        answers[q] = st.text_area(label = q, key = f"{q}")

    if st.button("Spara återkoppling", key=f"{tab_name}_save_button"):
        feedback = load_feedback()
        new_entry = {
            "tid": datetime.datetime.now().isoformat(),
            "selected_occupation": selected_occupation,
            "selected_tab": tab_name,
            "kommentarer": answers,
            "version": "Allmän"
        }
        if stars is not None:
            new_entry["stars"] = stars
        if selected_location is not None:
            new_entry["selected_location"] = selected_location
        feedback.append(new_entry)
        save_feedback(feedback)
        st.session_state[f"{tab_name}_feedback_saved"] = True
        st.rerun()

@st.fragment
def create_feedback(occupation_name, tab_name, questions, selected_location = None):
    if st.button(f"Återkoppla {tab_name}", key = f"{tab_name}_button"):
        dialog_(occupation_name, tab_name, questions, selected_location)
    if st.session_state[f"{tab_name}_feedback_saved"] == True:
        st.success("Återkoppling sparad. Tack!")

def create_tree(field, group, occupation, barometer, bold, yrkessamling = None, reglerad = None):
    SHORT_ELBOW = "└─"
    SPACE_PREFIX = "&nbsp;&nbsp;&nbsp;&nbsp;"
    LONG_PREFIX = "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
    strings = [f"{field}"]
    if barometer:
        barometer_name = barometer[0]
        if "barometer" in bold:
            barometer_name = f"<strong>{barometer_name}</strong>"
    if "occupation" in bold:
        occupation = f"<strong>{occupation}</strong>"
    if "group" in bold:
        group = f"<strong>{group}</strong>"

    if yrkessamling == "Kultur":
        occupation = f"{occupation} hanteras av AF Kultur"
    elif yrkessamling == "Sjöfart":
        occupation = f"{occupation} hanteras av AF Sjöfart"

    if reglerad:
        occupation = f"{occupation} Reglerat yrke"

    if barometer:
        if barometer[1] == True:
            strings.append(f"{SHORT_ELBOW}  {barometer_name}")
            strings.append(f"{SPACE_PREFIX}{SHORT_ELBOW}  {group}")
            strings.append(f"{SPACE_PREFIX}{SPACE_PREFIX}{SHORT_ELBOW}  {occupation}")
        elif barometer[2] == True:
            strings.append(f"{SHORT_ELBOW}  {group}")
            strings.append(f"{SPACE_PREFIX}{SHORT_ELBOW}  {barometer_name}")
            strings.append(f"{SPACE_PREFIX}{SPACE_PREFIX}{SHORT_ELBOW}  {occupation}")
        else:
            strings.append(f"{SHORT_ELBOW}  {group}")
            strings.append(f"{LONG_PREFIX} {barometer_name}")
            strings.append(f"{LONG_PREFIX}{SHORT_ELBOW}  {occupation}")
    else:
        strings.append(f"{SHORT_ELBOW}  {group}")
        strings.append(f"{SPACE_PREFIX}{SHORT_ELBOW}  {occupation}")
    string = "<br />".join(strings)
    tree = f"<p style='font-size:16px;'>{string}</p>"
    return tree
    
def create_regional_link(id_group, id_region = None):
    if id_region == "i46j_HmG_v64":
        id_region = None
    link = f"https://arbetsformedlingen.se/platsbanken/annonser?p=5:{id_group}&q="
    if id_region:
        region = "&l=2:" + id_region
        return link + region
    else:
        return link

def split_town_municipality(town_municipality):
    town_municipality_split = town_municipality.split(";")
    municipality_id = town_municipality_split[1]
    municipality_name = st.session_state.municipality_id_namn.get(municipality_id)
    town_split = town_municipality_split[0]
    city_name = ' '.join(re.split("_", town_split))
    town_with_municipality = f"{city_name.capitalize()} ({municipality_name.capitalize()})"
    return town_with_municipality, f"{municipality_name} kommun"

def create_list_locations(id_location):
    list_relevant_locations = st.session_state.geodata.get(id_location)
    selected_town_with_municipality, municipality_name = split_town_municipality(id_location)

    all_locations = [{
        "town_with_municipality": selected_town_with_municipality,
        "municipality": municipality_name,
        "distance": 0,
        "relevance": "hög"}]
    
    order = {"hög": 0, "medel": 1, "låg": 2}
    sorted_relevant_locations = sorted(list_relevant_locations, key = lambda x: (order.get(x["relevans"], 3), x["avstånd"]))

    for l in sorted_relevant_locations:
        town_with_municipality, municipality_name = split_town_municipality(l["ort2_id"])

        relevant_location = {
        "town_with_municipality": town_with_municipality,
        "municipality": municipality_name,
        "distance": l["avstånd"],
        "relevance": l["relevans"]}
        all_locations.append(relevant_location)
    return all_locations

def add_hoover_to_string(skill):
    hover_info = st.session_state.competence_descriptions.get(skill)
    if not hover_info:
        hover_info = "Ingen beskrivning tillgänglig."
    skill_string = f"<p style='font-size:16px;'>{skill}</p>"
    return [skill_string, hover_info]
    
def create_skill_string(license, skills, generated):
    strings = []

    if license:
        strings.append([f"<strong>Reglerad behörigheter</strong><br />",
                        "Behörigheter som du enligt svensk lag måste ha för att kunna utöva yrket."])
        for l in license:
            strings.append(add_hoover_to_string(l))
    if skills:
        strings.append([f"<strong>Kvalitetssäkrade kompetensbegrepp</strong><br />",
                        "Kompetensbegrepp med koppling i taxonomin till aktuell yrkesbenämning."])
        for s in skills:
            strings.append(add_hoover_to_string(s))
    if generated:
        strings.append([f"<strong>Genererade kompetensbegrepp</strong><br />",
                        "Beräknade utifrån relationer mellan taxonomin och ESCO. Kvalitén på genererade begreppen varierar."])
        for g in generated:
            strings.append(add_hoover_to_string(g))

    return strings

def create_string_educational_background(educations):
    strings = []
    for s in educations:
        strings.append(s)
    string = "<br />".join(strings)
    skill_string = f"<p style='font-size:16px;'>{string}</p>"
    return skill_string

def create_educational_string(data):
    strings = []
    for s in data:
        url = s["url"]
        educational_name = s["utbildningsnamn"]
        city = s["ort"]
        link = f"<a href='{url}'>{educational_name}</a>"
        hover_info = s["beskrivning"]
        string = f"{city} - {link}"
        edu_string = f"<p style='font-size:16px;'>{string}</p>"
        strings.append([edu_string, hover_info])
    return strings

def create_string_chosen_location(data):
    location_string = f"<p style='font-size:16px;'><strong>{data['town_with_municipality']}</strong></p>"
    return location_string

def create_string_location(data):
    location_string = f"<p style='font-size:16px;'><strong>{data['town_with_municipality']}</strong><br />&emsp;&emsp;&emsp;<small>{data['distance']} kilometer - {data['relevance'].upper()} relevans</small></p>"
    if data["relevance"] == "hög":
        hover_string = "Hög relevans: Närhet till stor ort med många platsannonser förra året och stor arbetskraft/befolkning"
    elif data["relevance"] == "medel":
        hover_string = "Medel relevans: Mindre orter, eller större orter som ligger längre bort"
    else:
        hover_string = "Låg relevans: Små orter med svagare möjligheter till jobb"
    return location_string, hover_string

def create_venn_data(a_name, a_words, b_name, b_words, degree_of_overlap):
    if degree_of_overlap == 1:
        common_max = 14
        only_in_max = 8
    elif degree_of_overlap == 0.5:
        common_max = 10
        only_in_max = 10
    elif degree_of_overlap == 0:
        common_max = 6
        only_in_max = 12
    output = {}
    common = [x for x in a_words if x in b_words]
    a = common[0:common_max]
    b = common[0:common_max]
    only_in_a = [x for x in a_words if x not in b_words]
    a.extend(only_in_a[0:only_in_max])
    only_in_b = [x for x in b_words if x not in a_words]
    b.extend(only_in_b[0:only_in_max])
    output[a_name] = a
    output[b_name] = b
    return output

def create_venn(name_choosen, name_similar, adwords_similar, degree_of_overlap):
    venn_data = create_venn_data(name_choosen, st.session_state.adwords_occupation, name_similar, adwords_similar, degree_of_overlap)

    titles = []
    words = []
    for k, v in venn_data.items():
        titles.append(k)
        words.append(set(v))
    plt.figure(figsize= (12, 8))
    venn = venn2(subsets = words, set_labels = titles, set_colors = ["skyblue", "lightgreen"])
    venn.get_label_by_id("10").set_text("\n".join(words[0] - words[1]))
    venn.get_label_by_id("11").set_text("\n".join(words[0] & words[1]))
    venn.get_label_by_id("01").set_text("\n".join(words[1] - words[0]))
    return plt

@st.cache_data
def create_wordcloud(words):
    wordcloud = WordCloud(width = 800, height = 800,
                          background_color = 'white',
                          prefer_horizontal = 1).generate_from_frequencies(words)
    plt.figure(figsize = (6, 6), facecolor = None)
    plt.imshow(wordcloud)
    plt.axis('off')
    plt.tight_layout(pad = 0)
    st.pyplot(plt)

def get_ads(occupation, location):
    ads = [0, 0]
    ads_selected_occupation = st.session_state.ad_data_platsbanken.get(occupation)
    if ads_selected_occupation:
        ads_selected_location = ads_selected_occupation.get(location)
        if ads_selected_location:
            ads[0] = ads_selected_location
    ads_selected_occupation_historical = st.session_state.ad_data_historical.get(occupation)
    if ads_selected_occupation_historical:
        ads_selected_location_historical = ads_selected_occupation_historical.get(location)
        if ads_selected_location_historical:
            ads[1] = ads_selected_location_historical
    return ads

def render_job_info_html(namn, överlappningsgrad, prognos, annonser, link):
    överlapp_dict = {0: 25, 0.5: 50, 1: 75}
    fyllnadsnivå = överlapp_dict.get(överlappningsgrad, 0)
    fyllnadsgrad = fyllnadsnivå / 100 * 360

    överlappningscirkel = f'''
    <span style="display:inline-block;width: 0.9em;height: 0.9em;border-radius: 50%;
    background: conic-gradient(black 0deg {fyllnadsgrad}deg, white {fyllnadsgrad}deg 360deg);
    border: 1px solid #666; margin-left: 6px; vertical-align: middle; position: relative; top: -1px;"></span>
    '''

    överlappning_html = f'&emsp;Annonsöverlapp närliggande yrke {överlappningscirkel}<br>'

    if prognos is not None:
        pil_dict = {"öka": "\u2191", "minska": "\u2193", "vara oförändrad": "\u2192"}
        pil = pil_dict.get(prognos[1].lower(), "")
        jobbmojlighet_färg = {"små": "#ffffff", "medelstora": "#B7DB92", "stora": "#7EC03C"}
        färg = jobbmojlighet_färg.get(prognos[0].lower(), "#ffffff")
        färg_html = f'<div style="display:inline-block;width:0.9em;height:0.9em;background-color:{färg};border-radius:50%;border:1px solid black;margin-left:6px;vertical-align:middle;position:relative;top:-1px;"></div>'
        prognos_html = f'&emsp;Jobbmöjligheter{färg_html} Prognos <span>{pil}</span><br>'

    annonser_idag, annonser_2024 = annonser
    annons_er_plats = "annons" if annonser_idag == 1 else "annonser"

    first_row_html = f"""
    <div style="display: flex; align-items: center; font-size: 16px; font-family: sans-serif;">
        <span style="margin-right: 0.5em;">{namn}</span>
    </div>
    """

    first_row_bold_html = first_row_html.replace(f">{namn}", f"><strong>{namn}</strong>")
  
    annonser_html = f'&emsp;{annonser_idag} {annons_er_plats} <a href="{link}" target="_blank" style="text-decoration: none; color: #0066cc;">Platsbanken</a> (<span style="font-variant-numeric: tabular-nums;">2024: {annonser_2024}</span>)'

    lines = [överlappning_html]
    if prognos:
        lines.append(f"<div style='margin-bottom: 2px;'>{prognos_html.strip()}</div>")
    lines.append(f"<div>{annonser_html}</div>")

    second_row_html = f"""
    <div style="font-size: 13px; color: #333; margin-top: 2px; font-family: sans-serif;">
        {''.join(lines)}
    </div>
    """

    full_html = f"""
    <div style="margin-bottom: 14px;">
        {first_row_bold_html}
        {second_row_html}
    </div>
    """
    return full_html

def create_similar_occupations(ssyk_source, region_id):
    similar_1 = {}
    similar_2 = {}

    for k, v in st.session_state.similar.items():
        info_similar = st.session_state.occupationdata.get(k)
        name_similar = info_similar["preferred_label"]
        similar_description = info_similar["description"]
        similar_group_id = info_similar["occupation_group_id"]

        occupation_group = info_similar["occupation_group"]
        ssyk_similar = occupation_group[0:4]
        labour_flow_ssyk = st.session_state.labour_flow.get(ssyk_source)

        if info_similar["barometer_id"]:
            occupation_forecast = st.session_state.forecast.get(info_similar["barometer_id"])
            if occupation_forecast:
                regional_forecast = occupation_forecast.get(region_id)
            else:
                regional_forecast = None
        else:
            regional_forecast = None

        ads = get_ads(similar_group_id, region_id)

        similar_string = render_job_info_html(
            name_similar, v, regional_forecast, ads, create_regional_link(similar_group_id, region_id))

        if info_similar["esco_description"] == True:
            description_string = f"<p style='font-size:16px;'><em>Beskrivning hämtad från relaterat ESCO-yrke.</em> {similar_description}</p>"
            
        else:
            description_string = f"<p style='font-size:16px;'>{similar_description}</p>"

        if ssyk_similar in labour_flow_ssyk:
            similar_1[k] = [k, v, description_string, similar_string, name_similar]

        else:
            similar_2[k] = [k, v, description_string, similar_string, name_similar]

    sorted_similar_1 = {k:v for k,v in sorted(similar_1.items(), key = lambda item: item[0])}
    sorted_similar_2 = {k:v for k,v in sorted(similar_2.items(), key = lambda item: item[0])}
    return sorted_similar_1, sorted_similar_2

@st.fragment
def choose_related_locations(tab_name):
    info = "Tätorter hämtas från SCB. Förslag på orter baseras på en bedömning om relevans som beräknas utifrån befolkningstäthet, annonser på Platsbanken historiskt och avstånd. Avstånd är fågelvägen. Datat är i en första version."
    st.write(info)

    valid_locations = sorted(st.session_state.valid_locations)
    selected_location = st.selectbox(
        "Välj en ort",
        (valid_locations), placeholder = "", index = None)

    if selected_location:
        id_selected_location = st.session_state.locations_id.get(selected_location)

        locations = create_list_locations(id_selected_location)

        col3, col4 = st.columns(2)

        relevant_locations = locations[1:]

        antal_orter = len(relevant_locations)
        n = math.ceil(antal_orter / 2)

        locations_1 = relevant_locations[:n]
        locations_2 = relevant_locations[n:]

        with col3:
            for l in locations_1:
                string_location, hover_info = create_string_location(l)
                st.markdown(string_location, unsafe_allow_html = True, help = hover_info)

        with col4:
            for l in locations_2:
                string_location, hover_info = create_string_location(l)
                st.markdown(string_location, unsafe_allow_html = True, help = hover_info)

        text_dataunderlag_närliggande_orter = "<strong>Dataunderlag</strong><br />Relevanta pendlingsorter baseras på avstånd mellan orter från öppen geodata, befolkningstäthet och annonsantal i Historiska annonser."
        
        st.write("---")
        st.markdown(f"<p style='font-size:12px;'>{text_dataunderlag_närliggande_orter}</p>", unsafe_allow_html=True)

        feedback_questions = ["Är relevanta pendlingsorter en hjälp i diskussionen med sökande?", "Vad kan göra relevanta pendlingsorter bättre?"]
        
        create_feedback("", tab_name, feedback_questions, selected_location)

@st.dialog("Annonsöverlapp", width = "large")
def visa_venn(venn, beskrivning):
    st.pyplot(venn)
    st.markdown(beskrivning, unsafe_allow_html = True) 

def skapa_venn(name_choosen, name_similar, adwords_similar, degree_of_overlap):
    venn = create_venn(name_choosen, name_similar, adwords_similar, degree_of_overlap)
    return venn

def create_dk_link(dk_names):
    alla_dk_names = []
    to_convert = {
        "ø": "%25C3%25B8",
        "æ": "%25C3%25A6",
        "å": "%25C3%25A5",
        " ": "%2520"}
    for d in dk_names:
        for key, value in to_convert.items():
            d = re.sub(key, value, d)
        alla_dk_names.append(d)
    alla_dk_url_string = ";".join(alla_dk_names)
    alla_dk_string =  "; ".join(dk_names)
    url = f"https://job.jobnet.dk/CV/FindWork?Offset=0&SortValue=BestMatch&Region=Hovedstaden%2520og%2520Bornholm&Occupations={alla_dk_url_string}"
    return url, alla_dk_string

def post_selected_occupation(id_occupation):
    info = st.session_state.occupationdata.get(id_occupation)
    occupation_name = info["preferred_label"]
    occupation_group = info["occupation_group"]
    occupation_group_id = info["occupation_group_id"]
    occupation_field = info["occupation_field"]
    ssyk_code = occupation_group[0:4]
    aub = st.session_state.aub_data.get(ssyk_code)
    
    field_string = f"{occupation_field} (yrkesområde)"
    group_string = f"{occupation_group} (yrkesgrupp)"
    occupation_string = f"{occupation_name} (yrkesbenämning)"

    if info["barometer_id"]:
        barometer = [f"{info['barometer_name']} (yrkesbarometeryrke)", info["barometer_above_ssyk"], info["barometer_part_of_ssyk"]]
    else:
        barometer = None

    if info["similar_occupations"]:
        st.session_state.similar = info["similar_occupations"]
    else:
        st.session_state.similar = None

    description = info["description"]
    license = info["license"]
    skills = info["skill"]
    potential_skills = info["potential_skill"]

    if info["yrkessamling"]:
        yrkessamling = info["yrkessamling"]
    else:
        yrkessamling = None

    tab_names = ["Yrkesbeskrivning", "Jobbmöjligheter", "Utbildning", "Närliggande yrken", "Relevanta pendlingsorter"]

    tab1, tab2, tab3, tab4, tab5 = st.tabs(tab_names)

    for tab in tab_names:
        if f"{tab}_feedback_saved" not in st.session_state:
            st.session_state[f"{tab}_feedback_saved"] = False

    with tab1:
        if barometer:
            tree = create_tree(field_string, group_string, occupation_string, barometer, ["occupation"], yrkessamling, license)
        else:
            tree = create_tree(field_string, group_string, occupation_string, None, ["occupation"], yrkessamling, license)
        st.markdown(tree, unsafe_allow_html = True)

        st.subheader(f"Yrkesbeskrivning - {occupation_name}")

        if info["esco_description"] == True:
            description_string = f"<p style='font-size:16px;'><em>Beskrivning hämtad från relaterat ESCO-yrke.</em> {description}</p>"             
        else:
            description_string = f"<p style='font-size:16px;'>{description}</p>"
        st.markdown(description_string, unsafe_allow_html = True)

        st.subheader("Kompetensbegrepp och annonsord")

        skill_string = create_skill_string(license, skills, potential_skills[0:10 - len(skills)])

        col1, col2 = st.columns(2)

        with col1:
            for c in skill_string:
                st.markdown(c[0], unsafe_allow_html = True, help = c[1])

        with col2:
            if info["wordcloud_id"]:
                st.session_state.adwords_occupation = st.session_state.adwords.get(info["wordcloud_id"])
                if info["wordcloud_id"] == id_occupation:
                    st.markdown(f"<strong>Annonsord</strong> {occupation_name}", unsafe_allow_html = True)
                    create_wordcloud(st.session_state.adwords_occupation)
                else:
                    st.markdown(f"<strong>Annonsord</strong> {occupation_group}", unsafe_allow_html = True)
                    create_wordcloud(st.session_state.adwords_occupation)
            else:
                st.write("Inte tillräkligt med annonsunderlag för att kunna skapa ordmoln")

        st.subheader("Länkar")

        url = "https://atlas.jobtechdev.se/taxonomy/"
        atlas_uri = f"{url}{id_occupation}"

        link1, link2 = st.columns(2)
        info_text_atlas = "Jobtech Atlas"
        link1.link_button("Jobtech Atlas", atlas_uri, help = info_text_atlas, icon = ":material/link:")

        if info["hitta_yrken"]:
            hitta_yrken_uri = info["hitta_yrken"]
            info_text_hitta_yrken = "Hitta yrken"
            link2.link_button("Hitta yrken", hitta_yrken_uri, help = info_text_hitta_yrken, icon = ":material/link:")

        text_dataunderlag_yrke = "<strong>Dataunderlag</strong><br />Yrkesbeskrivningar är hämtade från taxonomin i första hand. Saknas yrkesbeskrivning hämtas en från ett relaterat ESCO-yrke (European Skills, Competences and Occupations).<br />&emsp;&emsp;&emsp;Kompetensbeskrivningar har genererats av en språkmodell med taxonomin som kontext.<br />&emsp;&emsp;&emsp;Annonsord är hämtade från Historiska berikade annonser och viktade för relevans. Annonsorden är ord som ofta berör utbildnings-, kunskaps- eller erfarenhetskrav från arbetsgivare.<br />&emsp;&emsp;&emsp;Det finns alltid en länk till Jobtech Atlas där taxonomin kan närmare studeras. Finns det en koppling i Hitta yrken till aktuell yrkesbenämning finns en sådan länk också med."

        st.write("---")
        st.markdown(f"<p style='font-size:12px;'>{text_dataunderlag_yrke}</p>", unsafe_allow_html=True)

        feedback_questions = ["Vad saknar du i svaret när du väljer ett yrke?", "Är det någon information som är överflödig?", "Om du tycker att yrkesinfo är ett bra redskap, var tycker du att den skall finnas för att vara till mest nytta?"]
        create_feedback(occupation_name, tab_names[0], feedback_questions)

    with tab2:
        if barometer:
            tree = create_tree(field_string, group_string, occupation_string, barometer, ["barometer", "group"], yrkessamling, license)
            st.markdown(tree, unsafe_allow_html = True)
        else:
            tree = create_tree(field_string, group_string, occupation_string, None, ["group"], yrkessamling, license)
            st.markdown(tree, unsafe_allow_html = True)

        if barometer:
            try:
                barometer_name = info['barometer_name']
                st.subheader(f"Jobbmöjligheter - {barometer_name}")

                a, b = st.columns(2)
                mojligheter_png_name = f"mojligheter_{info['barometer_id']}.png"
                rekryteringssituation_png_name = f"rekrytering_{info['barometer_id']}.png"
                path = "./data/"               
                a.image(f"{path}/{mojligheter_png_name}")
                b.image(f"{path}/{rekryteringssituation_png_name}")

            except:
                st.write(f"Ingen tillgänglig prognos")
        else:
            st.write(f"Ingen tillgänglig prognos")

        valid_regions = sorted(list(st.session_state.regions.keys()))
        valid_regions.append("Sverige")

        a, b = st.columns(2)

        with a:
            c, d, e = st.columns(3)

        #index_förvald_region = valid_regions.index("Skåne län")
        # if not index_förvald_region:
        #     index_förvald_region = None

        selected_region = b.selectbox(
        "Regional avgränsning", (valid_regions), index = None)

        if selected_region:
            if selected_region == "Sverige":
                selected_region_id = "i46j_HmG_v64"
            else:
                selected_region_id = st.session_state.regions.get(selected_region)
        else:
            selected_region = "Sverige"
            selected_region_id = "i46j_HmG_v64"

        st.subheader(f"Annonser - {occupation_group} - {selected_region}")

        ads = get_ads(occupation_group_id, selected_region_id)
        link = create_regional_link(occupation_group_id, selected_region_id)

        c.metric(label = "Platsbanken", value = ads[0])
        d.metric(label = "2024", value = ads[1])

        st.link_button(f"Platsbanken - {occupation_group} - {selected_region}", link, icon = ":material/link:")

        if selected_region == "Skåne län":
            dk_preflabels = st.session_state.occupation_id_dk_preflabel.get(id_occupation)
            if dk_preflabels:
                dk_link, dk_names = create_dk_link(dk_preflabels)
                st.write("")
                st.write(f"Nedan finns en länk till danska annonser. Relaterade danska yrken är: {dk_names}.")

                st.link_button(f"Jobnet.dk - Köpenhamn och Bornholm", dk_link, icon = ":material/link:")

        st.subheader(f"Lön - {occupation_group}")

        k, l, m = st.columns(3)

        salary = st.session_state.ssyk_salary.get(ssyk_code)

        salary_string1 = f"<p style='font-size:16px;'>10 % tjänar mindre än<br />Genomsnittslön<br />10% tjänar mer än</p>"
        salary_string2 = f"<p style='font-size:16px;'><strong>{salary[0]}<br />{salary[1]}<br />{salary[2]}</strong></p>"

        k.markdown(salary_string1, unsafe_allow_html = True)
        l.markdown(salary_string2, unsafe_allow_html = True)

        text_dataunderlag_jobbmöjligheter = "<strong>Dataunderlag</strong><br />Här presenteras först information från Arbetsförmedlingens Yrkesbarometer. Yrkesbarometern baseras i huvudsak på information från en enkätundersökning från Arbetsförmedlingen, Statistikmyndigheten SCB:s registerstatistik samt Arbetsförmedlingens verksamhetsstatistik. Yrkesbarometern innehåller nulägesbedömningar av möjligheter till arbete samt rekryteringssituationen inom olika yrken. Förutom en nulägesbild ges även en prognos över hur efterfrågan på arbetskraft inom respektive yrke förväntas utvecklas på fem års sikt. Yrkesbarometern uppdateras två gånger per år, varje vår och höst.<br />&emsp;&emsp;&emsp;Information kompletteras med annonser i Platsbanken nu och 2024 och löner hämtade från SCB (2023)."

        st.write("---")
        st.markdown(f"<p style='font-size:12px;'>{text_dataunderlag_jobbmöjligheter}</p>", unsafe_allow_html=True)

        feedback_questions = ["Underlättar annonsantal och länk till Platsbanken ditt arbete?", "Övrigt, skriv vad du vill"]
        create_feedback(occupation_name, tab_names[1], feedback_questions)

    with tab3:
        if barometer:
            tree = create_tree(field_string, group_string, occupation_string, barometer, ["group"], yrkessamling, license)
        else:
            tree = create_tree(field_string, group_string, occupation_string, None, ["group"], yrkessamling, license)
        st.markdown(tree, unsafe_allow_html = True)

        if info["education"]:
            educational_group = info["education"]["group_name"]
            educational_backgrounds = info["education"]["educations"]

            if educational_group:
                aub_string = f"<strong>Vanlig utbildningsbakgrund {educational_group}</strong><br />"    
                st.markdown(f"<p style='font-size:24px;'>{aub_string}</p>", unsafe_allow_html=True) 
                educational_string = create_string_educational_background(educational_backgrounds)
                st.markdown(educational_string, unsafe_allow_html = True)
        else:
            st.write("Ingen data tillgänglig")

        if aub:
            aub_string = f"<strong>Arbetsmarknadsutbildning {occupation_group}</strong><br />"    
            st.markdown(f"<p style='font-size:24px;'>{aub_string}</p>", unsafe_allow_html=True) 
            educational_string = create_educational_string(aub)
            for e in educational_string:
                st.markdown(e[0], unsafe_allow_html = True, help = e[1])

        text_dataunderlag_utbildning = "<strong>Dataunderlag</strong><br />Vanlig utbildningsbakgrund kommer från Tillväxtverkets Regionala matchningsindikatorer. Notera att grupperingen ibland sker på en högre nivå än yrkesgrupp. Information om Arbetsmarknadsutbildningar är hämtade från Skolverkets SUSA-nav."

        st.write("---")
        st.markdown(f"<p style='font-size:12px;'>{text_dataunderlag_utbildning}</p>", unsafe_allow_html=True)


        feedback_questions = ["Är utbildningsstatistiken användbar och vad skulle göra den bättre?", "Övrigt, skriv vad du vill"]
        create_feedback(occupation_name, tab_names[2], feedback_questions)

    with tab4:
        if barometer:
            if info["similar_yb_yb"] == True:
                tree = create_tree(field_string, group_string, occupation_string, barometer, ["occupation"], yrkessamling, license)
            else:
                tree = create_tree(field_string, group_string, occupation_string, barometer, ["group"], yrkessamling, license)
        else:
            if info["similar_yb_yb"] == True:
                tree = create_tree(field_string, group_string, occupation_string, None, ["occupation"], yrkessamling, license)
            else:
                tree = create_tree(field_string, group_string, occupation_string, None, ["group"], yrkessamling, license)
        st.markdown(tree, unsafe_allow_html = True)

        if st.session_state.similar:
            if info["similar_yb_yb"] == True:
                st.subheader(f"Närliggande yrken - {occupation_name}")
            else:
                st.subheader(f"Närliggande yrken - {occupation_group}")

            text_information_närliggande_yrken = f"I vänstra kolumnen återfinns yrken som både är vanliga yrkesväxlingar och där det finns annonslikheter. I den högra kolumnen visas yrken där det finns annonslikheter. Antal annonser som visas knyts till den regionala avgränsningen under Jobbmöjligheter ({selected_region})."

            st.markdown(f"<p style='font-size:12px;'>{text_information_närliggande_yrken}</p>", unsafe_allow_html=True)

            col1, col2 = st.columns(2)

            headline_1 = "<strong>Vanlig yrkesväxling och annonsöverlapp</strong>"
            headline_2 = "<strong>Annonsöverlapp</strong>"

            similar_1, similar_2 = create_similar_occupations(ssyk_code, selected_region_id)

            with col1:
                st.markdown(f"<p style='font-size:16px;'>{headline_1}</p>", unsafe_allow_html=True)
                for key, value in similar_1.items():
                    e, f = st.columns([3, 1])
                    with e:
                        e.markdown(value[3], unsafe_allow_html=True)
                    with f:
                        if st.button("", icon = ":material/join_inner:", key = key):
                            adwords_similar = st.session_state.adwords.get(value[0])
                            venn = skapa_venn(occupation_name, value[4], adwords_similar, value[1])
                            visa_venn(venn, value[2])
             
            with col2:
                st.markdown(f"<p style='font-size:16px;'>{headline_2}</p>", unsafe_allow_html=True)
                for key, value in similar_2.items():
                    e, f = st.columns([3, 1])
                    with e:
                        e.markdown(value[3], unsafe_allow_html=True)
                    with f:
                        if st.button("", icon = ":material/join_inner:", key = key):
                            adwords_similar = st.session_state.adwords.get(value[0])
                            venn = skapa_venn(occupation_name, value[4], adwords_similar, value[1])
                            visa_venn(venn, value[2])

        else:
            st.subheader(f"Inte tillräckligt med data för att kunna visa närliggande yrken")

        text_dataunderlag_närliggande_yrken = "<strong>Dataunderlag</strong><br />Närliggande yrken baseras på nyckelord i Historiska berikade annonser filtrerade med taxonomin. Träffsäkerheten i annonsunderlaget varierar och detta påverkar förstås utfallet. Andelen samma nyckelord markeras som lågt \U000025D4, medel \U000025D1 eller högt \U000025D5 överlapp. Dessa kompletteras med statistik över yrkesväxlingar från SCB, aktuell nationell eller regional prognos och annonsantal."

        st.write("---")
        st.markdown(f"<p style='font-size:12px;'>{text_dataunderlag_närliggande_yrken}</p>", unsafe_allow_html=True)

        feedback_questions = ["Är fliken närliggande yrken en hjälp i samtal med sökande?", "Övrigt, skriv vad du vill"]
        create_feedback(occupation_name, tab_names[3], feedback_questions)

    with tab5:
        st.subheader("Relevanta pendlingsorter")
        choose_related_locations(tab_names[4])

def choose_occupation_name():
    show_initial_information()
    col1, col2 = st.columns([0.7, 0.3])

    with col1:
        if st.session_state.get("no_ed_req", False):
            selected_occupation_name = st.selectbox(
                "Välj en yrkesbenämning",
                st.session_state.valid_occupations_names_no_educational_req,
                placeholder="",
                index=None)
        else:
            selected_occupation_name = st.selectbox(
                "Välj en yrkesbenämning",
                st.session_state.valid_occupation_names,
                placeholder="",
                index=None)

    with col2:
        st.markdown(
            """<div style='margin-top: 2.1em;'>""",
            unsafe_allow_html=True)
        no_ed_req = st.toggle(
            ":small[Utan utbildningskrav]",
            key="no_ed_req",
            help="Yrken utan utbildningskrav är ett urval av yrken som vanligtvis inte kräver en yrkesutbildning.")
        st.markdown("</div>", unsafe_allow_html=True)

    if selected_occupation_name:
        plt.close("all")
        id_selected_occupation = st.session_state.valid_occupations.get(selected_occupation_name)
        post_selected_occupation(id_selected_occupation)

def main ():
    initiate_session_state()
    choose_occupation_name()
    
if __name__ == '__main__':
    main ()