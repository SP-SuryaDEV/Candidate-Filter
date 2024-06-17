import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

def establishSheetsConnections():
  st.session_state.conn = st.experimental_connection('gsheets', type=GSheetsConnection)



def isValidEmail(email):
  return email.find('@') > -1 and email.find('.') > -1
  
if not st.experimental_user.get('email'):
  st.session_state.logged_in = False
  
  with st.form(key='login'):
    email = st.text_input('Enter Authorized Email:', placeholder='Email')
  
    submit = st.form_submit_button('Authenticate')

    if submit:
      if not isValidEmail(email):
        st.error('Enter Valid Email to Authenticate')
      else:
        if email == st.secrets['EMAIL_KEY']:
          st.experimental_user.email = email
          st.session_state.logged_in = True

if st.session_state.get('logged_in'):
  if st.session_state.logged_in == True:
    st.success('Logged In')
