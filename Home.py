import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

def isValidEmail(email):
  return email.find('@') > -1 and email.find('.') > -1

with st.form(key='login'):
  email = st.text_input('Enter Authorized Email:', placeholder='Email')

  if email and not isValidEmail(email):
    st.error('Enter a Valid Email')

  submit = st.form_submit_button('Authenticate')
