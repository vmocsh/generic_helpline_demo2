"""
Helper class to manage status options of models
"""
'''

class SurveyStatusOptions:
    """
    Status options available to Client
    """
    ACTIVE = 1
    BLOCKED = 2
    STATUS_CHOICES = (
        (ACTIVE, 'Active'),
        (BLOCKED, 'Blocked'),
    )   
    '''

MAX_SURVEY_TASKS_FOR_HELPER = 5