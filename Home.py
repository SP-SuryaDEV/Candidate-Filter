import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time

def establishSheetsConnections():
  st.session_state.conn = st.experimental_connection('gsheets', type=GSheetsConnection)

def preprocessSheet(df, select=False):
  df.columns = [col.strip() for col in df.columns]
  phone_number_col = 'Phone number'
  df[phone_number_col] = df[phone_number_col].astype(str).str.strip('.0')

  time, name, *others = df.columns

  if select:
    df['Select'] = pd.Series([False for _ in range(len(df))])
    df = df[[time, name, 'Select'] + others]

  return df

def plotDataEditor(df):
  if len(df) <= 1:
    return st.dataframe(df)
    
  return st.data_editor(
      df,
      column_config={
        'Resume' : st.column_config.LinkColumn(
            "Resume", display_text="Open Resume"
        ),

        'LinkedIn Profile Link' : st.column_config.LinkColumn(
            "LinkedIn Profile", display_text="Open LinkedIn"
        ),

        'GitHub Profile Link' : st.column_config.LinkColumn(
            "GitHub Profile", display_text="Open GitHub"
        )
      }
    )

def evaluateChanges(df):
  return df[df['Select']][[col for col in df.columns if col != 'Select']]

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

    if not st.session_state.get('_loader_used'):
      with st.spinner('Logging In'):
        time.sleep(3)
        st.session_state._loader_used = True

    if not st.session_state.get('conn'):
      establishSheetsConnections()

    current_submissions = preprocessSheet(st.session_state.conn.read(worksheet='Form responses 1', usecols = list(range(int(st.secrets.COLS))), ttl=150), 
                                          select=True)
    verified = preprocessSheet(st.session_state.conn.read(worksheet='Verified', usecols = list(range(int(st.secrets.COLS))), ttl=150))

    st.write(':green[**Current Submissions**]')
    changes = plotDataEditor(current_submissions)

    st.dataframe(evaluateChanges(changes))

    st.write(':red[**Verified**]')
    plotDataEditor(verified)
