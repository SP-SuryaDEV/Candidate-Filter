import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time

def establishSheetsConnections():
  st.session_state.conn = st.experimental_connection('gsheets', type=GSheetsConnection)

def preprocessSheet(df):
  df.columns = [col.strip() for col in df.columns]
  phone_number_col = 'Phone Number'
  df[phone_number_col] = df[phone_number_col].astype(str).str.strip('.0')

  return df

def isValidEmail(email):
  return email.find('@') > -1 and email.find('.') > -1
  
if not st.session_state.get('logged_in'):
  st.session_state.logged_in = False
  
  with st.form(key='login'):
    email = st.text_input('Enter Authorized Email:', placeholder='Email')
  
    submit = st.form_submit_button('Authenticate')

    if submit:
      if not isValidEmail(email):
        st.error('Enter Valid Email to Authenticate')
      else:
        if email == st.secrets['EMAIL_KEY']:
          st.session_state.logged_in = True

else:
  if st.session_state.logged_in == True:
    st.set_page_config(layout='wide')
    
    with st.spinner('Logging In'):
      time.sleep(3)

    if not st.session_state.get('conn'):
      establishSheetsConnections()

    current_submissions = preprocessSheet(st.session_state.conn.read(worksheet='Form responses 1', usecols = list(range(int(st.secrets.COLS))), ttl=30))
    verified = preprocessSheet(st.session_state.conn.read(worksheet='Verified', usecols = list(range(int(st.secrets.COLS))), ttl=30))

    st.write(':green[**Current Submissions**]')
    st.data_editor(
      current_submissions,
      column_config={
        'Resume' : st.column_config.LinkColumn(
            "Resume", display_text="Open Resume"
        )
    )

    st.write(':red[**Verified**]')
    st.data_editor(verified)
