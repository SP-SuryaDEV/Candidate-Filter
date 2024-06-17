import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

def isValidEmail(email):
  return email.contains('@') and email.contains('.')

with st.form(key='login):
  email = st.text_input('Enter Authorized Email:', placeholder='Email')

  if email and not isValidEmail(email):
    st.error('Enter a Valid Email')
