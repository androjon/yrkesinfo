import streamlit as st
import json
from matplotlib import pyplot as plt
from matplotlib_venn import venn2
from wordcloud import WordCloud

@st.cache_data
def import_data(filename):
    with open(filename) as file:
        content = file.read()
    output = json.loads(content)
    return output

def fetch_data():
    st.session_state.occupationdata = import_data("all_valid_occupations_with_info_v25.json")
    for key, value in st.session_state.occupationdata.items():
        st.session_state.valid_occupations[value["preferred_label"]] = key
    st.session_state.adwords = import_data("all_wordclouds_v25.json")
    st.session_state.aub_data = import_data("SUSA_AUB.json")
    st.session_state.regions = import_data("region_name_id.json")
    st.session_state_regional_ads = import_data("yb_region_annonser_nu_2024.json")

def show_initial_information():
    st.logo("af-logotyp-rgb-540px.jpg")
    st.title("Yrkesinformation")
    initial_text = "Ett försöka att erbjuda information/stöd för arbetsförmedlare när det kommer till att välja <em>rätt</em> yrke och underlätta relaterade informerade bedömningar och beslut när det kommer till GYR-Y (Geografisk och yrkesmässig rörlighet - Yrke). Informationen är taxonomi-, statistik- och annonsdriven. 1180 yrkesbenämningar bedöms ha tillräckligt annonsunderlag för pålitliga beräkningar. Resterande yrkesbenämningar kompletteras med beräkningar på yrkesgruppsnivå."
    st.markdown(f"<p style='font-size:12px;'>{initial_text}</p>", unsafe_allow_html=True)

def initiate_session_state():
    if "valid_occupations" not in st.session_state:
        st.session_state.valid_occupations = {}
        st.session_state.adwords_occupation = {}

def create_tree(field, group, occupation, barometer, bold, yrkessamling = None):
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
        occupation = f"{occupation} <em>hanteras av AF Kultur</em>"
    elif yrkessamling == "Sjöfart":
        occupation = f"{occupation} <em>hanteras av AF Sjöfart</em>"

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

def create_string(skills, start, url):
    if start:
        strings = [f"<strong>{start}</strong><br />"]
    else:
        strings = []
    for s in skills:
        strings.append(s)
    string = "<br />".join(strings)
    skill_string = f"<p style='font-size:16px;'>{string}</p>"
    return skill_string


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
        strings.append(f"{city} - {link}")
    string = "<br />".join(strings)
    skill_string = f"<p style='font-size:16px;'>{string}</p>"
    return skill_string

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

def post_selected_occupation(id_occupation):
    info = st.session_state.occupationdata.get(id_occupation)

    occupation_name = info["preferred_label"]
    occupation_group = info["occupation_group"]
    occupation_group_id = info["occupation_group_id"]
    occupation_field = info["occupation_field"]

    ssyk_code = occupation_group[0:4]
    aub = st.session_state.aub_data.get(ssyk_code)

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


    tab1, tab2, tab3, tab4 = st.tabs(["Yrkesbeskrivning", "Jobbmöjligheter", "Utbildning", "Närliggande yrken"])

    with tab1:
        field_string = f"{occupation_field} (yrkesområde)"
        group_string = f"{occupation_group} (yrkesgrupp)"

        occupation_string = f"{occupation_name} (yrkesbenämning)"
        if barometer:
            tree = create_tree(field_string, group_string, occupation_string, barometer, ["occupation"], yrkessamling)
        else:
            tree = create_tree(field_string, group_string, occupation_string, None, ["occupation"], yrkessamling)
        st.markdown(tree, unsafe_allow_html = True)

        st.subheader(f"Yrkesbeskrivning - {occupation_name}")

        if info["esco_description"] == True:
            description_string = f"<p style='font-size:16px;'><em>Beskrivning hämtad från relaterat ESCO-yrke.</em> {description}</p>"
             
        else:
            description_string = f"<p style='font-size:16px;'>{description}</p>"

        st.markdown(description_string, unsafe_allow_html = True)

        st.subheader("Kompetensbegrepp och annonsord")

        competences = []

        if license:
            competences.extend(license)

        if skills:
            competences.extend(skills)

        if competences:
            skill_string = create_string(competences, "Kvalitetssäkrade kompetensbegrepp", None)

        if potential_skills:
            potential_skills = potential_skills[0:10 - len(competences)]
            potential_skill_string = create_string(potential_skills, "Genererade kompetensbegrepp", None)

        col1, col2 = st.columns(2)

        with col1:
            if competences:
                st.markdown(skill_string, unsafe_allow_html = True)
            if potential_skills:
                st.markdown(potential_skill_string, unsafe_allow_html = True)

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

        atlas_uri = info["uri"]

        link1, link2 = st.columns(2)
        info_text_atlas = "Jobtech Atlas"
        link1.link_button("Jobtech Atlas", atlas_uri, help = info_text_atlas, icon = ":material/link:")

        if info["hitta_yrken"]:
            hitta_yrken_uri = info["hitta_yrken"]
            info_text_hitta_yrken = "Hitta yrken"
            link2.link_button("Hitta yrken", hitta_yrken_uri, help = info_text_hitta_yrken, icon = ":material/link:")

        text_dataunderlag_yrke = "<strong>Dataunderlag</strong><br />Yrkesbeskrivningar är hämtade från taxonomin i första hand. Saknas yrkesbeskrivning hämtas en från ett relaterat ESCO-yrke (European Skills, Competences and Occupations).<br />&emsp;&emsp;&emsp;Kompetensbegrepp som är kopplade i taxonomin till aktuell yrkesbenämning visas upp under kvalitetssäkrade kompetensbegrepp. Det förekommer också genererade kompetensbegrepp beräknade utifrån relationer mellan taxonomin och ESCO. Kvalitén på de genererade begreppen varierar.<br />&emsp;&emsp;&emsp;Annonsord är hämtade från Historiska berikade annonser och viktade för relevans. Annonsorden är ord som ofta berör utbildnings-, kunskaps- eller erfarenhetskrav från arbetsgivare.<br />&emsp;&emsp;&emsp;Det finns alltid en länk till Jobtech Atlas där taxonomin kan närmare studeras. Finns det en koppling i Hitta yrken till aktuell yrkesbenämning finns en sådan länk också med."

        st.write("---")
        st.markdown(f"<p style='font-size:12px;'>{text_dataunderlag_yrke}</p>", unsafe_allow_html=True)

    with tab2:
        field_string = f"{occupation_field} (yrkesområde)"
        group_string = f"{occupation_group} (yrkesgrupp)"
        occupation_string = f"{occupation_name} (yrkesbenämning)"

        if barometer:
            tree = create_tree(field_string, group_string, occupation_string, barometer, ["barometer", "occupation"])
            st.markdown(tree, unsafe_allow_html = True)
        else:
            tree = create_tree(field_string, group_string, occupation_string, None, ["occupation"])
            st.markdown(tree, unsafe_allow_html = True)

        if barometer:

            try:
                barometer_name = info['barometer_name']
                st.subheader(f"Jobbmöjligheter - {barometer_name}")

                a, b = st.columns(2)
                mojligheter_png_name = f"mojligheter_{info['barometer_id']}.png"
                #path_mojligheter = "/Users/jonfindahl/Desktop/Python/Yrkesinformation/mojligheter_till_arbete_png"
                rekryteringssituation_png_name = f"rekrytering_{info['barometer_id']}.png"
                #path_rekrytering = "/Users/jonfindahl/Desktop/Python/Yrkesinformation/rekryteringssituation_png"

                path = "./data/"
                
                a.image(f"{path}/{mojligheter_png_name}")
                b.image(f"{path}/{rekryteringssituation_png_name}")

            except:
                st.write("Hittar ingen karta att visa")


        else:
            st.subheader(f"Ingen tillgänglig prognos")

        st.subheader(f"Annonser - {occupation_name}")

        valid_regions = sorted(list(st.session_state.regions.keys()))

        a, b = st.columns(2)

        with b:
            c, d, e = st.columns(3)

        selected_region = a.selectbox(
        "Regional avgränsning",
        (valid_regions), placeholder = "Sverige", index = 12)

        selected_region_id = st.session_state.regions.get(selected_region)

        ads_selected_occupation = st.session_state_regional_ads.get(id_occupation)
        ads_selected_region = ads_selected_occupation.get(selected_region_id)

        d.metric(label = "Platsbanken", value = ads_selected_region[0])
        e.metric(label = "2024", value = ads_selected_region[1])
        
        text_dataunderlag_jobbmöjligheter = "<strong>Dataunderlag</strong><br />Här presenteras först information från Arbetsförmedlingens Yrkesbarometer. Yrkesbarometern baseras i huvudsak på information från en enkätundersökning från Arbetsförmedlingen, Statistikmyndigheten SCB:s registerstatistik samt Arbetsförmedlingens verksamhetsstatistik. Yrkesbarometern innehåller nulägesbedömningar av möjligheter till arbete samt rekryteringssituationen inom olika yrken. Förutom en nulägesbild ges även en prognos över hur efterfrågan på arbetskraft inom respektive yrke förväntas utvecklas på fem års sikt. Yrkesbarometern uppdateras två gånger per år, varje vår och höst.<br />&emsp;&emsp;&emsp;Information kompletteras med annonser i Platsbanken nu och 2024. Antalet annonser är inte alltid uppdaterat."

        st.write("---")
        st.markdown(f"<p style='font-size:12px;'>{text_dataunderlag_jobbmöjligheter}</p>", unsafe_allow_html=True)

    with tab3:
        if barometer:
            tree = create_tree(field_string, group_string, occupation_string, barometer, ["group"])
        else:
            tree = create_tree(field_string, group_string, occupation_string, None, ["group"])

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
            st.markdown(educational_string, unsafe_allow_html = True)

        text_dataunderlag_utbildning = "<strong>Dataunderlag</strong><br />Vanlig utbildningsbakgrund kommer från Tillväxtverkets Regionala matchningsindikatorer. Notera att grupperingen ibland sker på en högre nivå än yrkesgrupp. Information om Arbetsmarknadsutbildningar är hämtade från Skolverkets SUSA-nav. Informationen här är inte alltid uppdaterad."

        st.write("---")
        st.markdown(f"<p style='font-size:12px;'>{text_dataunderlag_utbildning}</p>", unsafe_allow_html=True)

    with tab4:
        field_string = f"{occupation_field} (yrkesområde)"
        group_string = f"{occupation_group} (yrkesgrupp)"
        occupation_string = f"{occupation_name} (yrkesbenämning)"

        if barometer:
            if info["similar_yb_yb"] == True:
                tree = create_tree(field_string, group_string, occupation_string, barometer, ["occupation"])
            else:
                tree = create_tree(field_string, group_string, occupation_string, barometer, ["group"])
        else:
            if info["similar_yb_yb"] == True:
                tree = create_tree(field_string, group_string, occupation_string, None, ["occupation"])
            else:
                tree = create_tree(field_string, group_string, occupation_string, None, ["group"])

        st.markdown(tree, unsafe_allow_html = True)

        if st.session_state.similar:

            if info["similar_yb_yb"] == True:
                st.subheader(f"Närliggande yrken - {occupation_name}")
            else:
                st.subheader(f"Närliggande yrken - {occupation_group}")

            col1, col2 = st.columns(2)

            headline_1 = "<strong>Annonsöverlapp och vanlig yrkesväxling</strong>"
            headline_2 = "<strong>Annonsöverlapp</strong>"

            similar_1 = {}
            similar_2 = {}

            for k, v in st.session_state.similar.items():
                if v[2] == True:
                    similar_1[k] = v
                else:
                    similar_2[k] = v

            with col1:
                st.markdown(f"<p style='font-size:16px;'>{headline_1}</p>", unsafe_allow_html=True)
                for key, value in similar_1.items():
                    with st.popover(key, use_container_width = True):
                        info_similar = st.session_state.occupationdata.get(value[0])
                        name_similar = info_similar["preferred_label"]
                        adwords_similar = st.session_state.adwords.get(value[0])

                        venn = create_venn(occupation_name, name_similar, adwords_similar, value[1])
                        st.pyplot(venn)

                        ads_similar = st.session_state_regional_ads.get(value[0])
                        ads_selected_region = ads_similar.get(selected_region_id)

                        if not ads_selected_region:
                            ads_selected_region = [0, 0]

                        ads_string = f"<p style='font-size:16px;'><em>Annonser {selected_region}</em> {ads_selected_region[0]}/{ads_selected_region[1]} (Platsbanken/2024)</p>"

                        similar_description = info_similar["description"]

                        if info_similar["esco_description"] == True:
                            description_string = f"<p style='font-size:16px;'><em>Beskrivning hämtad från relaterat ESCO-yrke.</em> {similar_description}</p>"
                            
                        else:
                            description_string = f"<p style='font-size:16px;'>{similar_description}</p>"

                        st.markdown(description_string, unsafe_allow_html = True)
                        st.markdown(ads_string, unsafe_allow_html = True)

            with col2:
                st.markdown(f"<p style='font-size:16px;'>{headline_2}</p>", unsafe_allow_html=True)
                for key, value in similar_2.items():
                    with st.popover(key, use_container_width = True):
                        info_similar = st.session_state.occupationdata.get(value[0])
                        name_similar = info_similar["preferred_label"]
                        adwords_similar = st.session_state.adwords.get(value[0])

                        venn = create_venn(occupation_name, name_similar, adwords_similar, value[1])
                        st.pyplot(venn)

                        ads_similar = st.session_state_regional_ads.get(value[0])
                        ads_selected_region = ads_similar.get(selected_region_id)

                        if not ads_selected_region:
                            ads_selected_region = [0, 0]

                        ads_string = f"<p style='font-size:16px;'><em>Annonser {selected_region}</em> {ads_selected_region[0]}/{ads_selected_region[1]} (Platsbanken/2024)</p>"

                        similar_description = info_similar["description"]

                        if info_similar["esco_description"] == True:
                            description_string = f"<p style='font-size:16px;'><em>Beskrivning hämtad från relaterat ESCO-yrke.</em> {similar_description}</p>"
                            
                        else:
                            description_string = f"<p style='font-size:16px;'>{similar_description}</p>"

                        st.markdown(description_string, unsafe_allow_html = True)
                        st.markdown(ads_string, unsafe_allow_html = True)

        else:
            st.subheader(f"Inte tillräckligt med data för att kunna visa närliggande yrken")

        text_dataunderlag_närliggande_yrken = "<strong>Dataunderlag</strong><br />Närliggande yrken baseras på nyckelord i Historiska berikade annonser filtrerade med taxonomin. Träffsäkerheten i annonsunderlaget varierar och detta påverkar förstås utfallet. Andelen samma nyckelord markeras som lågt \U000025D4, medel \U000025D1 eller högt \U000025D5 överlapp. Dessa kompletteras med statistik över yrkesväxlingar från SCB, markeras med (SCB). Om det närliggande yrket tillhör ett annat yrkesområde märks det upp med \U000021D2."

        st.write("---")
        st.markdown(f"<p style='font-size:12px;'>{text_dataunderlag_närliggande_yrken}</p>", unsafe_allow_html=True)

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
