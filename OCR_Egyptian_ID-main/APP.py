import os
import tempfile
from PIL import Image
import streamlit as st
from utils import detect_and_process_id_card

st.set_page_config(page_title='ID Egyptian Card ', page_icon='💳', layout='wide')

if "current_tab" not in st.session_state:
    st.session_state.current_tab = "Home"

tabs = ["Home", "Guide"]
st.session_state.current_tab = st.sidebar.radio("Navigation", tabs)

if st.session_state.current_tab == "Home":
    st.subheader("Egyptian ID Card Verification / Registration 💳")
    method = st.radio("Choose method", ["Use Camera", "Upload Image"])

    path = None

    if method == "Use Camera":
        captured_image = st.camera_input("Capture your ID card")
        if captured_image:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp:
                temp.write(captured_image.getbuffer())
                path = temp.name
    else:
        uploaded_file = st.file_uploader("Upload ID card image", type=["jpg","jpeg","png"])
        if uploaded_file:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp:
                temp.write(uploaded_file.read())
                path = temp.name

    if path and st.button("Verify ID"):
        result = detect_and_process_id_card(path)
        os.remove(path)  # cleanup

        if result["verified"]:
            st.success("✅ ID verified successfully. You can complete registration.")
            first_name, second_name, full_name, nid, address, birth, gov, gender = result["data"]
            st.image("d2.jpg", use_container_width=True)
            st.write("Full Name:", full_name)
            st.write("National ID:", nid)
            st.write("Birth Date:", birth)
            st.write("Governorate:", gov)
            st.write("Gender:", gender)
            st.write("Address:", address)
        else:
            st.error("❌ " + result["message"])

elif st.session_state.current_tab == "Guide":
    st.title("How to use our application 📖")
    st.write("""
    ## Project Overview
    Upload or capture your Egyptian ID card to verify your identity.
    The system will check the card and extract the details.

    ## Steps:
    1. Choose camera or upload image.
    2. Capture or select the ID card.
    3. Click Verify ID.
    4. If verified, proceed to registration.
    """)
