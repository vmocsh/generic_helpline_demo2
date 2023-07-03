class Session:
    """
    Session option for call
    """
    #Added choices for display_sub_option and get_sub_option
    WELCOME = 0
    DISPLAY_LANGUAGE = 1
    GET_LANGUAGE = 2
    DISPLAY_OPTION = 3
    GET_OPTION = 4
    DISPLAY_SUB_OPTION = 5
    GET_SUB_OPTION = 6
    DISPLAY_TERMS = 7
    GET_TERMS = 8
    CALL_EXIT = 9
    CALL_FORWARD = 10
    CALL_DIRECT = 11
    INTRO1 = 12
    GET_INTRO1_INP = 13
    INTRO2 = 14
    GET_INTRO2_INP = 15
    DISPLAY_OPTION_2 = 16
    GET_OPTION_2 = 17



    SESSION_CHOICES = (
        (WELCOME, 'welcome'),
        (DISPLAY_LANGUAGE, 'display_language'),
        (GET_LANGUAGE, 'get_language'),
        (DISPLAY_OPTION, 'display_option'),
        (GET_OPTION, 'get_option'),
        (DISPLAY_SUB_OPTION, 'display_sub_option'),
        (GET_SUB_OPTION, 'get_sub_option'),
        (DISPLAY_TERMS, 'display_terms'),
        (GET_TERMS, 'get_terms'),
        (CALL_EXIT, 'call_exit'),
        (CALL_FORWARD, 'call_forward'),
        (CALL_DIRECT, 'call_direct'),
        (INTRO1, 'intro_1'),
        (GET_INTRO1_INP, 'get_intro_1_inp'),
        (INTRO2, 'intro_2'),
        (GET_INTRO2_INP, 'get_intro_2_inp'),
        (DISPLAY_OPTION_2, 'display_option_2'),
        (GET_OPTION_2, 'get_option_2'),

    )



