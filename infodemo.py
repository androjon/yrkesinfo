import streamlit as st
import json
from matplotlib import pyplot as plt
from matplotlib_venn import venn2
from wordcloud import WordCloud
import math

@st.cache_data
def import_data(filename):
    with open(filename) as file:
        content = file.read()
    output = json.loads(content)
    return output

def create_ads_occupations(id_occupation, id_selected_location, selected_location):
    other_locations = st.session_state.geodata.get(id_selected_location)

    all_locations = {}
    all_locations[id_selected_location] = 0
    for l, d in other_locations.items():
        location_name = st.session_state.id_locations.get(l)
        if location_name:
            all_locations[l] = d

    all_occupations = [id_occupation]
    for value in st.session_state.similar.values():
        all_occupations.append(value[0])

    all_ads = st.session_state_ad_data
    ads_occupations = {}
    for o in all_occupations:
        ads_o = {}
        all_ads_o = all_ads.get(o)
        for l, d in all_locations.items():
            if l == id_selected_location:
                ads_selected = all_ads_o.get(l)
                if not ads_selected:
                    ads_selected = [0, 0]
                ads_o[id_selected_location] = {
                    "ortnamn": selected_location,
                    "annonser": [ads_selected[0], ads_selected[1]],
                    "avstånd": d}
            else:
                ads_location = all_ads_o.get(l)
                if ads_location:
                    location_name = st.session_state.id_locations.get(l)
                    if location_name:
                        ads_o[l] = {
                            "ortnamn": location_name,
                            "annonser": [ads_location[0], ads_location[1]],
                            "avstånd": d}
        ads_occupations[o] = ads_o
    return all_locations, ads_occupations

def fetch_data():
    st.session_state.occupationdata = import_data("valid_occupations_with_info_v25.json")
    for key, value in st.session_state.occupationdata.items():
        st.session_state.valid_occupations[value["preferred_label"]] = key
    st.session_state.adwords = import_data("wordcloud_data_v25.json")
    st.session_state.locations_id = import_data("ortnamn_id.json")
    st.session_state.id_locations = import_data("id_ortnamn.json")
    st.session_state.valid_locations = list(st.session_state.locations_id.keys())
    st.session_state.geodata = import_data("tatorter_distance.json")
    st.session_state_ad_data = import_data("yb_ort_annonser_nu_2024.json")

def show_initial_information():
    st.logo("af-logotyp-rgb-540px.jpg")
    st.title("Yrkesinformation")
    initial_text = "Ett försöka att erbjuda information/stöd för arbetsförmedlare när det kommer till att välja <em>rätt</em> yrke och underlätta relaterade informerade bedömningar och beslut när det kommer till GYR-Y (Geografisk och yrkesmässig rörlighet - Yrke). Informationen är taxonomi-, statistik- och annonsdriven och berör 1140 yrkesbenämningar. Det är dessa yrkesbenämningar som bedöms ha tillräckligt annonsunderlag för pålitliga beräkningar."
    st.markdown(f"<p style='font-size:12px;'>{initial_text}</p>", unsafe_allow_html=True)

def initiate_session_state():
    if "valid_occupations" not in st.session_state:
        st.session_state.valid_occupations = {}
        st.session_state.adwords_occupation = {}
        st.session_state.similar = None
        st.session_state.selected_similar = []

def create_tree(field, group, occupation, barometer, bold):
    SHORT_ELBOW = "└─"
    SPACE_PREFIX = "&nbsp;&nbsp;&nbsp;&nbsp;"
    LONG_PREFIX = "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
    strings = [f"{field}"]
    if barometer:
        barometer_name = barometer[0]
        if bold == "barometer":
            barometer_name = f"<strong>{barometer_name}</strong>"
    if bold == "occupation":
        occupation = f"<strong>{occupation}</strong>"
    elif bold == "group":
        group = f"<strong>{group}</strong>"
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

def create_string(skills, start):
    if start:
        strings = [f"<strong>{start}</strong><br />"]
    else:
        strings = []
    for s in skills:
        strings.append(s)
    string = "<br />".join(strings)
    skill_string = f"<p style='font-size:16px;'>{string}</p>"
    return skill_string

def create_string_locations(data):
    strings = []
    for d in data:
        annonstext = f"{d[1]['avstånd']} kilometer - Annonser {d[1]['annonser'][0]}({d[1]['annonser'][1]})"
        strings.append(f"{d[1]['ortnamn']}<br />&emsp;&emsp;&emsp;<small>{annonstext}</small>")
    string = "<br />".join(strings)
    location_string = f"<p style='font-size:16px;'>{string}</p>"
    return location_string

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

def show_selectable_similar(data):
    with st.sidebar:
        selection = {}
        for k, v in data.items():
            name = f"{v[0]} {v[1]}({v[2]})"
            selection[name] = k
        selected = st.pills("Välj en eller flera närliggande yrken", list(selection.keys()), selection_mode = "multi")
        if selected:
            selected_ids = []
            for s in selected:
                selected_ids.append(selection.get(s))
            st.session_state.selected_similar = selected_ids

def post_selected_occupation(id_occupation):
    info = st.session_state.occupationdata.get(id_occupation)

    occupation_name = info["preferred_label"]
    occupation_group = info["occupation_group"]
    occupation_group_id = info["occupation_group_id"]
    occupation_field = info["occupation_field"]
    try:
        barometer = [f"{info['barometer_name']} (yrkesbarometeryrke)", info["barometer_above_ssyk"], info["barometer_part_of_ssyk"]]
    except:
        barometer = None
    try:
        st.session_state.similar = info["similar_occupations"]
    except:
        st.session_state.similar = None

    description = info["description"]
    license = info["license"]
    skills = info["skill"]
    potential_skills = info["potential_skill"]

    try:
        yrkessamling = info["yrkessamling"]
    except:
        yrkessamling = None

    st.session_state.adwords_occupation = st.session_state.adwords.get(id_occupation)

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Yrkesbeskrivning", "Jobbmöjligheter", "Utbildning", "Närliggande yrken", "Närliggande orter"])

    with tab1:
        field_string = f"{occupation_field} (yrkesområde)"
        group_string = f"{occupation_group} (yrkesgrupp)"

        if yrkessamling == "Kultur":
            occupation_string = f"{occupation_name} (yrkesbenämning) sorteras in under Arbetsförmedlingen Kultur och media"
        elif yrkessamling == "Sjöfart":
            occupation_string = f"{occupation_name} (yrkesbenämning) sorteras in under Arbetsförmedlingen Sjöfart"
        else:
            occupation_string = f"{occupation_name} (yrkesbenämning)"
        if barometer:
            tree = create_tree(field_string, group_string, occupation_string, barometer, "occupation")
        else:
            tree = create_tree(field_string, group_string, occupation_string, None, "occupation")
        st.markdown(tree, unsafe_allow_html = True)

        st.subheader(f"Yrkesbeskrivning {occupation_name}")

        st.write(description)

        st.subheader("Kompetensbegrepp och annonsord")

        competences = []

        if license:
            competences.extend(license)

        if skills:
            competences.extend(skills)

        if competences:
            skill_string = create_string(competences, "Kvalitetssäkrade kompetensbegrepp:")

        if potential_skills:
            potential_skills = potential_skills[0:10 - len(competences)]
            potential_skill_string = create_string(potential_skills, "Genererade kompetensbegrepp:")

        col1, col2 = st.columns(2)

        with col1:
            if competences:
                st.markdown(skill_string, unsafe_allow_html = True)
            if potential_skills:
                st.markdown(potential_skill_string, unsafe_allow_html = True)

        with col2:
            type = "yrkesbenämning"
            st.markdown(f"<strong>Annonsord {type}:</strong>", unsafe_allow_html = True)
            create_wordcloud(st.session_state.adwords_occupation)

        st.subheader("Länkar")

        atlas_uri = info["uri"]

        link1, link2 = st.columns(2)
        info_text_atlas = "Jobtech Atlas"
        link1.link_button("Jobtech Atlas", atlas_uri, help = info_text_atlas, icon = ":material/link:")

        try:
            hitta_yrken_uri = info["hitta_yrken"]
            info_text_hitta_yrken = "Hitta yrken"
            link2.link_button("Hitta yrken", hitta_yrken_uri, help = info_text_hitta_yrken, icon = ":material/link:")
        except:
            pass

        text_dataunderlag_yrke = "<strong>Dataunderlag</strong><br />Yrkesbeskrivningar är hämtade från taxonomin i första hand. Saknas yrkesbeskrivning hämtas en från ett relaterat ESCO-yrke (European Skills, Competences and Occupations).<br />&emsp;&emsp;&emsp;Kompetensbegrepp som är kopplade i taxonomin till aktuell yrkesbenämning visas upp under kvalitetssäkrade kompetensbegrepp. Det förekommer också genererade kompetensbegrepp beräknade utifrån relationer mellan taxonomin och ESCO. Kvalitén på de genererade begreppen varierar.<br />&emsp;&emsp;&emsp;Annonsord är hämtade från Historiska berikade annonser och viktade för relevans. Annonsorden är ord som ofta berör utbildnings-, kunskaps- eller erfarenhetskrav från arbetsgivare.<br />&emsp;&emsp;&emsp;Det finns alltid en länk till Jobtech Atlas där taxonomin kan närmare studeras. Finns det en koppling i Hitta yrken till aktuell yrkesbenämning finns en sådan länk också med."

        st.markdown(f"<p style='font-size:12px;'>{text_dataunderlag_yrke}</p>", unsafe_allow_html=True)

        #För kommentarer <fake@example.com>
        #För klickbara länkar <https://www.markdownguide.org>
        #Superscript E=MC<sup>2</sup>
        #<span style="font-family:Papyrus; font-size:4em;">LOVE!</span>

    with tab2:
        field_string = f"{occupation_field} (yrkesområde)"
        group_string = f"{occupation_group} (yrkesgrupp)"
        occupation_string = f"{occupation_name} (yrkesbenämning)"

        #En fil för barometeryrke - prognoser

        if barometer:
            tree = create_tree(field_string, group_string, occupation_string, barometer, "barometer")
        else:
            tree = create_tree(field_string, group_string, occupation_string, None, "occupation")

        st.markdown(tree, unsafe_allow_html = True)

        if barometer:
            st.image("prognos.png")

        else:
            st.write("Ingen tillgänglig prognos")

        text_dataunderlag_jobbmöjligheter = "<strong>Dataunderlag</strong><br />Här presenteras information från Arbetsförmedlingens Yrkesbarometer. Yrkesbarometern baseras i huvudsak på information från en enkätundersökning från Arbetsförmedlingen, Statistikmyndigheten SCB:s registerstatistik samt Arbetsförmedlingens verksamhetsstatistik. Yrkesbarometern innehåller nulägesbedömningar av möjligheter till arbete samt rekryteringssituationen inom olika yrken. Förutom en nulägesbild ges även en prognos över hur efterfrågan på arbetskraft inom respektive yrke förväntas utvecklas på fem års sikt. Yrkesbarometern uppdateras två gånger per år, varje vår och höst."
        st.markdown(f"<p style='font-size:12px;'>{text_dataunderlag_jobbmöjligheter}</p>", unsafe_allow_html=True)

    with tab3:
        if barometer:
            tree = create_tree(field_string, group_string, occupation_string, barometer, "group")
        else:
            tree = create_tree(field_string, group_string, occupation_string, None, "group")

        st.markdown(tree, unsafe_allow_html = True)

        try:
            educational_group = info["education"]["group_name"]
            educational_backgrounds = info["education"]["educations"]

            st.subheader(f"Utbildningsbakgrund {educational_group}")

            if educational_group:
                if len(educational_backgrounds) <= 2:
                    educational_string = create_string(educational_backgrounds, None)
                else:
                    educational_string = create_string(educational_backgrounds, None)

                st.markdown(educational_string, unsafe_allow_html = True)

        except:
            st.write("Ingen data tillgänglig")

        text_dataunderlag_utbildning = "<strong>Dataunderlag</strong><br />?Regionala matchningsindikatorer?"
        st.markdown(f"<p style='font-size:12px;'>{text_dataunderlag_utbildning}</p>", unsafe_allow_html=True)

        #Här borde också AUB finnas med

    with tab4:
        field_string = f"{occupation_field} (yrkesområde)"
        group_string = f"{occupation_group} (yrkesgrupp)"
        occupation_string = f"{occupation_name} (yrkesbenämning)"

        if barometer:
            tree = create_tree(field_string, group_string, occupation_string, barometer, "occupation")
        else:
            tree = create_tree(field_string, group_string, occupation_string, None, "occupation")

        st.markdown(tree, unsafe_allow_html = True)

        if st.session_state.similar:
            st.subheader(f"Närliggande yrken {occupation_name}")

            col1, col2 = st.columns(2)

            len_similar = len(st.session_state.similar)
            n = math.ceil(len_similar / 2)

            similar_1 = {}
            similar_2 = {}

            number_of_similar = 0
            for k, v in st.session_state.similar.items():
                if number_of_similar <= n:
                    similar_1[k] = v
                else:
                    similar_2[k] = v
                number_of_similar += 1

            with col1:
                for key, value in similar_1.items():
                    with st.popover(key, use_container_width = True):
                        info_similar = st.session_state.occupationdata.get(value[0])
                        name_similar = info_similar["preferred_label"]
                        adwords_similar = st.session_state.adwords.get(value[0])

                        venn = create_venn(occupation_name, name_similar, adwords_similar, value[1])
                        st.pyplot(venn)

                        description_similar = info_similar["description"]
                        st.write(description_similar)
            with col2:
                for key, value in similar_2.items():
                    with st.popover(key, use_container_width = True):
                        info_similar = st.session_state.occupationdata.get(value[0])
                        name_similar = info_similar["preferred_label"]
                        adwords_similar = st.session_state.adwords.get(value[0])

                        venn = create_venn(occupation_name, name_similar, adwords_similar, value[1])
                        st.pyplot(venn)

                        description_similar = info_similar["description"]
                        st.write(description_similar)

        else:
            st.subheader(f"Inte tillräckligt med data för att kunna visa närliggande yrken för {occupation_name}")

        text_dataunderlag_närliggande_yrken = "<strong>Dataunderlag</strong><br />Närliggande yrken baseras på nyckelord i Historiska berikade annonser filtrerade med taxonomin. Träffsäkerheten i annonsunderlaget varierar och detta påverkar förstås utfallet. Andelen samma nyckelord markeras som lågt \U000025D4, medel \U000025D1 eller högt \U000025D5 överlapp. Dessa kompletteras med statistik över yrkesväxlingar från SCB, markeras med (SCB). Om det närliggande yrket tillhör ett annat yrkesområde märks det upp med \U000021D2."
        st.markdown(f"<p style='font-size:12px;'>{text_dataunderlag_närliggande_yrken}</p>", unsafe_allow_html=True)

    with tab5:
        field_string = f"{occupation_field} (yrkesområde)"
        group_string = f"{occupation_group} (yrkesgrupp)"
        occupation_string = f"{occupation_name} (yrkesbenämning)"
        if barometer:
            tree = create_tree(field_string, group_string, occupation_string, barometer, "occupation")
        else:
            tree = create_tree(field_string, group_string, occupation_string, None, "occupation")

        st.markdown(tree, unsafe_allow_html = True)

        valid_locations = sorted(st.session_state.valid_locations)
        selected_location = st.selectbox(
            "Välj en ort",
            (valid_locations), placeholder = "", index = None)

        if selected_location:
            id_selected_location = st.session_state.locations_id.get(selected_location)

            all_locations, ads_occupations = create_ads_occupations(id_occupation, id_selected_location, selected_location)

            col1, col2 = st.columns(2)

            with col1:
                a, b = st.columns(2)

            col3, col4 = st.columns(2)

            if st.session_state.similar:
                add_similar = st.toggle("Inkludera närliggande yrken")

                if add_similar:
                    similiar_name_ads = {}
                    for value in st.session_state.similar.values():
                        id_similar = value[0]
                        info_similar = st.session_state.occupationdata.get(id_similar)
                        name_similar = info_similar["preferred_label"]

                        total_ads_similar = [name_similar, 0, 0]
                        for l in all_locations.keys():
                            try:
                                ads_similar_location = ads_occupations[id_similar][l]["annonser"]
                                total_ads_similar[1] += ads_similar_location[0]
                                total_ads_similar[2] += ads_similar_location[1]
                            except:
                                pass
                        similiar_name_ads[id_similar] = total_ads_similar

                    show_selectable_similar(similiar_name_ads)

            alla_nu = 0
            alla_historiskt = 0

            locations_with_ads_max = {}
            for l, d in all_locations.items():
                location_name = st.session_state.id_locations.get(l)
                try:
                    ads_occupation_location = ads_occupations[id_occupation][l]["annonser"]
                    locations_with_ads_max[l] = {
                                    "ortnamn": location_name,
                                    "annonser": [ads_occupation_location[0], ads_occupation_location[1]],
                                    "avstånd": d}
                    alla_nu += ads_occupation_location[0]
                    alla_historiskt += ads_occupation_location[1]
                except:
                    pass

            if st.session_state.selected_similar:
                for s in st.session_state.selected_similar:
                    for l, d in all_locations.items():
                        try:
                            ads_similar_location = ads_occupations[s][l]["annonser"]
                            locations_with_ads_max[l]["annonser"][0] += ads_similar_location[0]
                            locations_with_ads_max[l]["annonser"][1] += ads_similar_location[1]
                            alla_nu += ads_similar_location[0]
                            alla_historiskt += ads_similar_location[1]
                        except:
                            pass

            ads_grund = ads_occupations[id_occupation][id_selected_location]["annonser"]

            skillnad_nu = alla_nu - ads_grund[0]
            skillnad_historiska = alla_historiskt - ads_grund[1]

            a.metric(label = "Platsbanken", value = alla_nu, delta = skillnad_nu)
            b.metric(label = "2024", value = alla_historiskt, delta = skillnad_historiska)

            antal_orter = len(locations_with_ads_max)
            n = math.ceil(antal_orter / 2)

            list_locations_with_ads_max = list(locations_with_ads_max.items())

            locations_1 = list_locations_with_ads_max[:n]
            locations_2 = list_locations_with_ads_max[n:]

            geo_string1 = create_string_locations(locations_1)
            geo_string2 = create_string_locations(locations_2)

            with col3:
                st.markdown(geo_string1, unsafe_allow_html = True)

            with col4:
                st.markdown(geo_string2, unsafe_allow_html = True)

        text_dataunderlag_närliggande_orter = "<strong>Dataunderlag</strong><br />Närliggande orter baseras på avstånd mellan orter från öppen geodata, annonser i Platsbanken och Historiska berikade annonser knutna till dessa orter och vald yrkesbenämning."
        st.markdown(f"<p style='font-size:12px;'>{text_dataunderlag_närliggande_orter}</p>", unsafe_allow_html=True)

def choose_occupation_name():
    show_initial_information()
    valid_occupations = list(st.session_state.valid_occupations.keys())
    valid_occupations = sorted(valid_occupations)
    selected_occupation_name = st.selectbox(
        "Välj en yrkesbenämning",
        (valid_occupations), placeholder = "", index = None)
    if selected_occupation_name:
        plt.close("all")
        id_selected_occupation = st.session_state.valid_occupations.get(selected_occupation_name)
        post_selected_occupation(id_selected_occupation)

def main ():
    initiate_session_state()
    fetch_data()
    choose_occupation_name()

if __name__ == '__main__':
    main ()