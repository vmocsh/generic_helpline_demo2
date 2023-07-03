import datetime
import json
from django.utils import timezone
import requests
from django.http import HttpResponse
from django.views.generic import View
from constants import *
from ivr import kookoo
from management.models import HelpLine, AvailableSlot
from register_helper.models import HelperLevel, Helper, HelperCategory
from registercall.models import Task
from registercall.views import RegisterCall
from task_manager.models import Assign, Action
from task_manager.helpers import AssignAction
from task_manager.options import AssignStatusOptions, ActionStatusOptions
from .models import IVR_Call, Call_Forward, Misc_Audio, Misc_Category, IVR_Audio, Language, Call_Forward_Details, \
    FeedbackType, Feedback, FeedbackResponse
from register_helper.options import HelperLevel, LoginStatus

# Create your views here.
class IVR(View):
    def post_data(self, url, data):
        base_url = BASE_URL  # "http://vmocsh.cse.iitb.ac.in/nutrition/"
        #base_url = 'http://vmocsh.cse.iitb.ac.in:9030/hospital/'
        authentication = (USERNAME, PASSWORD)
        print("IVR post data")
        headers = {'Content-type': 'application/json'}
        resp = requests.post(base_url + url, data=json.dumps(data), headers=headers, auth=authentication, verify=True)
        print("Register call post response: ", resp.status_code)

    def call_helpers(self, task, helper, r):
        print('In call helpers')
        action = Action.objects.get(task=task)
        task.call_attempt = task.call_attempt + 1
        task.save()
        assign = Assign.objects.filter(action=action).exclude(status=AssignStatusOptions.ACCEPTED)
        assign.delete()
        assign = Assign.objects.create(helper=helper, action=action)
        helper_no = assign.helper.helper_number
        client_no = task.call_request.client.client_number
        Call_Forward.objects.all().delete()
        call_forward = Call_Forward(helper_no=helper_no[len(helper_no) - 10:], caller_no=client_no, task=task, type="regular")
        call_forward.save()
        call_forward_details = Call_Forward_Details(helper_no=helper_no, caller_no=client_no, task=task, type="regular")
        call_forward_details.save()
        r.addDial(dialnumber=helper_no, timeout="15")

    def get(self, request):
        audio_url = AUDIO_URL  # "http://vmocsh.cse.iitb.ac.in/nutrition/media/"
        r = kookoo.Response()
        sid = request.GET.get("sid")
        print("sid for new call is:", sid)
        try:
            call = IVR_Call.objects.get(sid=sid)
            session_next = int(call.session_next)
        except ValueError:
            print("SID not found for IVR call")
            session_next = Session.CALL_DIRECT
            pass
        except IVR_Call.DoesNotExist:
            print("SID not found for IVR call")
            session_next = Session.CALL_DIRECT
            pass

        if (((request.GET.get("event") == "Hangup" and request.GET.get("process") == "dial") or
             request.GET.get("event") == "Dial") and request.GET.get("status") == "answered"):

            cid = request.GET.get("cid")
            cid = self.fetch_number(cid)
            print("cid: ", cid)
            session_next = Session.CALL_FORWARD
            call_forward = Call_Forward.objects.filter(caller_no=cid)
            if call_forward:                                                   #direct call to helper and helper picked
                print('in direct call')
                call_forward = Call_Forward.objects.get(caller_no=cid)
                caller_no = self.fetch_number(cid)
                helper_no = call_forward.helper_no
                task = call_forward.task
                helper_no = self.fetch_number(helper_no)
                name = ""
                action = Action.objects.get(task=task)
                action.status = ActionStatusOptions.ASSIGNED
                action.save()
                helper = Helper.objects.get(helper_number=helper_no)
                assign = Assign.objects.get(action=action, helper=helper)
                assign.status = AssignStatusOptions.ACCEPTED
                assign.save()
                call_forward_details = Call_Forward_Details.objects.filter(helper_no=helper_no, caller_no=caller_no, task=task,
                                                                           status='initiated').order_by('-created')[0]
                call_forward_details.status = "completed"
                call_forward_details.call_duration = request.GET.get("callduration")
                call_forward_details.call_pickup_duration = request.GET.get("pickduration")
                call_forward_details.call_recording_name = name
                call_forward_details.save()
                call_forward.delete()
            else:                                                             #helper called client and client picked
                helper_no = self.fetch_number(cid)
                print(helper_no)
                if request.GET.get("data") != "-1":
                    name = requests.get(request.GET.get("data"))
                else:
                    name = ""
                call_forward = Call_Forward.objects.get(helper_no=helper_no)
                if call_forward.type == "survey":
                    caller_no = call_forward.caller_no
                    survey_task = call_forward.survey_task
                    caller_no = self.fetch_number(caller_no)
                    call_forward_details = Call_Forward_Details.objects.filter(helper_no=helper_no, caller_no=caller_no, survey_task=survey_task,
                                                                               status='initiated').order_by('-created')[0]
                    call_forward_details.status = "completed"
                    call_forward_details.call_duration = request.GET.get("callduration")
                    call_forward_details.call_pickup_duration = request.GET.get("pickduration")
                    call_forward_details.call_recording_name = name
                    call_forward_details.save()
                    call_forward.delete()
                else:
                    caller_no = call_forward.caller_no
                    task = call_forward.task
                    caller_no = self.fetch_number(caller_no)
                    call_forward_details = Call_Forward_Details.objects.filter(helper_no=helper_no, caller_no=caller_no, task=task,
                                                                               status='initiated').order_by('-created')[0]
                    call_forward_details.status = "completed"
                    call_forward_details.call_duration = request.GET.get("callduration")
                    call_forward_details.call_pickup_duration = request.GET.get("pickduration")
                    call_forward_details.call_recording_name = name
                    call_forward_details.save()
                    call_forward.delete()

        if ((request.GET.get("event") == "Dial" or request.GET.get("event") == "Hangup") and
                request.GET.get("status") == "not_answered"):
            try:
                cid = request.GET.get("cid")
                cid = self.fetch_number(cid)
                session_next = Session.CALL_FORWARD
                call_forward = Call_Forward.objects.filter(caller_no=cid)     #direct call to helper and helper did not pick
                if call_forward:
                    call_forward = Call_Forward.objects.get(caller_no=cid)
                    caller_no = self.fetch_number(cid)
                    call_forward = Call_Forward.objects.get(caller_no=caller_no)
                    helper_no = call_forward.helper_no
                    task = call_forward.task
                    helper_no = self.fetch_number(helper_no)
                    call_forward_details = Call_Forward_Details.objects.filter(helper_no=helper_no, caller_no=caller_no, task=task,
                                                                               status='initiated').order_by('-created')[0]

                    call_forward_details.status = "not_answered"
                    call_forward_details.save()
                    call_forward.delete()
                    day_of_week = (datetime.datetime.today().weekday()+1)%7
                    print(day_of_week)
                    avail_direct_helpers = AvailableSlot.objects.filter(
                        start_time__lte=timezone.localtime(timezone.now()).time(),
                        end_time__gte=timezone.localtime(timezone.now()).time(), is_available=True,
                        day_of_week=day_of_week).values('helper').distinct()

                    assigning_list = []
                    for helper in avail_direct_helpers:
                        helper_id = helper.get('helper')
                        assigning_list.append(helper_id)

                    helpers = Helper.objects.all().exclude(login_status=LoginStatus.PENDING)
                    helpers = helpers.filter(id__in=assigning_list, category__name=call.category_option, \
                                             language__language=call.language_option).order_by('last_assigned')
                    if(task.call_attempt < 2 and helpers.count() >= 2):
                        r.addPlayText("The first helper did not pick the call. We are trying another helper.")
                        self.call_helpers(task, helpers[1], r)
                    else:
                        r.addPlayText("Your call has been recorded as task. One of the helpers will contact you shortly.")
                        action = Action.objects.get(task=task)
                        assign = Assign.objects.filter(action=action).exclude(status=AssignStatusOptions.ACCEPTED)
                        assign.delete()
                        assignaction = AssignAction()
                        assignaction.primary_assign(task, NEW_TASK_NOTIF)

                else:
                    helper_no = self.fetch_number(cid)
                    call_forward = Call_Forward.objects.get(helper_no=helper_no)  #helper called and client did not pick
                    if call_forward.type == "survey":
                        caller_no = self.fetch_number(call_forward.caller_no)
                        survey_task = call_forward.survey_task
                        call_forward_details = Call_Forward_Details.objects.filter(helper_no=helper_no, caller_no=caller_no, survey_task=survey_task,
                                                                                   status='initiated').order_by('-created')[0]
                        call_forward_details.status = "not_answered"
                        call_forward_details.save()
                        call_forward.delete()
                    else:
                        caller_no = self.fetch_number(call_forward.caller_no)
                        task = call_forward.task
                        call_forward_details = Call_Forward_Details.objects.filter(helper_no=helper_no, caller_no=caller_no, task=task,
                                                                                   status='initiated').order_by('-created')[0]
                        call_forward_details.status = "not_answered"
                        call_forward_details.save()
                        call_forward.delete()
            except ValueError:
                pass

        # New call starts execution here
        if request.GET.get("event") == "NewCall":
            caller_no = request.GET.get("cid")
            caller_no = self.fetch_number(caller_no)
            helpline_no = request.GET.get("called_number")
            caller_location = request.GET.get("circle")

            day_of_week = (datetime.datetime.today().weekday()+1)%7
            call_forward = Call_Forward.objects.filter(helper_no=caller_no[len(caller_no) - 10:])
            print("New Call:")

            if call_forward :
                if call_forward[0].type == "survey":
                    session_next = Session.CALL_FORWARD
                    helper_no = call_forward[0].helper_no
                    survey_task = call_forward[0].survey_task
                    caller_no = self.fetch_number(call_forward[0].caller_no)
                    # Issue of not able to complete task because of multiple initiated entries in CallForwardDetails
                    call_forward_details = Call_Forward_Details(helper_no=helper_no, caller_no=caller_no, survey_task=survey_task, type="survey")
                    call_forward_details.save()
                    r.addDial(dialnumber=caller_no)
                    print("Inside call forward for survey task:", session_next)


                else:
                    # Checks if call forward table has entry for call forward (means helper is calling)
                    session_next = Session.CALL_FORWARD
                    helper_no = call_forward[0].helper_no
                    task = call_forward[0].task
                    caller_no = self.fetch_number(call_forward[0].caller_no)
                    # Issue of not able to complete task because of multiple initiated entries in CallForwardDetails
                    call_forward_details = Call_Forward_Details(helper_no=helper_no, caller_no=caller_no, task=task, type="regular")
                    call_forward_details.save()
                    r.addDial(dialnumber=caller_no)
                    print("Inside call forward for regular task:", session_next)
            # else this is new call coming from client, redirect to language selection messages (by setting session_
            # next to DISPLAY_LANGUAGE option) and further
            else:
                try:
                    session_next = self.get_next_session(0)
                    caller_no_len = len(caller_no)
                    caller_no = caller_no[caller_no_len - 10:]
                    print("Helpline no retrieved from call: ", helpline_no)
                    if  IVR_Call.objects.filter(sid=sid).count() < 1:
                        call = IVR_Call(sid=sid, caller_no=caller_no, helpline_no=helpline_no, caller_location=caller_location, session_next=session_next)
                        print(">>>>>>>>>>>>>CREATED IVR_CALL OBJECT:  for, caller_no, sid ", caller_no, sid,"<<<<<<<<<<<<<")
                        call.save()
                        print("call saved as :")
                        print(call)
                    else:
                        print("call already exists<<<<<<<<<")
                except:
                    pass

        # First option after new call
        if session_next == Session.DISPLAY_LANGUAGE:
            g = r.append(kookoo.CollectDtmf(maxDigits=1, timeout=5000))
            helpline = HelpLine.objects.get(helpline_number=call.helpline_no)
            audio_cat = Misc_Category.objects.get(category="Language")
            audio_objs = Misc_Audio.objects.filter(helpline=helpline, category=audio_cat).order_by('playorder')
            for audio_obj in audio_objs:
                g.append(kookoo.PlayAudio(url=audio_url + audio_obj.audio.name))
                print("audio:", audio_url + audio_obj.audio.name)
            current = SESSION_LEVELS.index(session_next) + 1
            call.session_next = self.get_next_session(current)
            call.save()

        if request.GET.get("event") == "GotDTMF" and session_next == Session.GET_LANGUAGE:
            if len(request.GET.get("data")) != 0:
                # call.language_option = request.GET.get("data")
                # Below lines added to store language instead of language number
                lang_picked = request.GET.get("data")
                if int(lang_picked) <= len(ALL_LANGUAGES):
                    call.language_option = ALL_LANGUAGES[int(lang_picked) - 1]
                    current = SESSION_LEVELS.index(session_next) + 1
                    call.session_next = self.get_next_session(current)
                    print("1")
                else:
                    current = SESSION_LEVELS.index(session_next) - 1
                    call.session_next = self.get_next_session(current)
                    print("2")

                call.save()
            else:
                current = SESSION_LEVELS.index(session_next) - 1
                call.session_next = self.get_next_session(current)
                r.addHangup()
                call.save()
                print("3")

        if session_next == Session.WELCOME:
            helpline = HelpLine.objects.get(helpline_number=call.helpline_no)
            # Below line commented and new one added for language storage change
            #language = Language.objects.filter(helpline=helpline)[int(call.language_option)-1]
            language = call.language_option
            audio_cat = Misc_Category.objects.get(category="Welcome")
            if len(call.language_option) != 0:
                language = Language.objects.get(helpline=helpline, language=call.language_option)
                print("call object:", call.helpline_no, call.language_option, audio_cat.category)
                audio_obj = Misc_Audio.objects.get(helpline=helpline, category=audio_cat, language=language)
            else:
                audio_obj = Misc_Audio.objects.get(helpline=helpline, category=audio_cat)
            
            r.addPlayAudio(url=audio_url + audio_obj.audio.name)
            #r.addPlayText("Welcome to CSE at I I T B Helpline. If you are not a CSE student at I I T Bombay, please disconnect now.")
            current = SESSION_LEVELS.index(session_next) + 1
            call.session_next = self.get_next_session(current)
            call.save()

        if session_next == Session.INTRO1:
            call.language_option = 'Hindi'
            helpline = HelpLine.objects.get(helpline_number=call.helpline_no)
            audio_cat = Misc_Category.objects.get(category="Welcome")
            g = r.append(kookoo.CollectDtmf(maxDigits=1, timeout=5000))
            #if len(call.language_option) != 0:
            #    language = Language.objects.get(helpline=helpline, language=call.language_option)
            #    print("call object:", call.helpline_no, call.language_option, audio_cat.category)
            #    audio_obj = Misc_Audio.objects.get(helpline=helpline, category=audio_cat, language=language)
            #else:
            audio_obj = Misc_Audio.objects.get(helpline=helpline, category=audio_cat)
            g.append(kookoo.PlayAudio(url=audio_url + audio_obj.audio.name))
            #r.addPlayAudio(url=audio_url + audio_obj.audio.name)
            current = SESSION_LEVELS.index(session_next) + 1
            call.session_next = self.get_next_session(current)
            call.save()

        if request.GET.get("event") == "GotDTMF" and session_next == Session.GET_INTRO1_INP:
            if len(request.GET.get("data")) != 0:
                intro1_inp = request.GET.get("data")
                if int(intro1_inp) == 1:
                    current = SESSION_LEVELS.index(session_next) + 1
                    call.session_next = self.get_next_session(current)
                elif int(intro1_inp) == 2:
                    current = SESSION_LEVELS.index(session_next) + 7
                    call.session_next = self.get_next_session(current)
                    call.category_option = CATEGORIES[4]
                else:
                    current = SESSION_LEVELS.index(session_next) - 1
                    call.session_next = self.get_next_session(current)
                call.save()
            else:
                current = SESSION_LEVELS.index(session_next) - 1
                call.session_next = self.get_next_session(current)
                call.save()

        if session_next == Session.INTRO2:
            helpline = HelpLine.objects.get(helpline_number=call.helpline_no)
            audio_cat = Misc_Category.objects.get(category="corona")
            g = r.append(kookoo.CollectDtmf(maxDigits=1, timeout=5000))
            #if len(call.language_option) != 0:
            #    language = Language.objects.get(helpline=helpline, language=call.language_option)
            #    print("call object:", call.helpline_no, call.language_option, audio_cat.category)
            #    audio_obj = Misc_Audio.objects.get(helpline=helpline, category=audio_cat, language=language)
            #else:
            audio_obj = Misc_Audio.objects.get(helpline=helpline, category=audio_cat)
            g.append(kookoo.PlayAudio(url=audio_url + audio_obj.audio.name))
            #r.addPlayAudio(url=audio_url + audio_obj.audio.name)
            current = SESSION_LEVELS.index(session_next) + 1
            call.session_next = self.get_next_session(current)
            call.save()

        if request.GET.get("event") == "GotDTMF" and session_next == Session.GET_INTRO2_INP:
            if len(request.GET.get("data")) != 0:
                intro1_inp = request.GET.get("data")
                if int(intro1_inp) == 1:
                    current = SESSION_LEVELS.index(session_next) + 1
                    call.session_next = self.get_next_session(current)
                elif int(intro1_inp) == 2:
                    current = SESSION_LEVELS.index(session_next) + 3
                    call.session_next = self.get_next_session(current)
                else:
                    current = SESSION_LEVELS.index(session_next) - 1
                    call.session_next = self.get_next_session(current)
                call.save()
            else:
                current = SESSION_LEVELS.index(session_next) - 1
                call.session_next = self.get_next_session(current)
                call.save()


        if session_next == Session.DISPLAY_OPTION:
            g = r.append(kookoo.CollectDtmf(maxDigits=1,termchar="#",timeout=10000))
            helpline = HelpLine.objects.get(helpline_number=call.helpline_no)
            #language = Language.objects.get(helpline=helpline, language=call.language_option)
            #audio_objs = IVR_Audio.objects.filter(helpline=helpline, language=language).order_by('playorder')
            #for audio_obj in audio_objs:
            #    g.append(kookoo.PlayAudio(url=audio_url + audio_obj.audio.name))
            #    print("audio:", audio_url + audio_obj.audio.name)            
            #g.append(kookoo.PlayText("Welcome to CSE at I I T B Helpline. If you are not a CSE student at I I T Bombay, please disconnect now. Press 1 to contact a CSE course instructor or T A . Press 2 to contact a DAMP or A R P mentor or advisor. "
            #"Press 3 to contact your faculty advisor. Press 4 if you are facing problems participating effectively in online classes and need help. "
            #"Press 5 if you have any other issue related to online classes that you wish to seek help on."))
            audio_cat = Misc_Category.objects.get(category="oxygen")
            audio_obj = Misc_Audio.objects.get(helpline=helpline, category=audio_cat)
            g.append(kookoo.PlayAudio(url=audio_url + audio_obj.audio.name))
            current = SESSION_LEVELS.index(session_next) + 1
            call.session_next = self.get_next_session(current)
            call.save()

        if request.GET.get("event") == "GotDTMF" and session_next == Session.GET_OPTION:
            if len(request.GET.get("data")) != 0:
                call.category_option = request.GET.get("data")
                category_picked = request.GET.get("data")

                if int(category_picked) <= len(CATEGORIES):
                    call.category_option = CATEGORIES[int(category_picked) - 1]

                print(call.category_option)
                helpline = HelpLine.objects.get(helpline_number=call.helpline_no)
                #language = Language.objects.get(helpline=helpline, language=call.language_option)
                #tot_opts = str(len(IVR_Audio.objects.filter(helpline=helpline, language=language)))                
                if 1 <= int(category_picked) <= 2:
                    current = SESSION_LEVELS.index(session_next) + 5
                    call.session_next = self.get_next_session(current)
                    call.save()
                else:
                    current = SESSION_LEVELS.index(session_next) - 1
                    call.session_next = self.get_next_session(current)
                    call.save()

            else:
                current = SESSION_LEVELS.index(session_next) - 1
                call.session_next = self.get_next_session(current)
                call.save()



        if session_next == Session.DISPLAY_OPTION_2:
            g = r.append(kookoo.CollectDtmf(maxDigits=1,termchar="#",timeout=10000))
            helpline = HelpLine.objects.get(helpline_number=call.helpline_no)
            #language = Language.objects.get(helpline=helpline, language=call.language_option)
            #audio_objs = IVR_Audio.objects.filter(helpline=helpline, language=language).order_by('playorder')
            #for audio_obj in audio_objs:
            #    g.append(kookoo.PlayAudio(url=audio_url + audio_obj.audio.name))
            #    print("audio:", audio_url + audio_obj.audio.name)            
            #g.append(kookoo.PlayText("Welcome to CSE at I I T B Helpline. If you are not a CSE student at I I T Bombay, please disconnect now. Press 1 to contact a CSE course instructor or T A . Press 2 to contact a DAMP or A R P mentor or advisor. "
            #"Press 3 to contact your faculty advisor. Press 4 if you are facing problems participating effectively in online classes and need help. "
            #"Press 5 if you have any other issue related to online classes that you wish to seek help on."))
            audio_cat = Misc_Category.objects.get(category="oxygen")
            audio_obj = Misc_Audio.objects.get(helpline=helpline, category=audio_cat)
            g.append(kookoo.PlayAudio(url=audio_url + audio_obj.audio.name))
            current = SESSION_LEVELS.index(session_next) + 1
            call.session_next = self.get_next_session(current)
            call.save()

        if request.GET.get("event") == "GotDTMF" and session_next == Session.GET_OPTION_2:
            if len(request.GET.get("data")) != 0:
                call.category_option = request.GET.get("data")
                category_picked = request.GET.get("data")

                if int(category_picked) <= len(CATEGORIES):
                    call.category_option = CATEGORIES[int(category_picked) + 1]

                print(call.category_option)
                helpline = HelpLine.objects.get(helpline_number=call.helpline_no)
                #language = Language.objects.get(helpline=helpline, language=call.language_option)
                #tot_opts = str(len(IVR_Audio.objects.filter(helpline=helpline, language=language)))                
                if 1 <= int(category_picked) <= 2:
                    current = SESSION_LEVELS.index(session_next) + 3
                    call.session_next = self.get_next_session(current)
                    call.save()
                else:
                    current = SESSION_LEVELS.index(session_next) - 1
                    call.session_next = self.get_next_session(current)
                    call.save()

            else:
                current = SESSION_LEVELS.index(session_next) - 1
                call.session_next = self.get_next_session(current)
                call.save()

        if session_next == Session.DISPLAY_SUB_OPTION:
            g = r.append(kookoo.CollectDtmf(maxDigits=1,termchar="#",timeout=10000))
            helpline = HelpLine.objects.get(helpline_number=call.helpline_no)
            #language = Language.objects.get(helpline=helpline, language=call.language_option)
            #audio_objs = IVR_Audio.objects.filter(helpline=helpline, language=language).order_by('playorder')
            #for audio_obj in audio_objs:
            #    g.append(kookoo.PlayAudio(url=audio_url + audio_obj.audio.name))
            #    print("audio:", audio_url + audio_obj.audio.name)            
            #g.append(kookoo.PlayText("Welcome to CSE at I I T B Helpline. If you are not a CSE student at I I T Bombay, please disconnect now. Press 1 to contact a CSE course instructor or T A . Press 2 to contact a DAMP or A R P mentor or advisor. "
            #"Press 3 to contact your faculty advisor. Press 4 if you are facing problems participating effectively in online classes and need help. "
            #"Press 5 if you have any other issue related to online classes that you wish to seek help on."))
            audio_cat = Misc_Category.objects.get(category="oxygen")
            audio_obj = Misc_Audio.objects.get(helpline=helpline, category=audio_cat)
            g.append(kookoo.PlayAudio(url=audio_url + audio_obj.audio.name))
            current = SESSION_LEVELS.index(session_next) + 1
            call.session_next = self.get_next_session(current)
            call.save()

        if request.GET.get("event") == "GotDTMF" and session_next == Session.GET_SUB_OPTION:
            if len(request.GET.get("data")) != 0:
                call.category_option = request.GET.get("data")
                category_picked = request.GET.get("data")

                if int(category_picked) <= len(CATEGORIES):
                    call.category_option = CATEGORIES[int(category_picked) + 3]

                print(call.category_option)
                helpline = HelpLine.objects.get(helpline_number=call.helpline_no)
                #language = Language.objects.get(helpline=helpline, language=call.language_option)
                #tot_opts = str(len(IVR_Audio.objects.filter(helpline=helpline, language=language)))                
                if 1 <= int(category_picked) <= 2:
                    current = SESSION_LEVELS.index(session_next) + 1
                    call.session_next = self.get_next_session(current)
                    call.save()
                else:
                    current = SESSION_LEVELS.index(session_next) - 1
                    call.session_next = self.get_next_session(current)
                    call.save()

            else:
                current = SESSION_LEVELS.index(session_next) - 1
                call.session_next = self.get_next_session(current)
                call.save()



        '''if session_next == Session.DISPLAY_SUB_OPTION:
            g = r.append(kookoo.CollectDtmf(maxDigits=1, timeout=5000))
            helpline = HelpLine.objects.get(helpline_number=call.helpline_no)
            # Below line commented and new line added for language change
            # language = Language.objects.filter(helpline=helpline)[int(call.language_option) - 1]
            language = Language.objects.get(helpline=helpline, language=call.language_option)
            #category = HelperCategory.objects.get(name=call.category_option)
            #audio_objs = IVR_Audio.objects.filter(helpline=helpline, language=language, category=category,
            #                                      level=2).order_by('playorder')
            #for audio_obj in audio_objs:
            #    g.append(kookoo.PlayAudio(url=audio_url + audio_obj.audio.name))
            if int(call.category_option[0]) == 1:
                audio_cat = Misc_Category.objects.get(category="sub_cat_course")
                audio_objs = Misc_Audio.objects.filter(helpline=helpline, category=audio_cat).order_by('playorder')
                for audio_obj in audio_objs:
                    g.append(kookoo.PlayAudio(url=audio_url + audio_obj.audio.name))
                    print("audio:", audio_url + audio_obj.audio.name)

                #g.append(kookoo.PlayText("Most course related problems can be solved by T As. Press 1 to contact a T A. Press 2 to contact the instructor. or press 0 to go back to main menu"))
            if int(call.category_option[0]) == 3:
                audio_cat = Misc_Category.objects.get(category="sub_cat_facad")
                audio_objs = Misc_Audio.objects.filter(helpline=helpline, category=audio_cat).order_by('playorder')
                for audio_obj in audio_objs:
                    g.append(kookoo.PlayAudio(url=audio_url + audio_obj.audio.name))
                    print("audio:", audio_url + audio_obj.audio.name)
                #g.append(kookoo.PlayText("Press 1 if you are a BTech student, press 2 if you are an MTech student, press 3 if you are a PhD student, press 4 otherwise or press 0 to go back to main menu"))
            current = SESSION_LEVELS.index(session_next) + 1
            call.session_next = self.get_next_session(current)
            call.save()

        if request.GET.get("event") == "GotDTMF" and session_next == Session.GET_SUB_OPTION:

            helpline = HelpLine.objects.get(helpline_number=call.helpline_no)
            language = Language.objects.get(helpline=helpline, language=call.language_option)
            #category = HelperCategory.objects.get(name=call.category_option)

            #audio_objs = IVR_Audio.objects.filter(helpline=helpline, language=language, category=category,
            #                                      level=2).order_by('playorder')

            #if len(request.GET.get("data")) != 0 or len(audio_objs) == 0:
            if len(request.GET.get("data")) != 0:
                #call.category_sub_option = request.GET.get("data")

                #sel_category = CATEGORIES.index(call.category_option)
                sel_category = CATEGORIES.index(call.category_option)
                subcat_picked = request.GET.get("data")
                #if len(audio_objs) == 0:
                #    call.category_sub_option = sel_category
                #else:
                #    call.category_sub_option = SUBCATEGORIES[sel_category][int(subcat_picked) - 1]
                #call.category_sub_option = SUBCATEGORIES[sel_category][int(subcat_picked) - 1]
                if int(call.category_option[0]) == 1:
                    if int(subcat_picked) == 1 or int(subcat_picked) == 2:
                        call.category_sub_option = int(subcat_picked)
                        current = SESSION_LEVELS.index(session_next) + 1
                        call.session_next = self.get_next_session(current)
                        call.save()
                    elif int(subcat_picked) == 0:
                        current = SESSION_LEVELS.index(session_next) - 5
                        call.session_next = self.get_next_session(current)
                        call.save()

                    else:
                        r.addPlayText("Invalid input")
                        current = SESSION_LEVELS.index(session_next) - 1
                        call.session_next = self.get_next_session(current)
                        call.save()

                elif int(call.category_option[0]) == 3:
                    if int(subcat_picked) == 1 or int(subcat_picked) == 2 or int(subcat_picked) == 3 or int(subcat_picked) == 4:
                        call.category_option=call.category_option+'-'+str(subcat_picked)
                        current = SESSION_LEVELS.index(session_next) + 1
                        call.session_next = self.get_next_session(current)
                        call.save()
                    elif int(subcat_picked) == 0:
                        current = SESSION_LEVELS.index(session_next) - 5
                        call.session_next = self.get_next_session(current)
                        call.save()

                    else:
                        r.addPlayText("Invalid input")
                        current = SESSION_LEVELS.index(session_next) - 1
                        call.session_next = self.get_next_session(current)
                        call.save()
                    
                print(call.category_sub_option)
                

            else:
                current = SESSION_LEVELS.index(session_next) - 1
                call.session_next = self.get_next_session(current)
                call.save()'''

        '''if session_next == Session.DISPLAY_TERMS:
            g = r.append(kookoo.CollectDtmf(maxDigits=1, timeout=5000))
            helpline = HelpLine.objects.get(helpline_number=call.helpline_no)
            # language = Language.objects.filter(helpline=helpline)[int(call.language_option) - 1]
            language = Language.objects.get(helpline=helpline, language=call.language_option)
            audio_cat = Misc_Category.objects.get(category="Terms")
            audio_obj = Misc_Audio.objects.get(helpline=helpline, category=audio_cat, language=language)
            g.append(kookoo.PlayAudio(url=audio_url + audio_obj.audio.name))
            current = SESSION_LEVELS.index(session_next) + 1
            call.session_next = self.get_next_session(current)
            call.save()

        if request.GET.get("event") == "GotDTMF" and session_next == Session.GET_TERMS:
            if len(request.GET.get("data")) != 0:
                terms_option = request.GET.get("data")
                if terms_option == '1':
                    # Check if direct helpers are available....for the category.
                    day_of_week = (datetime.datetime.today().weekday() + 1) % 7
                    avail_direct_helpers = AvailableSlot.objects.filter(
                        start_time__lte=timezone.localtime(timezone.now()).time(),
                        end_time__gte=timezone.localtime(timezone.now()).time(), is_available=True,
                        day_of_week=day_of_week).values('helper').distinct()

                    assigning_list = []
                    for helper in avail_direct_helpers:
                        helper_id = helper.get('helper')
                        assigning_list.append(helper_id)

                    helpers = Helper.objects.all().exclude(login_status=LoginStatus.PENDING)
                    helpers = helpers.filter(id__in=assigning_list, category__name=call.category_option, \
                                             language__language=call.language_option).order_by('last_assigned')
                    if helpers:
                        print('In direct new call')
                        session_next = Session.CALL_FORWARD
                        call.session_next = Session.CALL_FORWARD
                        call.save()
                        data = {
                            "client_number": call.caller_no,
                            "helpline_number": call.helpline_no,
                            "location": call.caller_location,
                            "category": call.category_option,
                            "language": call.language_option,
                            "sub_category": call.category_sub_option,
                            "task_type": "Direct"
                        }
                        print('Task is being created with :', data)
                        register_call = RegisterCall()
                        task_id = register_call.register_call(data)
                        self.call_helpers(task_id, helpers[0], r)
                    else:
                        current = SESSION_LEVELS.index(session_next) + 1
                        call.session_next = self.get_next_session(current)
                        call.save()
                        data = {
                            "client_number": call.caller_no,
                            "helpline_number": call.helpline_no,
                            "location": call.caller_location,
                            "category": call.category_option,
                            "language": call.language_option,
                            "sub_category": call.category_sub_option,
                            "task_type": "Indirect"
                        }
                        print('Task is being created with :', data)
                        self.post_data("registercall/", data)
                elif terms_option == '2':
                    r.addHangup()
                else:
                    current = SESSION_LEVELS.index(session_next) - 1
                    call.session_next = self.get_next_session(current)
                    call.save()

            else:
                current = SESSION_LEVELS.index(session_next) - 1
                call.session_next = self.get_next_session(current)
                call.save()'''

        if session_next == Session.CALL_EXIT:
            if session_next == Session.CALL_EXIT and not DISPLAY_TERMS_IN_IVR:
                # Check if direct helpers are available....for the category.
                day_of_week = (datetime.datetime.today().weekday() + 1) % 7
                avail_direct_helpers = AvailableSlot.objects.filter(
                    start_time__lte=timezone.localtime(timezone.now()).time(),
                    end_time__gte=timezone.localtime(timezone.now()).time(), is_available=True,
                    day_of_week=day_of_week).values('helper').distinct()

                assigning_list = []
                for helper in avail_direct_helpers:
                    helper_id = helper.get('helper')
                    assigning_list.append(helper_id)

                helpers = Helper.objects.all().exclude(login_status=LoginStatus.PENDING)
                helpers = helpers.filter(id__in=assigning_list, category__name=call.category_option, \
                                         language__language=call.language_option).order_by('last_assigned')
                if helpers:
                    print('In direct new call')
                    session_next = Session.CALL_FORWARD
                    call.session_next = Session.CALL_FORWARD
                    call.save()
                    data = {
                        "client_number": call.caller_no,
                        "helpline_number": call.helpline_no,
                        "location": call.caller_location,
                        "category": call.category_option,
                        "language": call.language_option,
                        "sub_category": call.category_sub_option,
                        "task_type": "Direct"
                    }
                    print('Task is being created with :', data)
                    register_call = RegisterCall()
                    task_id = register_call.register_call(data)
                    self.call_helpers(task_id, helpers[0], r)
                else:
                    data = {
                        "client_number": call.caller_no,
                        "helpline_number": call.helpline_no,
                        "location": call.caller_location,
                        "category": call.category_option,
                        "language": call.language_option,
                        "sub_category": call.category_sub_option,
                        "task_type": "Indirect"
                    }
                    print('Task is being created with :', data)
                    self.post_data("registercall/", data)
                    current = SESSION_LEVELS.index(session_next) + 1
                    call.session_next = self.get_next_session(current)
                    call.save()
            helpline = HelpLine.objects.get(helpline_number=call.helpline_no)
            language = Language.objects.get(helpline=helpline, language=call.language_option)
            audio_cat = Misc_Category.objects.get(category="Exit")
            audio_obj = Misc_Audio.objects.get(helpline=helpline, category=audio_cat, language=language)
            r.addPlayAudio(url=audio_url + audio_obj.audio.name)
            r.addHangup()

        return HttpResponse(r)

    def get_next_session(self, current):
        next_session = SESSION_LEVELS[current]
        return next_session

    def fetch_number(self, url_number):
        contact = url_number.strip()
        if len(contact) > 10:
            contact = contact[len(contact) - 10:]

        try:
            contact_num = int(contact)

        except ValueError:
            print('Number is invalid !!')

        return str(contact_num)


class FeedbackView(View):
    def get(self, request):
        audio_url = AUDIO_URL

        try:
            number_of_questions = len(FeedbackType.objects.all())
            caller_no = request.GET.get("cid")
            caller_no = self.fetch_number(caller_no)
            feedback_obj = Feedback.objects.filter(task__call_request__client__client_number=caller_no).filter(
                isFeedbackTaken=False).order_by('-id')[0]

        except ValueError:
            print('No feedback found !!')

        r = kookoo.Response()

        if request.GET.get("event") == "NewCall":
            r.addPlayText("Good Morning, Dear User we would like to take your feedback on your experience with "
                          "career counselling. ")

        if request.GET.get("event") != "GotDTMF" and request.GET.get("event") != "Disconnect":
            g = r.append(kookoo.CollectDtmf(maxDigits=1, timeout=5000))
            feedback_type = FeedbackType.objects.get(id=feedback_obj.current_question + 1)
            # r.addPlayText(feedback_type.question)
            # g.append(kookoo.PlayAudio(url=audio_url + audio_obj.audio.name))
            g.append(kookoo.PlayText(feedback_type.question))

        if request.GET.get("event") == "GotDTMF":

            if len(request.GET.get("data")) != 0:
                new_feedback_type = FeedbackType.objects.get(id=feedback_obj.current_question + 1)
                feedback_resp = FeedbackResponse(feedbackType=new_feedback_type, response=int(request.GET.get("data")))
                feedback_resp.save()
                feedback_obj.feedbackresponses.add(feedback_resp)
                feedback_obj.current_question += 1
                feedback_obj.save()

                if feedback_obj.current_question >= len(FeedbackType.objects.all()):
                    feedback_obj.isFeedbackTaken = True
                    feedback_obj.save()
                    r.addPlayText("Thank you for your feedback, Have a nice day ")
                    r.addHangup()

        return HttpResponse(r)


"""
        if session_next == Session.DISPLAY_OPTION_2:
            print("Display option 2")
            helpline = HelpLine.objects.get(helpline_number=call.helpline_no)
            if int(call.category_option) == 1:
                g = r.append(kookoo.CollectDtmf(maxDigits=3,termchar="#",timeout=5000))
                audio_cat = Misc_Category.objects.get(category="course")
                audio_objs = Misc_Audio.objects.filter(helpline=helpline, category=audio_cat).order_by('playorder')
                for audio_obj in audio_objs:
                    g.append(kookoo.PlayAudio(url=audio_url + audio_obj.audio.name))
                    print("audio:", audio_url + audio_obj.audio.name)
                #g.append(kookoo.PlayText("Please enter only numeric part of course number.  For example, for CS228M, enter two two eight or press 0 to go back to main menu"))
            elif int(call.category_option) == 2:
                g = r.append(kookoo.CollectDtmf(maxDigits=1,termchar="#",timeout=5000))
                audio_cat = Misc_Category.objects.get(category="damp")
                audio_objs = Misc_Audio.objects.filter(helpline=helpline, category=audio_cat).order_by('playorder')
                for audio_obj in audio_objs:
                    g.append(kookoo.PlayAudio(url=audio_url + audio_obj.audio.name))
                    print("audio:", audio_url + audio_obj.audio.name)
                #g.append(kookoo.PlayText("Press 1 to contact a DAMP mentor,  press 2 to contact DAMP faculty advisor, press 3 to contact A R P faculty advisor or press 0 to go back to main menu"))
            elif int(call.category_option) == 3:
                g = r.append(kookoo.CollectDtmf(maxDigits=4,termchar="#",timeout=8000))
                audio_cat = Misc_Category.objects.get(category="facad")
                audio_objs = Misc_Audio.objects.filter(helpline=helpline, category=audio_cat).order_by('playorder')
                for audio_obj in audio_objs:
                    g.append(kookoo.PlayAudio(url=audio_url + audio_obj.audio.name))
                    print("audio:", audio_url + audio_obj.audio.name)
                #g.append(kookoo.PlayText("Please enter the year you joined I I T Bombay.  For example, for 2017, enter two zero one seven or press 0 to go back to main menu"))
            elif int(call.category_option) == 4:
                g = r.append(kookoo.CollectDtmf(maxDigits=1,termchar="#",timeout=5000))
                audio_cat = Misc_Category.objects.get(category="online_problems")
                audio_objs = Misc_Audio.objects.filter(helpline=helpline, category=audio_cat).order_by('playorder')
                for audio_obj in audio_objs:
                    g.append(kookoo.PlayAudio(url=audio_url + audio_obj.audio.name))
                    print("audio:", audio_url + audio_obj.audio.name)
                #g.append(kookoo.PlayText("Press 1 if you have serious laptop, internet or power problem that you are unable to resolve."
                #"Press 2 if you have serious problems with space or time available for studying."
                #"Press 3 if you are facing both resource and space/time problems, or are facing other problems or press 0 to go back to main menu"))
            elif int(call.category_option) == 5:
                g = r.append(kookoo.CollectDtmf(maxDigits=1,termchar="#",timeout=5000))
                audio_cat = Misc_Category.objects.get(category="cse_task_force")
                audio_objs = Misc_Audio.objects.filter(helpline=helpline, category=audio_cat).order_by('playorder')
                for audio_obj in audio_objs:
                    g.append(kookoo.PlayAudio(url=audio_url + audio_obj.audio.name))
                    print("audio:", audio_url + audio_obj.audio.name)
                #g.append(kookoo.PlayText("Press 1 if the issue you wish to discuss is sensitive and you would like only a woman student/faculty member to contact you. "
                #"Press 2 if you are comfortable discussing with any CSE Task Force member or press 0 to go back to main menu"))            
            current = SESSION_LEVELS.index(session_next) + 1
            call.session_next = self.get_next_session(current)
            call.save()



        if request.GET.get("event") == "GotDTMF" and session_next == Session.GET_OPTION_2:
            if len(request.GET.get("data")) != 0:
                #call.category_option = request.GET.get("data")
                category_picked = request.GET.get("data")

                #if int(category_picked) <= len(CATEGORIES):
                
                call.category_option = str(call.category_option)+'-'+str(category_picked)
                print(call.category_option)
                helpline = HelpLine.objects.get(helpline_number=call.helpline_no)
                language = Language.objects.get(helpline=helpline, language=call.language_option)
                #tot_opts = str(len(IVR_Audio.objects.filter(helpline=helpline, language=language)))
                
                
                if call.category_option in CATEGORIES:

                    if int(call.category_option[0]) == 2 or int(call.category_option[0]) == 4 or int(call.category_option[0]) == 5:
                        current = SESSION_LEVELS.index(session_next) + 3
                        call.session_next = self.get_next_session(current)
                        call.save()

                    else:
                        current = SESSION_LEVELS.index(session_next) + 1
                        call.session_next = self.get_next_session(current)
                        call.save()

                elif int(category_picked) == 0:
                    current = SESSION_LEVELS.index(session_next) - 3
                    call.session_next = self.get_next_session(current)
                    call.save()

                else:
                    r.addPlayText("Invalid input")
                    call.category_option = call.category_option[0]
                    current = SESSION_LEVELS.index(session_next) - 1
                    call.session_next = self.get_next_session(current)
                    call.save()

            else:
                call.category_option = call.category_option[0]
                current = SESSION_LEVELS.index(session_next) - 1
                call.session_next = self.get_next_session(current)
                call.save()
"""



