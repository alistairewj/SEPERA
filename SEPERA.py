"""
Title: Development, multi-institutional validation, and algorithmic audit of SEPERA - An artificial intelligence-based
 Side-specific Extra-Prostatic Extension Risk Assessment tool for patients undergoing radical prostatectomy.
"""

# Import packages and libraries
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import PIL.Image
import streamlit as st
import shap
import joblib
from pathlib import Path
from google_drive_downloader import GoogleDriveDownloader as gdd
from PIL import ImageFont, ImageDraw, ImageOps
import SessionState


def main():
    st.title("SEPERA (Side-specific Extra-Prostatic Extension Risk Assessment)")
    st.sidebar.image("Images/Logo.png", use_column_width=True)
    st.sidebar.header("Navigation")
    session_state = SessionState.get(button_id="", color_to_label={})
    PAGES = {
        "SEPERA": full_app,
        "About": about
    }
    page = st.sidebar.selectbox("", options=list(PAGES.keys()))
    PAGES[page](session_state)


# ssEPE Tool Page
def full_app(session_state):
    # Header text
    st.subheader("Instructions")
    st.markdown(
        """
    1. Enter patient values on the left
    1. Press submit button
    1. SEPERA will output the following:
        * Annotated prostate map showing location and severity of disease
        * Probability of side-specific extraprostatic extension for the left and right prostatic lobe
        * Percentage of patients in our multi-institutional cohort with similar characteristics that had side-specific 
        extraprostatic extension
    """
    )

    # Create 2 columns, one to show SHAP plots, one to show annotated prostate diagram
    col1, col2 = st.columns([1, 1.75])

    col1.subheader('Annotated Prostate')
    col1.write('Automatically updates based on patient characteristics.')
    col2.subheader('SEPERA explanations')
    col2.write('The probability of side-specific extraprostatic extension for each lobe is indicated in **bold**. \
    Each plot highlights which features have the greatest impact on the predicted probability.')

    st.subheader('See how you compare with the study population')
    st.write('From our study cohort, X patients had the similar characteristics as you. Of these patients, \
              Y patients had ssEPE')

    # Specify font size for annotated prostate diagram
    font = ImageFont.truetype('Font.ttf', 50)

    # Load saved items from Google Drive
    Model_location = st.secrets['SEPERA']
    Feature_location = st.secrets['Feature']

    @st.cache(allow_output_mutation=True)
    def load_items():
        save_dest = Path('model')
        save_dest.mkdir(exist_ok=True)
        model_checkpoint = Path('model/SEPERA.pkl')
        feature_checkpoint = Path('model/Features.pkl')
        explainer_checkpoint = Path('model/explainer.pkl')
        shap_checkpoint = Path('model/model shap.pkl')

        # download from Google Drive if model or features are not present
        if not model_checkpoint.exists():
            with st.spinner("Downloading model... this may take awhile! \n Don't stop it!"):
                gdd.download_file_from_google_drive(Model_location, model_checkpoint)
        if not feature_checkpoint.exists():
            with st.spinner("Downloading model... this may take awhile! \n Don't stop it!"):
                gdd.download_file_from_google_drive(Feature_location, feature_checkpoint)

        model = joblib.load(model_checkpoint)
        features = joblib.load(feature_checkpoint)
        if not explainer_checkpoint.exists():
            explainer = shap.TreeExplainer(model, np.array(features), model_output='probability')
            joblib.dump(explainer, explainer_checkpoint)
        explainer2 = joblib.load(explainer_checkpoint)
        if not shap_checkpoint.exists():
            model_shap = explainer2(features)
            joblib.dump(model_shap, shap_checkpoint)
        model_shap2 = joblib.load(shap_checkpoint)
        return model, features, explainer2, model_shap2

    model, features, explainer, model_shap = load_items()

    # Load blank prostate as image objects from GitHub repository
    def load_images():
        image2 = PIL.Image.open('Images/Prostate diagram.png')
        return image2

    image2 = load_images()

    # Define choices and labels for feature inputs
    CHOICES = {0: 'No', 1: 'Yes'}

    def format_func_yn(option):
        return CHOICES[option]

    G_CHOICES = {0: 'Benign',
                 1: 'ISUP Grade 1 (Gleason 3+3)',
                 2: 'ISUP Grade 2 (Gleason 3+4)',
                 3: 'ISUP Grade 3 (Gleason 4+3)',
                 4: 'ISUP Grade 4 (Gleason 4+4/5+3/3+5)',
                 5: 'ISUP Grade 5 (Gleason 4+5/5+4/5+5)'}

    def format_func_gleason(option):
        return G_CHOICES[option]

    features_list = ('Age at Biopsy',
                     'Worst Gleason Grade Group',
                     'PSA density',
                     'Perineural invasion',
                     '% positive cores',
                     '% Gleason pattern 4/5',
                     'Max % core involvement',
                     'Base finding',
                     'Base % core involvement',
                     'Mid % core involvement',
                     'Apex % core involvement')

    # Input individual values in sidebar
    st.sidebar.header("Enter patient information")
    with st.sidebar:
        with st.form(key="my_form"):
            st.subheader("General information")
            age = st.number_input("Age (years)", 0, 100, 60)
            psa = st.number_input("PSA (ng/ml)", 0.00, 200.00, 7.00)
            vol = st.number_input("Prostate volume (ml)", 0.0, 300.0, 40.0)
            p_high = st.number_input("% Gleason pattern 4/5", 0.0, 100.00, 22.5)
            perineural_inv = st.selectbox("Perineural invasion", options=list(CHOICES.keys()),
                                          format_func=format_func_yn, index=1)

            st.subheader("Left-sided biopsy information")
            base_findings = st.selectbox('Left base findings', options=list(G_CHOICES.keys()),
                                         format_func=format_func_gleason, index=3)
            base_p_inv = st.number_input('Left base % core involvement (0 to 100)', 0.0, 100.0, value=7.5)
            mid_findings = st.selectbox('Left mid findings', options=list(G_CHOICES.keys()),
                                        format_func=format_func_gleason,
                                        index=3)
            mid_p_inv = st.number_input('Left mid % core involvement (0 to 100)', 0.0, 100.0, value=5.0)
            apex_findings = st.selectbox('Left apex findings', options=list(G_CHOICES.keys()),
                                         format_func=format_func_gleason, index=0)
            apex_p_inv = st.number_input('Left apex % core involvement (0 to 100)', 0.0, 100.0, value=0.0)
            pos_core = st.number_input('Left # of positive cores', 0, 30, 3)
            taken_core = st.number_input('Left # of cores taken', 0, 30, 6)

            st.subheader("Right-sided biopsy information")
            base_findings_r = st.selectbox('Right base findings', options=list(G_CHOICES.keys()),
                                           format_func=format_func_gleason, index=5)
            base_p_inv_r = st.number_input('Right base % core involvement (0 to 100)', 0.0, 100.0, value=45.0)
            mid_findings_r = st.selectbox('Right mid findings', options=list(G_CHOICES.keys()),
                                          format_func=format_func_gleason, index=4)
            mid_p_inv_r = st.number_input('Right mid % core involvement (0 to 100)', 0.0, 100.0, value=45.0)
            apex_findings_r = st.selectbox('Right apex findings', options=list(G_CHOICES.keys()),
                                           format_func=format_func_gleason, index=3)
            apex_p_inv_r = st.number_input('Right apex % core involvement (0 to 100)', 0.0, 100.0, value=20.0)
            pos_core_r = st.number_input('Left # of positive cores', 0, 30, 5)
            taken_core_r = st.number_input('Left # of cores taken', 0, 30, 8)

            submitted = st.form_submit_button(label='Submit')

            if submitted:
                ### LEFT DATA STORAGE ###
                # Group site findings into a list
                gleason_t = [base_findings, mid_findings, apex_findings]

                # Group % core involvements at each site into a list
                p_inv_t = [base_p_inv, mid_p_inv, apex_p_inv]

                # Combine site findings and % core involvements into a pandas DataFrame and sort by descending Gleason
                # then descending % core involvement
                g_p_inv = pd.DataFrame({'Gleason': gleason_t, '% core involvement': p_inv_t})
                sort_g_p_inv = g_p_inv.sort_values(by=['Gleason', '% core involvement'], ascending=False)

                # Store a dictionary into a variable
                pt_data = {'Age at Biopsy': age,
                           'Worst Gleason Grade Group': sort_g_p_inv['Gleason'].max(),
                           'PSA density': psa/vol,
                           'Perineural invasion': perineural_inv,
                           '% positive cores': (pos_core/taken_core)*100,
                           '% Gleason pattern 4/5': p_high,
                           'Max % core involvement': sort_g_p_inv['% core involvement'].max(),
                           'Base finding': base_findings,
                           'Base % core involvement': base_p_inv,
                           'Mid % core involvement': mid_p_inv,
                           'Apex % core involvement': apex_p_inv
                           }

                pt_features = pd.DataFrame(pt_data, index=[0])

                ### RIGHT DATA STORAGE ###
                # Group site findings into a list
                gleason_t_r = [base_findings_r, mid_findings_r, apex_findings_r]

                # Group % core involvements at each site into a list
                p_inv_t_r = [base_p_inv_r, mid_p_inv_r, apex_p_inv_r]

                # Combine site findings and % core involvements into a pandas DataFrame and sort by descending Gleason
                # then descending % core involvement
                g_p_inv_r = pd.DataFrame({'Gleason': gleason_t_r, '% core involvement': p_inv_t_r})
                sort_g_p_inv_r = g_p_inv_r.sort_values(by=['Gleason', '% core involvement'], ascending=False)

                # Store a dictionary into a variable
                pt_data_r = {'Age at Biopsy': age,
                             'Worst Gleason Grade Group': sort_g_p_inv['Gleason'].max(),
                             'PSA density': psa/vol,
                             'Perineural invasion': perineural_inv,
                             '% positive cores': (pos_core_r/taken_core_r)*100,
                             '% Gleason pattern 4/5': p_high,
                             'Max % core involvement': sort_g_p_inv_r['% core involvement'].max(),
                             'Base finding': base_findings_r,
                             'Base % core involvement': base_p_inv_r,
                             'Mid % core involvement': mid_p_inv_r,
                             'Apex % core involvement': apex_p_inv_r
                             }

                pt_features_r = pd.DataFrame(pt_data_r, index=[0])

                ### ANNOTATED PROSTATE DIAGRAM ###
                # Create text to overlay on annotated prostate diagram, auto-updates based on user inputted values
                base_L = str(G_CHOICES[base_findings]) + '\n' \
                         + '% core inv: ' + str(base_p_inv)
                mid_L = str(G_CHOICES[mid_findings]) + '\n' \
                        + '% core inv: ' + str(mid_p_inv)
                apex_L = str(G_CHOICES[apex_findings]) + '\n' \
                         + '% core inv: ' + str(apex_p_inv)
                base_R = str(G_CHOICES[base_findings_r]) + '\n' \
                         + '% core inv: ' + str(base_p_inv_r)
                mid_R = str(G_CHOICES[mid_findings_r]) + '\n' \
                        + '% core inv: ' + str(mid_p_inv_r)
                apex_R = str(G_CHOICES[apex_findings_r]) + '\n' \
                         + '% core inv: ' + str(apex_p_inv_r)

                # Set conditions to show colour coded site images based on Gleason Grade Group for each site
                draw = ImageDraw.Draw(image2)
                if base_findings == 1:
                    image_bl_G1 = PIL.ImageOps.flip(PIL.Image.open('Images/Corner 1.png'))
                    image2.paste(image_bl_G1, (145, 958), mask=image_bl_G1)
                if base_findings == 2:
                    image_bl_G2 = PIL.ImageOps.flip(PIL.Image.open('Images/Corner 2.png'))
                    image2.paste(image_bl_G2, (145, 958), mask=image_bl_G2)
                if base_findings == 3:
                    image_bl_G3 = PIL.ImageOps.flip(PIL.Image.open('Images/Corner 3.png'))
                    image2.paste(image_bl_G3, (145, 958), mask=image_bl_G3)
                if base_findings == 4:
                    image_bl_G4 = PIL.ImageOps.flip(PIL.Image.open('Images/Corner 4.png'))
                    image2.paste(image_bl_G4, (145, 958), mask=image_bl_G4)
                if base_findings == 5:
                    image_bl_G5 = PIL.ImageOps.flip(PIL.Image.open('Images/Corner 5.png'))
                    image2.paste(image_bl_G5, (145, 958), mask=image_bl_G5)

                if mid_findings == 1:
                    image_ml_G1 = PIL.Image.open('Images/Mid 1.png')
                    image2.paste(image_ml_G1, (145, 606), mask=image_ml_G1)
                if mid_findings == 2:
                    image_ml_G2 = PIL.Image.open('Images/Mid 2.png')
                    image2.paste(image_ml_G2, (145, 606), mask=image_ml_G2)
                if mid_findings == 3:
                    image_ml_G3 = PIL.Image.open('Images/Mid 3.png')
                    image2.paste(image_ml_G3, (145, 606), mask=image_ml_G3)
                if mid_findings == 4:
                    image_ml_G4 = PIL.Image.open('Images/Mid 4.png')
                    image2.paste(image_ml_G4, (145, 606), mask=image_ml_G4)
                if mid_findings == 5:
                    image_ml_G5 = PIL.Image.open('Images/Mid 5.png')
                    image2.paste(image_ml_G5, (145, 606), mask=image_ml_G5)

                if apex_findings == 1:
                    image_al_G1 = PIL.Image.open('Images/Corner 1.png')
                    image2.paste(image_al_G1, (145, 130), mask=image_al_G1)
                if apex_findings == 2:
                    image_al_G2 = PIL.Image.open('Images/Corner 2.png')
                    image2.paste(image_al_G2, (145, 130), mask=image_al_G2)
                if apex_findings == 3:
                    image_al_G3 = PIL.Image.open('Images/Corner 3.png')
                    image2.paste(image_al_G3, (145, 130), mask=image_al_G3)
                if apex_findings == 4:
                    image_al_G4 = PIL.Image.open('Images/Corner 4.png')
                    image2.paste(image_al_G4, (145, 130), mask=image_al_G4)
                if apex_findings == 5:
                    image_al_G5 = PIL.Image.open('Images/Corner 5.png')
                    image2.paste(image_al_G5, (145, 130), mask=image_al_G5)

                if base_findings_r == 1:
                    image_br_G1 = PIL.ImageOps.flip(PIL.ImageOps.mirror(PIL.Image.open('Images/Corner 1.png')))
                    image2.paste(image_br_G1, (1104, 958), mask=image_br_G1)
                if base_findings_r == 2:
                    image_br_G2 = PIL.ImageOps.flip(PIL.ImageOps.mirror(PIL.Image.open('Images/Corner 2.png')))
                    image2.paste(image_br_G2, (1104, 958), mask=image_br_G2)
                if base_findings_r == 3:
                    image_br_G3 = PIL.ImageOps.flip(PIL.ImageOps.mirror(PIL.Image.open('Images/Corner 3.png')))
                    image2.paste(image_br_G3, (1104, 958), mask=image_br_G3)
                if base_findings_r == 4:
                    image_br_G4 = PIL.ImageOps.flip(PIL.ImageOps.mirror(PIL.Image.open('Images/Corner 4.png')))
                    image2.paste(image_br_G4, (1104, 958), mask=image_br_G4)
                if base_findings_r == 5:
                    image_br_G5 = PIL.ImageOps.flip(PIL.ImageOps.mirror(PIL.Image.open('Images/Corner 5.png')))
                    image2.paste(image_br_G5, (1104, 958), mask=image_br_G5)

                if mid_findings_r == 1:
                    image_mr_G1 = PIL.Image.open('Images/Mid 1.png')
                    image2.paste(image_mr_G1, (1542, 606), mask=image_mr_G1)
                if mid_findings_r == 2:
                    image_mr_G2 = PIL.Image.open('Images/Mid 2.png')
                    image2.paste(image_mr_G2, (1542, 606), mask=image_mr_G2)
                if mid_findings_r == 3:
                    image_mr_G3 = PIL.Image.open('Images/Mid 3.png')
                    image2.paste(image_mr_G3, (1542, 606), mask=image_mr_G3)
                if mid_findings_r == 4:
                    image_mr_G4 = PIL.Image.open('Images/Mid 4.png')
                    image2.paste(image_mr_G4, (1542, 606), mask=image_mr_G4)
                if mid_findings_r == 5:
                    image_mr_G5 = PIL.Image.open('Images/Mid 5.png')
                    image2.paste(image_mr_G5, (1542, 606), mask=image_mr_G5)

                if apex_findings_r == 1:
                    image_ar_G1 = PIL.ImageOps.mirror(PIL.Image.open('Images/Corner 1.png'))
                    image2.paste(image_ar_G1, (1104, 130), mask=image_ar_G1)
                if apex_findings_r == 2:
                    image_ar_G2 = PIL.ImageOps.mirror(PIL.Image.open('Images/Corner 2.png'))
                    image2.paste(image_ar_G2, (1104, 130), mask=image_ar_G2)
                if apex_findings_r == 3:
                    image_ar_G3 = PIL.ImageOps.mirror(PIL.Image.open('Images/Corner 3.png'))
                    image2.paste(image_ar_G3, (1104, 130), mask=image_ar_G3)
                if apex_findings_r == 4:
                    image_ar_G4 = PIL.ImageOps.mirror(PIL.Image.open('Images/Corner 4.png'))
                    image2.paste(image_ar_G4, (1104, 130), mask=image_ar_G4)
                if apex_findings_r == 5:
                    image_ar_G5 = PIL.ImageOps.mirror(PIL.Image.open('Images/Corner 5.png'))
                    image2.paste(image_ar_G5, (1104, 130), mask=image_ar_G5)

                # Overlay text showing Gleason Grade Group, % positive cores, and % core involvement for each site
                draw.text((525, 1110), base_L, fill="black", font=font, align="center")
                draw.text((205, 690), mid_L, fill="black", font=font, align="center")
                draw.text((525, 275), apex_L, fill="black", font=font, align="center")
                draw.text((1300, 1110), base_R, fill="black", font=font, align="center")
                draw.text((1590, 690), mid_R, fill="black", font=font, align="center")
                draw.text((1300, 275), apex_R, fill="black", font=font, align="center")
                col1.image(image2, use_column_width='auto')
                col1.write('**Red bars**: Features that ***increase*** the risk of ssEPE  \n'
                           '**Blue bars**: Features that ***decrease*** the risk of ssEPE  \n'
                           '**Width of bars**: Importance of the feature. The wider it is, the greater impact it has '
                           'on risk of ssEPE')

                ### SHAP FORCE PLOTS ###
                # SHAP plot for left lobe
                col2.subheader('Left lobe')
                st.set_option('deprecation.showPyplotGlobalUse', False)

                shap_values = explainer.shap_values(pt_features)
                shap.force_plot(0.3, shap_values, pt_features, features_list, text_rotation=10,  # features_list,
                                matplotlib=True)
                col2.pyplot(bbox_inches='tight', dpi=600, pad_inches=0, use_column_width='auto')
                plt.clf()

                # SHAP plot for right lobe
                col2.subheader('Right lobe')
                shap_values_r = explainer.shap_values(pt_features_r)
                shap.plots.force(0.3, shap_values_r, pt_features_r, features_list, matplotlib=True,
                                 text_rotation=10)
                col2.pyplot(bbox_inches='tight', dpi=600, pad_inches=0, use_column_width='auto')
                plt.clf()

                """
                ### COMPARISON TO STUDY POPULATION ###
                colglobal.write('**Global Variables**')

                # PSA
                shap.plots.scatter(model_shap[:, 0], hist=True, dot_size=5, show=False)
                plt.ylabel('Impact on probability of ssEPE')
                x_pt_psa = np.array(pt_features)[:, 0]
                y_pt_psa = shap_values[:, 0]
                plt.plot(x_pt_psa, y_pt_psa, 'ro', markersize=7, alpha=1)
                colpsa.pyplot(bbox_inches='tight', dpi=600, pad_inches=0, use_column_width='auto')

                # Maximum % core involvement
                shap.plots.scatter(model_shap[:, 1], hist=True, dot_size=5, show=False)
                plt.ylabel('Impact on probability of ssEPE')
                x_pt_maxci = np.array(pt_features)[:, 1]
                y_pt_maxci = shap_values[:, 1]
                plt.plot(x_pt_maxci, y_pt_maxci, 'ro', markersize=7, alpha=1)
                colmaxci.pyplot(bbox_inches='tight', dpi=600, pad_inches=0, use_column_width='auto')

                # % Gleason 4/5
                shap.plots.scatter(model_shap[:, 2], hist=True, dot_size=5, show=False)
                plt.ylabel('Impact on probability of ssEPE')
                x_pt_phigh = np.array(pt_features)[:, 2]
                y_pt_phigh = shap_values[:, 2]
                plt.plot(x_pt_phigh, y_pt_phigh, 'ro', markersize=7, alpha=1)
                colphigh.pyplot(bbox_inches='tight', dpi=600, pad_inches=0, use_column_width='auto')

                # Perineural invasion
                shap.plots.scatter(model_shap[:, 3], hist=True, dot_size=5, show=False)
                positions = (0, 1)
                x_labels = ('No', 'Yes')
                plt.xticks(positions, x_labels, rotation=0)
                plt.ylabel('Impact on probability of ssEPE')
                x_pt_pinv = np.array(pt_features)[:, 3]
                y_pt_pinv = shap_values[:, 3]
                plt.plot(x_pt_pinv, y_pt_pinv, 'ro', markersize=7, alpha=1)
                colpinv.pyplot(bbox_inches='tight', dpi=600, pad_inches=0, use_column_width='auto')

                # Age
                shap.plots.scatter(model_shap[:, 8], hist=True, dot_size=5, show=False)
                plt.ylabel('Impact on probability of ssEPE')
                x_pt_age = np.array(pt_features)[:, 8]
                y_pt_age = shap_values[:, 8]
                plt.plot(x_pt_age, y_pt_age, 'ro', markersize=7, alpha=1)
                colage.pyplot(bbox_inches='tight', dpi=600, pad_inches=0, use_column_width='auto')

                colside.write('**Side-specific Variables**')
                colside.write('**Red** data-points represents **left** side-specific values, while **green** '
                              'data-points represents **right** side-specific values.')

                # Base # core involvement
                shap.plots.scatter(model_shap[:, 4], hist=True, dot_size=5, show=False)
                plt.ylabel('Impact on probability of ssEPE')
                x_pt_bci = np.array(pt_features)[:, 4]
                y_pt_bci = shap_values[:, 4]
                x_pt_bcir = np.array(pt_features_r)[:, 4]
                y_pt_bcir = shap_values_r[:, 4]
                plt.plot(x_pt_bci, y_pt_bci, 'ro', markersize=7, alpha=1, color='red')
                plt.plot(x_pt_bcir, y_pt_bcir, 'ro', markersize=7, alpha=1, color='green')
                colbci.pyplot(bbox_inches='tight', dpi=600, pad_inches=0, use_column_width='auto')

                # Mid % core involvement
                shap.plots.scatter(model_shap[:, 10], hist=True, dot_size=5, show=False)
                plt.ylabel('Impact on probability of ssEPE')
                x_pt_mci = np.array(pt_features)[:, 10]
                y_pt_mci = shap_values[:, 10]
                x_pt_mcir = np.array(pt_features_r)[:, 10]
                y_pt_mcir = shap_values_r[:, 10]
                plt.plot(x_pt_mci, y_pt_mci, 'ro', markersize=7, alpha=1, color='red')
                plt.plot(x_pt_mcir, y_pt_mcir, 'ro', markersize=7, alpha=1, color='green')
                colmci.pyplot(bbox_inches='tight', dpi=600, pad_inches=0, use_column_width='auto')

                # TZ % core involvement
                shap.plots.scatter(model_shap[:, 7], hist=True, dot_size=5, show=False)
                plt.ylabel('Impact on probability of ssEPE')
                x_pt_tzci = np.array(pt_features)[:, 7]
                y_pt_tzci = shap_values[:, 7]
                x_pt_tzcir = np.array(pt_features_r)[:, 7]
                y_pt_tzcir = shap_values_r[:, 7]
                plt.plot(x_pt_tzci, y_pt_tzci, 'ro', markersize=7, alpha=1, color='red')
                plt.plot(x_pt_tzcir, y_pt_tzcir, 'ro', markersize=7, alpha=1, color='green')
                coltzci.pyplot(bbox_inches='tight', dpi=600, pad_inches=0, use_column_width='auto')

                # Base findings
                shap.plots.scatter(model_shap[:, 5], hist=True, dot_size=5, show=False)
                positions = (0, 1, 2, 3, 4, 5, 6, 7)
                x_labels = ('Normal', 'HGPIN', 'ASAP', 'GGG1', 'GGG2', 'GGG3', 'GGG4', 'GGG5')
                plt.xticks(positions, x_labels, rotation=0)
                plt.ylabel('Impact on probability of ssEPE')
                x_pt_bf = np.array(pt_features)[:, 5]
                y_pt_bf = shap_values[:, 5]
                x_pt_bfr = np.array(pt_features_r)[:, 5]
                y_pt_bfr = shap_values_r[:, 5]
                plt.plot(x_pt_bf, y_pt_bf, 'ro', markersize=7, alpha=1, color='red')
                plt.plot(x_pt_bfr, y_pt_bfr, 'ro', markersize=7, alpha=1, color='green')
                colbf.pyplot(bbox_inches='tight', dpi=600, pad_inches=0, use_column_width='auto')

                # Worst Gleason Grade Group
                shap.plots.scatter(model_shap[:, 9], hist=True, dot_size=5, show=False)
                positions = (0, 1, 2, 3, 4, 5, 6, 7)
                x_labels = ('Normal', 'HGPIN', 'ASAP', 'GGG1', 'GGG2', 'GGG3', 'GGG4', 'GGG5')
                plt.xticks(positions, x_labels, rotation=0)
                plt.ylabel('Impact on probability of ssEPE')
                x_pt_wggg = np.array(pt_features)[:, 9]
                y_pt_wggg = shap_values[:, 9]
                x_pt_wgggr = np.array(pt_features_r)[:, 9]
                y_pt_wgggr = shap_values_r[:, 9]
                plt.plot(x_pt_wggg, y_pt_wggg, 'ro', markersize=7, alpha=1, color='red')
                plt.plot(x_pt_wgggr, y_pt_wgggr, 'ro', markersize=7, alpha=1, color='green')
                colwggg.pyplot(bbox_inches='tight', dpi=600, pad_inches=0, use_column_width='auto')

                # % positive cores
                shap.plots.scatter(model_shap[:, 6], hist=True, dot_size=5, show=False)
                plt.ylabel('Impact on probability of ssEPE')
                x_pt_pc = np.array(pt_features)[:, 6]
                y_pt_pc = shap_values[:, 6]
                x_pt_pcr = np.array(pt_features_r)[:, 6]
                y_pt_pcr = shap_values_r[:, 6]
                plt.plot(x_pt_pc, y_pt_pc, 'ro', markersize=7, alpha=1, color='red')
                plt.plot(x_pt_pcr, y_pt_pcr, 'ro', markersize=7, alpha=1, color='green')
                colpc.pyplot(bbox_inches='tight', dpi=600, pad_inches=0, use_column_width='auto')
                """

def about(session_state):
    st.markdown(
        """
    Welcome to the Side-Specific Extra-Prostatic Extension Risk Assessment (SEPERA) tool. SEPERA provides several 
    outputs that may be beneficial for surgical planning and patient counselling for patients with localized prostate
    cancer:
    * Annotated prostate diagram showing location and severity of disease based on prostate biopsy
    * Probability of side-specific extraprostatic extension for the left and right prostatic lobe
    * Comparison of individual patient characteristics to the study population used to create SEPERA
    """
    )
    st.subheader("Reference")
    st.markdown(
        """
    **Development, multi-institutional validation, and algorithmic audit of SEPERA - An artificial intelligence-based 
    Side-specific Extra-Prostatic Extension Risk Assessment tool for patients undergoing radical prostatectomy.**\n

    *Jethro CC. Kwong$^{1,2}$, Adree Khondker$^{3}$, Eric Meng$^{4}$, Nicholas Taylor$^{3}$, Nathan Perlis$^{1}$, 
    Girish S. Kulkarni$^{1,2}$, Robert J. Hamilton$^{1}$, Neil E. Fleshner$^{1}$, Antonio Finelli$^{1}$, 
    Valentin Colinet$^{5}$, Alexandre Peltier$^{5}$, Romain Diamand$^{5}$, Yolene Lefebvre$^{5}$, 
    Qusay Mandoorah$^{6}$, Rafael Sanchez-Salas$^{6}$, Petr Macek$^{6}$, Xavier Cathelineau$^{6}$, 
    Martin Eklund$^{7}$, Alistair E.W. Johnson$^{2,8,9}$, Andrew H. Feifer$^{1}$, Alexandre R. Zlotta$^{1,10}$*\n

    1. Division of Urology, Department of Surgery, University of Toronto, Toronto, Ontario, Canada
    1. Temerty Centre for AI Research and Education in Medicine, University of Toronto, Toronto, Ontario, Canada
    1. Temerty Faculty of Medicine, University of Toronto, Toronto, Ontario, Canada
    1. Faculty of Medicine, Queen's University, Kingston, Ontario, Canada
    1. Jules Bordet Institute, Brussels, Belgium
    1. L'Institut Mutualiste Montsouris, Paris, France
    1. Department of Medical Epidemiology and Biostatistics, Karolinska Institutet, Stockholm, Sweden
    1. Division of Biostatistics, Dalla Lana School of Public Health, University of Toronto, Toronto, Ontario, Canada
    1. Vector Institute, Toronto, Ontario, Canada
    1. Division of Urology, Department of Surgery, Mount Sinai Hospital, University of Toronto, Toronto, Ontario, Canada

    For more information, the full manuscript is available [here] (#).
    """
    )

if __name__ == "__main__":
    st.set_page_config(page_title="SEPERA - Side-Specific Extra-Prostatic Extension Risk Assessment",
                       page_icon=":ribbonblue:",
                       layout="wide",
                       initial_sidebar_state="expanded"
                       )
    main()