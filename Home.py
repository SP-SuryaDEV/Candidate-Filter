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

class Cacher:
  @staticmethod
  def newWorksheet(worksheet_name):
    with open('worksheets.cache', 'a') as file:
      file.append(f'{worksheet_name}, ')

  @staticmethod
  def readWorksheets():
    worksheets = open('worksheets.cache', 'r').read().strip().split(', ')
    return worksheets

class Worksheet:
  @staticmethod
  def createNewWorksheet(worksheet_name, df):
    st.session_state.conn.create(
      worksheet=worksheet_name, 
      data=df
    )

  @staticmethod
  def updateWorksheet(worksheet_name, df):
    st.session_state.conn.update(
      worksheet=worksheet_name, 
      data=df
    )
    
@st.experimental_dialog('Commit Changes?')
def commitChanges(df):
  options = [
    'Append To Verified',
    'Create a New Worksheet',
    'Append to Existing Worksheet'
  ]

  option_to_commit = st.selectbox(
    label='Commit By Which Option',
    options=options
  )

  if option_to_commit:
    if option_to_commit == options[0]:
      Worksheet.updateWorksheet(
        'Verified',
        pd.concat([getVerified(), df]).drop_duplicates()
      )
      
    if option_to_commit == options[1]:

      @st.experimental_dialog("Enter Name for New Worksheet")
      def getWorksheetName():
        worksheets = Cacher.readWorksheet()
        
        new_worksheet_name = st.text_input('Enter New Worksheet Name').strip()
        submit = st.button('Create New Worksheet')

        if submit:
          if new_worksheet_name in worksheets:
            st.error('Worksheet Already Exists... Enter Unique Name.')
            return None
          else:
            return new_worksheet_name

      new_worksheet_name = getWorksheetName()

      if new_worksheet_name:
        Worksheet.createNewWorksheet(new_worksheet_name, df)
        
    if option_to_commit == options[2]:
      st.success('Hello')
      

def getResponses():
  return preprocessSheet(st.session_state.conn.read(worksheet='Form responses 1', usecols = list(range(int(st.secrets.COLS))), ttl=150), 
                                          select=True)

def getVerified():
  return preprocessSheet(st.session_state.conn.read(worksheet='Verified', usecols = list(range(int(st.secrets.COLS))), ttl=5))

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

    current_submissions = getResponses()
    verified = getVerified()

    st.write(':blue[### **Current Submissions**]')
    changes = plotDataEditor(current_submissions)

    st.write(':green[### **Verified**]')
    plotDataEditor(verified)

    commit = st.button('Commit Changes')

    if commit:
      eval_changes = evaluateChanges(changes)
      commitChanges(eval_changes)
  
