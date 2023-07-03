from ivr.options import Session

# URLs
BASE_URL = 'http://vmocsh.cse.iitb.ac.in/nutrition/'
AUDIO_URL = 'http://vmocsh.cse.iitb.ac.in/nutrition/media/'
LOGIN_URL = '/nutrition/web_auth/login/'
STATIC_URL_APPEND = '/nutrition'
URL_APPEND = 'nutrition/'

# IVRS 
ALL_LANGUAGES = ['Hindi', 'Marathi', 'Gujarati', 'English', 'Tamil']
CATEGORIES = ['Premature', 'Breastfeeding', 'ChildNutrition', 'MotherNutrition']
SUBCATEGORIES = [[], [], [], []]
HELPER_LEVELS = ['PRIMARY', 'SECONDARY']
SESSION_LEVELS = [Session.DISPLAY_LANGUAGE, Session.GET_LANGUAGE, Session.WELCOME, Session.DISPLAY_OPTION, Session.GET_OPTION, '', '', Session.DISPLAY_TERMS, Session.GET_TERMS, Session.CALL_EXIT]

# Account Details
SMS_USER = 'iitbombay'
SMS_PWD = 'vmocsh@2'
SMS_SENDERID = 'MAASPH'
API_KEY = 'KK7a90e699849af7b22114bb564eae644b'

# DJANGO ADMIN Details
USERNAME = 'admin'
PASSWORD = 'r@j2331992'

# Features
FEEDBACK_NEEDED = True # False for IITB helpline
MULTILEVEL_ALLOCATION = False # True incase of BAIF
FOLLOWUP_TASK_NEEDED = True # For other helplines, follow up tasks are not needed
CALL_RECORDING_NEEDED = False
SUB_CATEGORY_ALLOCATION = False # True for IITB helpline
TOLLFREE = True
CLICK_TO_CONNECT = True
MISSED_CALL_NEEDED = False # True for BAIF Helpline

# Notifications and messages
TIMEOUT_TASK_NOTIF = "Timed Out task has been assigned"
NEW_TASK_NOTIF = "New Task Has Been Assigned"
REALLOCATE_TASK_NOTIF = "Accepted Task has been reallocated"
ACTIVATION_NOTIF = "Account activated. Please select category and language in profile on first login attempt."
PROMOTIONAL_SMS = 'Hey!%20 Its%20 been%20 long%20 since%20 you%20 called%20 Maa%20 aur%20 Shishu%20 Poshan%20 Helpline%20 tollfree%20 number%20 ' \
					      '18002002098.%20 Free%20 advice%20 on%20 maternal%20 nutrition,%20 lactation,%20 child%20 nutrition%20 by%20 our%20 team%20 of%20 ' \
					      'doctors,%20 nutritionists%20 and%20 field%20 officers%20 with%20 10%20 plus%20 years%20 of%20 experience!%20 Please%20 spread%20 ' \
					      'this%20 number.'

# Weekly report parameters
HELPER_WEEKLY_REPORT='helper-wise.csv'
RECIPIENT_LIST=['Smartika']
SUBJECT='Weekly report of MAASPH'
BODY='Please find attached the weekly report of helpers. The summary of activity in the week is listed below: '

# Configurable parameters
NO_OF_HELPERS = 3
TIMEOUT_HOURS = 24
NUMBER_FEEDBACK_TASKS = 1

# Version details
CURRENT_VERSION = '1'
LAST_UPDATED_ON = '26/02/2019'