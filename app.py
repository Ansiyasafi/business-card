import pandas as pd
import streamlit as st
import numpy as np
from streamlit_option_menu import option_menu
import easyocr
import mysql.connector 
from PIL import Image
import cv2
import os
import matplotlib.pyplot as plt
import re
import sqlite3


st.set_page_config(page_title="BIZCARD:EXTRACTING DATA FROM BUSINESS CARD WITH OCR",
                        page_icon=None,
                         layout= "wide",
                        initial_sidebar_state= "expanded",
                        menu_items={'About': """# This OCR app is created by *Ansiya*!"""})
st.markdown("<h1 style='text-align: center; color: Red;'>BIZCARD:EXTRACTING DATA FROM BUSINESS CARD WITH OCR</h1>", unsafe_allow_html=True)

def setting_bg():
    st.markdown(f""" <style>.stApp {{
                        background: url("https://cutewallpaper.org/22/plane-colour-background-wallpapers/189265759.jpg");
                        background-size: cover}}
                     </style>""",unsafe_allow_html=True) 
setting_bg()


with st.sidebar:

  selected = option_menu(None,[ "card upload & data extract", 'modify the data'])
                    #    icons=["cloud-upload","pencil-square"],
                    #    default_index=0,
                    #    orientation="horizontal",
                    #    styles={"nav-link": {"font-size": "35px", "text-align": "centre", "margin": "0px", "--hover-color": "#6495ED"},
                    #            "icon": {"font-size": "35px"},
                    #            "container" : {"max-width": "6000px"},
                    #            "nav-link-selected": {"background-color": "#6495ED"}})



#connecting sql
config = {
    'user':'root', 'password':'Ansiya93',
    'host':'127.0.0.1', 'database':'businesscard'}

print(config)
connection = mysql.connector.connect(**config)
cursor=connection.cursor()
print(cursor)

create_table= """CREATE TABLE IF NOT EXISTS Card_info
                   (id INTEGER PRIMARY KEY AUTO_INCREMENT,
                    company_name TEXT,
                    card_holder TEXT,
                    designation TEXT,
                    mobile_number VARCHAR(50),
                    email TEXT,
                    website TEXT,
                    area TEXT,
                    city TEXT,
                    state TEXT,
                    pin_code VARCHAR(10),
                    image LONGBLOB
                    )"""
cursor.execute(create_table)
connection.commit()

# UPLOAD AND EXTRACT MENU
if selected == "card upload & data extract":
    st.markdown("### Upload a Business Card")
    uploaded_card = st.file_uploader("upload here",label_visibility="collapsed",type=["png","jpeg","jpg"])

# INITIALIZING THE EasyOCR READER
    if uploaded_card is not None:
        reader = easyocr.Reader(['en'])
        saved_img = os.getcwd()+ "\\" + "images"+ "\\"+ uploaded_card.name
        result = reader.readtext(saved_img,detail = 0,paragraph=False)
   
    # # CONVERTING IMAGE TO BINARY TO UPLOAD TO SQL DATABASE
        def img_to_binary(file):
            # Convert image data to binary format
            with open(file, 'rb') as file:
                binaryData = file.read()
            return binaryData

        # #
        # if uploaded_card is not None:
        #     def save_card(uploaded_card):
        #         uploaded_cards_dir = os.path.join(os.getcwd(), "uploaded_cards")
        #         with open(os.path.join(uploaded_cards_dir, uploaded_card.name), "wb") as f:
        #             f.write(uploaded_card.getbuffer())


        #     save_card(uploaded_card)
        #     #view uploaded card
        #     image_width=400
        #     st.image(uploaded_card,width=image_width, caption="Uploaded Card Image")
        data = {"company_name" : [],
                        "card_holder" : [],
                        "designation" : [],
                        "mobile_number":[],
                        "email" : [],
                        "website" : [],
                        "area" : [],
                        "city" : [],
                        "state" : [],
                        "pin_code" : [],
                        "image" :img_to_binary(saved_img)}


        def get_data(res):
            for ind,i in enumerate(res):

                # To get WEBSITE_URL
                if "www " in i.lower() or "www." in i.lower():
                    data["website"].append(i)
                elif "WWW" in i:
                    data["website"] = res[4] +"." + res[5]

                # To get EMAIL ID
                elif "@" in i:
                    data["email"].append(i)

                # To get MOBILE NUMBER
                elif "-" in i:
                    data["mobile_number"].append(i)
                    if len(data["mobile_number"]) ==2:
                        data["mobile_number"] = " & ".join(data["mobile_number"])

                # To get COMPANY NAME  
                elif ind == len(res)-1:
                    data["company_name"].append(i)

                # To get CARD HOLDER NAME
                elif ind == 0:
                    data["card_holder"].append(i)

                # To get DESIGNATION
                elif ind == 1:
                    data["designation"].append(i)

                # To get AREA
                if re.findall('^[0-9].+, [a-zA-Z]+',i):
                    data["area"].append(i.split(',')[0])
                elif re.findall('[0-9] [a-zA-Z]+',i):
                    data["area"].append(i)

                # To get CITY NAME
                match1 = re.findall('.+St , ([a-zA-Z]+).+', i)
                match2 = re.findall('.+St,, ([a-zA-Z]+).+', i)
                match3 = re.findall('^[E].*',i)
                if match1:
                    data["city"].append(match1[0])
                elif match2:
                    data["city"].append(match2[0])
                elif match3:
                    data["city"].append(match3[0])

                # To get STATE
                state_match = re.findall('[a-zA-Z]{9} +[0-9]',i)
                if state_match:
                        data["state"].append(i[:9])
                elif re.findall('^[0-9].+, ([a-zA-Z]+);',i):
                    data["state"].append(i.split()[-1])
                if len(data["state"])== 2:
                    data["state"].pop(0)

                # To get PINCODE        
                if len(i)>=6 and i.isdigit():
                    data["pin_code"].append(i)
                elif re.findall('[a-zA-Z]{9} +[0-9]',i):
                    data["pin_code"].append(i[10:])
        get_data(result)

        #to create dataframe
        df = pd.DataFrame(data)
        st.success("##DATA EXTRACTED!!!")
        st.write(df)
        if st.button("Upload to Database"):
                for i,row in df.iterrows():
                    #here %S means string values 
                    sql = """INSERT INTO card_info(company_name,card_holder,designation,mobile_number,email,website,area,city,state,pin_code,image)
                            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
                    cursor.execute(sql,tuple(row))
                    connection.commit()
                st.success("#### Uploaded to database successfully!")
if selected == "modify the data": 
    column1,column2 = st.columns(2,gap="large")
    try:
        with column1:
            cursor.execute('SELECT card_holder FROM card_info')
            result=cursor.fetchall()
            list1=np.array(result) 
            list2=list1.tolist()
            print(list2)
            res=[]
            for i in range (0,len(list2)):
                res.append(list2[i][0])
            print(res)  
            selected_card = st.selectbox("Select a card holder name to update", res)
            st.markdown("#### Update or modify any data below")
            cursor.execute("select company_name,card_holder,designation,mobile_number,email,website,area,city,state,pin_code from card_info WHERE card_holder=%s",
                            (selected_card,))
            result1= cursor.fetchone()

            for i in range(0,len(result1)):
                get=['company_name','card_holder','designation','mobile_number','email','website','area','city','state','pin_code']
                st.info(get[i])
                container = st.container(border=True)
                container.write(result1[i])

            st.markdown('## :red[DISPLAYING ALL THE INFORMATIONS FOR MODIFICATION]')
            company_name =st.text_input("Company_Name", result1[0])
            card_holder =st.text_input("Card_Holder", result1[1])
            designation = st.text_input("Designation", result1[2])
            mobile_number = st.text_input("Mobile_Number", result1[3])
            email = st.text_input("Email", result1[4])
            website = st.text_input("Website", result1[5])
            area = st.text_input("Area", result1[6])
            city = st.text_input("City", result1[7])
            state = st.text_input("State", result1[8])
            pin_code = st.text_input("Pin_Code", result1[9])
            if st.button("Commit changes to DB"):
                    # Update the information for the selected business card in the database
                cursor.execute("""UPDATE card_info SET company_name=%s,card_holder=%s,designation=%s,mobile_number=%s,email=%s,website=%s,area=%s,city=%s,state=%s,pin_code=%s
                                    WHERE card_holder=%s""", (company_name,card_holder,designation,mobile_number,email,website,area,city,state,pin_code,selected_card))
                connection.commit()
                st.success("Information updated in database successfully.")

        with column2:
            st.markdown('## :red[PROCESS FOR DELETING THE DATA]')
            cursor.execute('SELECT card_holder FROM card_info')
            result=cursor.fetchall()
            list1=np.array(result) 
            list2=list1.tolist()
            print(list2)
            res=[]
            for i in range (0,len(list2)):
                res.append(list2[i][0])
            print(res)  
            selected_card = st.selectbox("Select a card holder name to delete", res)
            if st.button("Yes Delete Business Card"):
                cursor.execute(f"DELETE FROM card_info WHERE card_holder='{selected_card}'")
                connection.commit()
                st.success("Business card information deleted from database.")        


                                        
    except:
        st.warning("There is no data available in the database")







