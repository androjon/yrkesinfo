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
    st.session_state.occupationdata = import_data("valid_occupations_with_info.json")
    for key, value in st.session_state.occupationdata.items():
        st.session_state.valid_occupations[value["preferred_label"]] = key
    st.session_state.adwords = import_data("wordcloud_data_v25.json")

def show_initial_information():
    st.logo("af-logotyp-rgb-540px.jpg")
    st.title("Yrkesinformation")
    initial_text = "Text"
    st.markdown(f"<p style='font-size:12px;'>{initial_text}</p>", unsafe_allow_html=True)

def initiate_session_state():
    if "valid_occupations" not in st.session_state:
        st.session_state.valid_occupations = {}
        st.session_state.adwords_occupation = {}

def create_tree(field, group, occupation):
    SHORT_ELBOW = "└─"
    SPACE_PREFIX = "&nbsp;&nbsp;&nbsp;&nbsp;"
    strings = [f"{field}"]
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

def create_venn_data(a_name, a_words, b_name, b_words):
    output = {}
    common = [x for x in a_words if x in b_words]
    a = common[0:10]
    b = common[0:10]
    only_in_a = [x for x in a_words if x not in b_words]
    a.extend(only_in_a[0:10])
    only_in_b = [x for x in b_words if x not in a_words]
    b.extend(only_in_b[0:10])
    output[a_name] = a
    output[b_name] = b  
    return output

def create_venn(name_choosen, name_similar, adwords_similar):
    venn_data = create_venn_data(name_choosen, st.session_state.adwords_occupation, name_similar, adwords_similar)

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
    occupation_field = info["occupation_field"]
    

    description = info["description"]
    license = info["license"]
    skills = info["skill"]
    potential_skills = info["potential_skill"]

    st.session_state.adwords_occupation = st.session_state.adwords.get(id_occupation)

    tab1, tab2, tab3 = st.tabs(["Yrkesbeskrivning", "Jobbmöjligheter", "Närliggande yrken"])

    #En tab för Prognos + antal annonser

    with tab1:
        field_string = f"{occupation_field} (yrkesområde)"
        group_string = f"{occupation_group} (yrkesgrupp)"
        occupation_string = f"<strong>{occupation_name} (yrkesbenämning)</strong>"
        tree = create_tree(field_string, group_string, occupation_string)
        st.markdown(tree, unsafe_allow_html = True)

        st.header(f"Yrkesbeskrivning {occupation_name}")

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
            st.markdown(f"<strong>Relaterade annonsord {type}</strong>", unsafe_allow_html = True)
            create_wordcloud(st.session_state.adwords_occupation)

        educational_group = info["education"]["group_name"]
        educational_backgrounds = info["education"]["educations"]

        st.subheader(f"Utbildningsbakgrund {educational_group}")

        if educational_group:
            if len(educational_backgrounds) <= 2:
                educational_string = create_string(educational_backgrounds, None)
            else:
                educational_string = create_string(educational_backgrounds, None)
        
            st.markdown(educational_string, unsafe_allow_html = True)

        #Här borde också AUB finnas med

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
     
    with tab2:
        field_string = f"{occupation_field} (yrkesområde)"
        group_string = f"<strong>{occupation_group} (yrkesgrupp)</strong>"
        occupation_string = f"{occupation_name} (yrkesbenämning)"
        tree = create_tree(field_string, group_string, occupation_string)
        st.markdown(tree, unsafe_allow_html = True)

        st.header(f"Jobbmöjligheter {occupation_group}")

        st.image("prognos.jpg")


    with tab3:
        field_string = f"{occupation_field} (yrkesområde)"
        group_string = f"{occupation_group} (yrkesgrupp)"
        occupation_string = f"<strong>{occupation_name} (yrkesbenämning)</strong>"
        tree = create_tree(field_string, group_string, occupation_string)
        st.markdown(tree, unsafe_allow_html = True)

        st.header(f"Närliggande yrken {occupation_name}")

        similar = info["similar_occupations"]

        col1, col2 = st.columns(2)
        number_of_similar = 0

        for key, value in similar.items():
            if (number_of_similar % 2) == 0:
                with col1:
                    with st.popover(key):
                        info_similar = st.session_state.occupationdata.get(value)
                        name_similar = info_similar["preferred_label"]
                        adwords_similar = st.session_state.adwords.get(value)
                        
                        venn = create_venn(occupation_name, name_similar, adwords_similar)
                        st.pyplot(venn)

                        description_similar = info_similar["description"]
                        st.write(description_similar)
            else:
                with col2:
                    with st.popover(key):
                        info_similar = st.session_state.occupationdata.get(value)
                        name_similar = info_similar["preferred_label"]
                        adwords_similar = st.session_state.adwords.get(value)

                        venn = create_venn(occupation_name, name_similar, adwords_similar)
                        st.pyplot(venn)

                        description_similar = info_similar["description"]
                        st.write(description_similar)
            number_of_similar += 1

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