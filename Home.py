import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime
import time
import os

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

  df['Time'] = pd.to_datetime(df['Time'])

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
    worksheets = Cacher.readWorksheets()

    if worksheets:
      with open('worksheets.cache', 'a') as file:
        file.write(f'{worksheet_name}, ')
    else:
      with opem('worksheets.cache', 'w') as file:
        file.write(f'{worksheet_name}, ')
    

  @staticmethod
  def readWorksheets():
    if os.path.exists('worksheets.cache'):
      worksheets = open('worksheets.cache', 'r').read().strip().split(', ')
      worksheets[-1] = worksheets[-1].strip(',')
      return worksheets
    return None

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

  def getData(worksheet_name):
    return preprocessSheet(st.session_state.conn.read(worksheet=worksheet_name, usecols = list(range(int(st.secrets.COLS))), ttl=5))
    
@st.experimental_dialog('Commit Changes?')
def commitChanges(df):
  options = [
    'Append To Verified',
    'Create a New Worksheet',
    'Append to Existing Worksheet'
  ]

  option_to_commit = st.selectbox(
    label='Commit By Which Option',
    options=options,
    index=None,
    placeholder='Select an Option'
  )

  if option_to_commit:
    if option_to_commit == options[0]:
      Worksheet.updateWorksheet(
        'Verified',
        pd.concat([getVerified(), df]).drop_duplicates()
      )
      st.rerun()
      
    if option_to_commit == options[1]:

      def getWorksheetName():
        worksheets = Cacher.readWorksheets()
        
        new_worksheet_name = st.text_input('Enter New Worksheet Name').strip()
        submit = st.button(f'Create New Worksheet with name {new_worksheet_name}')

        if submit:
          if worksheets:
            if new_worksheet_name in worksheets:
              st.error('Worksheet Already Exists... Enter Unique Name.')
            else:
              return new_worksheet_name
          else:
            return new_worksheet_name

      new_worksheet_name = getWorksheetName()

      if new_worksheet_name:
        Cacher.newWorksheet(new_worksheet_name)
        Worksheet.createNewWorksheet(new_worksheet_name, df)
        st.rerun()
        
    if option_to_commit == options[2]:
      existing_worksheets = Cacher.readWorksheets()

      if existing_worksheets:
        worksheet = st.selectbox(label='Select an Existing Worksheet', placeholder='Select an Existing Worksheet', options=existing_worksheets, index=None)

        if worksheet:
          Worksheet.updateWorksheet(
            worksheet,
            pd.concat([Worksheet.getData(worksheet), df], axis=0).drop_duplicates()
          )
          st.rerun()
      else:
        st.error('No Existing Worksheets Found')
      

def getResponses():
  ''' A Function to Get all submitted responses from Form Responses Worksheet'''
  
  return preprocessSheet(st.session_state.conn.read(worksheet='Form responses 1', usecols = list(range(int(st.secrets.COLS))), ttl=150), 
                          select=True)

def getVerified():
  '''A Function to Get all verified responses from Verified Responses Worksheet'''
  
  return preprocessSheet(st.session_state.conn.read(worksheet='Verified', usecols = list(range(int(st.secrets.COLS))), ttl=5))

def isValidEmail(email):
  return email.find('@') > -1 and email.find('.') > -1



if not st.session_state.get('logged_in'):
  st.session_state.logged_in = False
  st.set_page_config(page_title='Login')
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
    st.set_page_config(layout='wide', page_title='Dashboard')

    if not st.session_state.get('_loader_used'):
      with st.spinner('Logging In'):
        time.sleep(3)
        st.session_state._loader_used = True

    if not st.session_state.get('conn'):
      establishSheetsConnections()

    current_submissions = getResponses()
    verified = getVerified()

    st.write('### :blue[**Current Submissions**]')

    st.session_state.cs_filtered = current_submissions.copy()
    
    bound = st.container(border=True)
    _name, _n_sw_toggle, _phone, _email, _email_sw_toggle = bound.container().columns([0.5, 0.2, 0.4, 0.4, 0.2])

    name = _name.text_input('Name', placeholder='Enter Name')
    
    _n_sw_toggle.write('')
    _n_sw_toggle.write('')
    name_sw = _n_sw_toggle.toggle('Starts with', value=False)

    phone = _phone.text_input('Phone', placeholder='Enter Phone')

    _email_sw_toggle.write('')
    _email_sw_toggle.write('')
    email_sw = _email_sw_toggle.toggle('Starts with ', value=False)
    
    email = _email.text_input('Email', placeholder='Enter Email')

    if name != '':
      if name_sw:
        st.session_state.cs_filtered = st.session_state.cs_filtered[st.session_state.cs_filtered['Name'].str.lower().str.startswith(name.lower())]
      else:
        st.session_state.cs_filtered = st.session_state.cs_filtered[st.session_state.cs_filtered['Name'].str.lower().str.contains(name.lower())]

    if phone != '':
      st.session_state.cs_filtered = st.session_state.cs_filtered[st.session_state.cs_filtered['Phone number'].str.startswith(phone)]

    if email != '':
      if email_sw:
        st.session_state.cs_filtered = st.session_state.cs_filtered[st.session_state.cs_filtered['Email'].str.startswith(email.lower())]
      else:
        st.session_state.cs_filtered = st.session_state.cs_filtered[st.session_state.cs_filtered['Email'].str.contains(email.lower())]
        
    _date, _college, _college_sw_toggle, _year, _department = bound.container().columns([0.2, 0.5, 0.2, 0.3, 0.2])
    
    date = _date.selectbox(
      label='Select Date',
      options=['All'] + list(st.session_state.cs_filtered['Time'].dt.strftime('%d-%m-%Y').unique()),
    )

    college_name = _college.text_input('College Name', placeholder='Enter College Name')

    _college_sw_toggle.write('')
    _college_sw_toggle.write('')
    collge_sw = _college_sw_toggle.toggle('Starts with  ', value=False)
    
    year = _year.selectbox(
      label='Select Year',
      options=['1st Year', '2nd Year', '3rd Year', '4th Year'],
      index=None,
      placeholder='Select Year'
    )

    department = _department.selectbox(label='Select Department', options=st.session_state.cs_filtered['Department'].unique(), index=None)
    
    if date:
      if date != 'All':
        st.session_state.cs_filtered = st.session_state.cs_filtered[st.session_state.cs_filtered['Time'].dt.strftime('%d-%m-%Y') == date]

    if college_name = '':
      if college_sw:
        st.session_state.cs_filtered = st.session_state.cs_filtered[st.session_state.cs_filtered['College'].str.startswith(college_name.lower())]
      else:
        st.session_state.cs_filtered = st.session_state.cs_filtered[st.session_state.cs_filtered['College'].str.contains(college_name.lower())]

    if year:
      st.session_state.cs_filtered = st.session_state.cs_filtered[st.session_state.cs_filtered['Year'].str.strip() == year.strip()]

    if department:
      st.session_state.cs_filtered = st.session_state.cs_filtered[st.session_state.cs_filtered['Department'].str.strip() == department.strip()]

      
    changes = plotDataEditor(st.session_state.cs_filtered)
    
    st.write('### :gray[**Buffer**]')
    st.dataframe(evaluateChanges(changes))
    
    _, center, __ = st.columns([0.4, 0.45, 0.1])
    use_predefined_buffer_options = center.button('Use Predifined Buffer Options')

    st.write('### :green[**Verified**]')
    plotDataEditor(verified)

    commit = st.button('Commit Changes')

    if commit:
      eval_changes = evaluateChanges(changes)
      commitChanges(eval_changes)

  
