import pandas as pd
import streamlit as st
# from streamlit_gsheets import GSheetsConnection
import datetime
import time
import random
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
      with open('worksheets.cache', 'w') as file:
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

def setBuffer(df):
  st.session_state.sheet1['Select'] = pd.Series([False for _ in range(len(st.session_state.sheet1))])
  st.session_state.buffer = df.copy()

@st.experimental_dialog("Load Predefined Buffer?")
def predefinedBufferOptions(sheet1, sheet2):
  options = [
    'In Sheet1, Not in Sheet2',
    'In Sheet2, Not in Sheet1',
    'Both in Sheet1 and Sheet2 only [Intersection]',
    'Merge both sheets and Remove Duplicates [Union]'
  ]

  option = st.selectbox(
    options=options,
    label='Predefined Option',
    placeholder='Select Predefined Option',
    index=None
  )

  if option:
    if option == options[0]:
      setBuffer(sheet1.merge(sheet2, indicator=True, how='left').loc[lambda x: x['_merge'] == 'left_only'].drop(columns=['_merge']))
    elif option == options[1]:
      setBuffer(sheet2.merge(sheet1, indicator=True, how='left').loc[lambda x: x['_merge'] == 'left_only'].drop(columns=['_merge']))
    elif option == options[2]:
      setBuffer(pd.merge(sheet1, sheet2))
    elif option == options[3]:
      setBuffer(pd.concat([sheet1, sheet2]).drop_duplicates().reset_index(drop=True))

  

def Filter(sheet, key):
  bound = st.container(border=True)
  _name, _n_sw_toggle, _phone, _email, _email_sw_toggle = bound.container().columns([0.5, 0.2, 0.4, 0.4, 0.2])

  name = _name.text_input('Name', placeholder='Enter Name', key=f'{key}')
  
  _n_sw_toggle.write('')
  _n_sw_toggle.write('')
  name_sw = _n_sw_toggle.toggle('Starts with', value=False, key=f'{key+1}')

  phone = _phone.text_input('Phone', placeholder='Enter Phone', key=f'{key+2}')

  _email_sw_toggle.write('')
  _email_sw_toggle.write('')
  email_sw = _email_sw_toggle.toggle('Starts with ', value=False, key=f'{key+3}')
  
  email = _email.text_input('Email', placeholder='Enter Email', key=f'{key+4}')

  if name != '':
    if name_sw:
      sheet = sheet[sheet['Name'].str.lower().str.startswith(name.lower())]
    else:
      sheet = sheet[sheet['Name'].str.lower().str.contains(name.lower())]

  if phone != '':
    sheet = sheet[sheet['Phone number'].str.startswith(phone)]

  if email != '':
    if email_sw:
      sheet = sheet[sheet['Email'].str.startswith(email.lower())]
    else:
      sheet = sheet[sheet['Email'].str.contains(email.lower())]
      
  _date, _college, _college_sw_toggle, _year, _department = bound.container().columns([0.2, 0.5, 0.2, 0.3, 0.2])
  
  date = _date.selectbox(
    label='Date',
    options=['All'] + list(sheet['Time'].dt.strftime('%d-%m-%Y').unique()),
    key=f'{key+5}'
  )

  college_name = _college.text_input('College Name', placeholder='Enter College Name', key=f'{key+6}')

  _college_sw_toggle.write('')
  _college_sw_toggle.write('')
  college_sw = _college_sw_toggle.toggle('Starts with  ', value=False, key=f'{key+7}')
  
  year = _year.selectbox(
    label='Year',
    options=['1st Year', '2nd Year', '3rd Year', '4th Year'],
    index=None,
    placeholder='Select Year',
    key=f'{key+8}'
  )

  department = _department.selectbox(label='Department', options=sheet['Department'].unique(), index=None,
                                    placeholder='Select Department', key=f'{key+9}')
  
  if date:
    if date != 'All':
      sheet = sheet[sheet['Time'].dt.strftime('%d-%m-%Y') == date]

  if college_name != '':
    if college_sw:
      sheet = sheet[sheet['College'].str.startswith(college_name.lower())]
    else:
      sheet = sheet[sheet['College'].str.contains(college_name.lower())]

  if year:
    sheet = sheet[sheet['Year'].str.strip() == year.strip()]

  if department:
    sheet = sheet[sheet['Department'].str.strip() == department.strip()]

  _first, _second, _third = bound.container().columns(3)

  first = _first.selectbox('1st Priority', ['Any'] + list(sheet['Which skill do you prioritize the most (1st priority)?'].unique()), key=f'{key+10}')
  second = _second.selectbox('2nd Priority', ['Any'] + list(sheet['Which skill do you prioritize next (2nd priority)?'].unique()), key=f'{key+11}')
  third = _third.selectbox('3rd Priority', ['Any'] + list(sheet['Which skill do you prioritize after that (3rd priority)?'].unique()), key=f'{key+12}')

  if first:
    if first != 'Any':
      sheet = sheet[sheet[sheet.columns[7]].str.strip() == first]
  if second:
    if second != 'Any':
      sheet = sheet[sheet[sheet.columns[12]].str.strip() == second]
  if third:
    if third != 'Any':
      sheet = sheet[sheet[sheet.columns[13]].str.strip() == third]


  _, __, _count, *___ = bound.container().columns([1, 1.75, 1, 1 ,1])
  _count.metric(':green[**Filtered Count**]', f'-   {len(sheet)}   -')

      

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

    st.session_state.sheet1 = getResponses()
    st.session_state.sheet2 = getVerified()

    

    st.write('## :blue[**Current Submissions**]')
    Filter(st.session_state.sheet1, 1)
    buffer = plotDataEditor(st.session_state.sheet1)

    st.divider()
    
    st.write('## :gray[**Buffer**]')
    
    _, center, __ = st.columns([0.4, 0.45, 0.1])
    use_predefined_buffer_options = center.toggle('Use Predifined Buffer Options', value=False)

    
   
    if len(st.session_state.sheet1) != 0:
      st.session_state.buffer = evaluateChanges(buffer)
      with st.expander("Filter"):
        Filter(st.session_state.buffer, 20)
      st.dataframe(st.session_state.buffer)
    else:
      st.info('No Options to Select From.')
  

    st.divider()
    
    st.write('## :green[**Verified**]')
    with st.expander('Filter'):
      Filter(st.session_state.sheet2, 40)
    plotDataEditor(st.session_state.sheet2)

    commit = st.button('Commit Changes')

    if commit:
      eval_changes = evaluateChanges(st.session_state.buffer)
      commitChanges(st.session_state.buffer)

  
