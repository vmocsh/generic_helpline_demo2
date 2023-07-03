from ivr.options import Session

# URLs
BASE_URL = 'http://vmocsh.cse.iitb.ac.in/demo2/'
AUDIO_URL = 'http://vmocsh.cse.iitb.ac.in/demo2/media/'
LOGIN_URL = '/demo2/web_auth/login/'
STATIC_URL_APPEND = '/demo2'
URL_APPEND = 'demo2/'
HELPLINE_NAME = 'Demo Helpline'

# IVRS 
ALL_LANGUAGES = ['Hindi']
CATEGORIES = ['corona-positive-o2below90', 'corona-positive-o2above90','corona-negative-o2below90', 'corona-negative-o2above90' , 'non-corona-o2below90','non-corona-o2above90']
SUBCATEGORIES = [[],[] ,[],[]]
HELPER_LEVELS = ['PRIMARY', 'SECONDARY']
HELPER_TYPES = ['DIRECT', 'INDIRECT']
DIRECT_DAYS = ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY']
START_TIME = '9:00'
END_TIME = '18:00'
SESSION_LEVELS = [Session.INTRO1, Session.GET_INTRO1_INP, Session.INTRO2, Session.GET_INTRO2_INP, Session.DISPLAY_OPTION, Session.GET_OPTION, Session.DISPLAY_OPTION_2, Session.GET_OPTION_2, Session.DISPLAY_SUB_OPTION, Session.GET_SUB_OPTION, Session.CALL_EXIT, Session.CALL_DIRECT]
TAG_LIST_1 = ['Doctor1', 'Doctor2']
TAG_LIST_2 = ['8am-12pm', '2pm-6pm']

# Account Details
SMS_USER = 'iitbombay'
SMS_PWD = 'vmocsh@2'
#SMS_SENDERID = 'MAASPH'
SMS_SENDERID = 'HOSPITAL_HELPLINE'
API_KEY = 'KK7a90e699849af7b22114bb564eae644b'

# DJANGO ADMIN Details
USERNAME = 'admin'
PASSWORD = 'r@j2331992'

# Features
FEEDBACK_NEEDED = False  # False for IITB helpline
MULTILEVEL_ALLOCATION = True  # True incase of BAIF
FOLLOWUP_TASK_NEEDED = True  # For other helplines, follow up tasks are not needed
CALL_RECORDING_NEEDED = False
SUB_CATEGORY_ALLOCATION = True  # True for IITB helpline
TOLLFREE = False #True
CLICK_TO_CONNECT = False #True
MISSED_CALL_NEEDED = False  # True for BAIF Helpline
QANDA_OPTIONAL = True  #If QANDA_OPTIONAL is true make FEEDBACK_NEEDED false
MIN_CALL_ATTEMPTS = 0
DISPLAY_TERMS_IN_IVR = False


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
SUBJECT='Weekly report of ' + HELPLINE_NAME
BODY='Please find attached the weekly report of helpers. The summary of activity in the week is listed below: '

# Configurable parameters
NO_OF_HELPERS = 4
TIMEOUT_HOURS = 24
NUMBER_FEEDBACK_TASKS = 1

# Version details
CURRENT_VERSION = '1'
LAST_UPDATED_ON = '06/05/2019'
