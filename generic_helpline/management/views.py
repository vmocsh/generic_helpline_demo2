
import json
from datetime import *
from urllib.request import urlopen

from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.generic import View
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import CharField
from django.db.models.functions import Cast
from constants import *
from ivr.models import Call_Forward, Call_Forward_Details, Language
from register_client.models import Client
from register_helper.models import Helper
from register_helper.options import LoginStatus, HelperLevel, HelperType
from registercall.models import Task, FollowUpTask, CallRequest
from registercall.options import TaskStatusOptions
from surveys.models import Survey, SurveyTask, SurveyResponse, FollowUpSurveyTask
from surveys.options import *
from task_manager.helpers import HelperMethods
from task_manager.models import Action, Assign, QandA, Feedback, TaskHistory
from task_manager.options import AssignStatusOptions, ActionStatusOptions, ActionTypeOptions
from .models import HelpLine, HelperCategory, CategorySubcategory, AvailableSlot, DoctorAvailableSlot, DoctorBookedSlot, GroupConcat, Tag_List
from .serializers import HelperCategorySerializer, HelplineSerializer, LanguageSerializer
from bs4 import BeautifulSoup
from collections import OrderedDict
import requests
import os
import csv

# Create your views here.


class Helplines(APIView):
    def post(self):
        helplines = HelpLine.objects.all()
        helplines = HelplineSerializer(helplines, many=True)
        return Response({"helplines": helplines.data}, status=200)


class HelplineNumber(APIView):
    def get(self, request):
        username = request.GET.get("username")
        user = get_object_or_404(User, username=username)
        helper = get_object_or_404(Helper, user=user)
        if TOLLFREE:
            helpline_number = helper.helpline.helpline_tollfree_number
        else:
            helpline_number = helper.helpline.helpline_number
        if CLICK_TO_CONNECT:
            contactnumber = helper.helper_number
            appurl = BASE_URL + "ivr/"
            url = "http://www.kookoo.in/outbound/outbound.php?phone_no="+contactnumber+"&api_key="+API_KEY + \
                  "%20&outbound_version=2&url="+appurl
            urlopen(url)

        return Response({"helpline_number": helpline_number[2:]}, status=200)


class SendSms(APIView):
    def post(self, request):
        print('In send sms')
        username = request.data.get("username")
        task_id = request.data.get("taskId")
        caller_number = request.data.get("callerNumber")
        message = ''
        for word in request.data.get("message").split(' '):
            message = message + word + "%20"
        user = get_object_or_404(User, username=username)
        user_name = SMS_USER
        password = SMS_PWD
        sender_id = SMS_SENDERID
        msg_url = 'http://smscloud.ozonetel.com/GatewayAPI/rest?send_to='+caller_number+'&msg='+message + \
                  '&msg_type=text&loginid='+user_name+'&auth_scheme=plain&password='+password+'&v=1.1&format=text' \
                  '&method=sendMessage&mask='+sender_id
        urlopen(msg_url)
        message = request.data.get("message")
        task = Task.objects.get(id=task_id)
        q_and_a = QandA.objects.filter(task=task)
        if q_and_a:
            old_message = QandA.objects.get(task=task).message
            QandA.objects.filter(task=task).update(message=old_message + ";\n " + message)
        else:
            q_and_a = QandA(task=task, message=message)
            q_and_a.save()
        return Response({"notification": "success"}, status=200)


class TagUpdate(APIView):
    def post(self, request):
        print('In tag update')
        username = request.data.get("username")
        task_id = request.data.get("taskId")
        tag_string = ""
        user = get_object_or_404(User, username=username)
        tag_string = request.data.get("tag_string")
        print(task_id)
        if task_id.find("(") != -1:
            index=task_id.index("(")
            task_id=task_id[0: index]
        print(task_id)
        task = Task.objects.get(id=task_id)
        task.tag_string = tag_string
        task.save()
        return Response({"notification": "success"}, status=200)

class SurveyTagUpdate(APIView):
    def post(self, request):
        print('In tag update')
        username = request.data.get("username")
        task_id = request.data.get("taskId")
        tag_string = ""
        user = get_object_or_404(User, username=username)
        tag_string = request.data.get("tag_string")
        if task_id.find("(") != -1:
            index=task_id.index("(")
            task_id=task_id[0: index]
        print(task_id)
        print(tag_string)
        survey_task = SurveyTask.objects.get(id=task_id)
        survey_task.tag_string = tag_string
        survey_task.save()
        return Response({"notification": "success"}, status=200)

class NameUpdate(APIView):
    def post(self, request):
        print('In name update')
        username = request.data.get("username")
        print(username)
        task_id = request.data.get("taskId")
        tag_string = ""
        #user = get_object_or_404(User, username=username)
        tag_string = request.data.get("tag_string")
        if task_id.find("(") != -1:
            index=task_id.index("(")
            task_id=task_id[0: index]
        print(task_id)
        task = Task.objects.get(id=task_id)
        client = Client.objects.get(client_number=task.call_request.client.client_number)
        print(client.name)
        client.name = username
        print(client.name)
        client.save()
        print(client.name)
        return Response({"notification": "success"}, status=200)

# Adding function for getting helper categories and subcategories

class getHelperCategoryandSubcategory(APIView):
    def post(self, request):

        username = request.data.get("username")
        lang = request.data.get("language")
        if lang == "en" or lang is None or lang == "":
            lang = "english"
        elif lang == "hi":
            lang = "hindi"
        elif lang == "gj":
            lang = "gujarati"
        elif lang == "mr":
            lang = "marathi"
        elif lang == 'ta':
            lang = "tamil"
        user = get_object_or_404(User, username=username)
        helper = get_object_or_404(Helper, user=user)
        helpline = helper.helpline
        helpline_categories = CategorySubcategory.objects.filter(helpline=helpline, language=lang).exclude(category='Repeat')
        distinct_categories = CategorySubcategory.objects.filter(helpline=helpline, language=lang).exclude(category='Repeat').values('category').distinct()
        subcategories_list = []
        categories_list = []
        for category in helpline_categories:
            main_category = category.category
            sub_category = category.subcategory
            data = {"main_category": main_category, "sub_category": sub_category, "language": lang}
            subcategories_list.append(data)

        for category in distinct_categories:
            categories_list.append(category)
            
        return JsonResponse({"subcategory": subcategories_list, "category": categories_list}, status=200)

# End of changes

# New function added by Smartika to fetch all helpers of that helpline for task reallocation


class AllHelpers(APIView):
    def get(self, request):
        username = request.GET.get("username")
        print (username)
        user = get_object_or_404(User, username=username)
        helper = get_object_or_404(Helper, user=user)
        helpline = helper.helpline
        # print (helpline)
        helpers = Helper.objects.filter(helpline=helpline)
        # print(helpers)
        helper_list = []
        categories_list = []
        for helper in helpers:
            first_name = helper.user.first_name
            helper_name = helper.user.username
            category = HelperCategorySerializer(helper.category.all(), many=True)
            helper_list.append({"username": helper_name, "firstname": first_name,"category": category.data})

        distinct_categories = CategorySubcategory.objects.filter(helpline=helpline).exclude(category='Repeat').values('category','language').distinct()
        print("Distinct_categories:  ", distinct_categories, "----")
        for i in range(0, len(distinct_categories)):
            # print(distinct_categories[i])
            categories_list.append({"category": distinct_categories[i]['category'],
                                    "lang": distinct_categories[i]['language']})

        print("helper_list",helper_list)
        print("categories_list",categories_list)
        return Response({"helpers": helper_list, "categories": categories_list}, status=200)

# New function end

# New function to fetch all languages

class TagFields(APIView):
    def get(self, request):
        return Response({"TAG_LIST_1": list(Tag_List.objects.values_list('tag', flat=True)), "TAG_LIST_2": TAG_LIST_2}, status=200)

class Languages(APIView):
    def get(self, request):
        username = request.GET.get("username")
        user = get_object_or_404(User, username=username)
        helper = get_object_or_404(Helper, user=user)
        helpline = helper.helpline
        languages = Language.objects.filter(helpline=helpline)
        lang_list = []
        for lang in languages:
            lang_list.append({"name": lang.language})

        print("Lang_list: ", lang_list)

        return Response({"languages": lang_list}, status=200)
# End new function

# New function to fetch all clients


class AllClients(APIView):
    def get(self, request):
        clients = Client.objects.exclude(name__isnull=True).exclude(name__exact='').order_by('name')
        client_list = []
        for client in clients:
            client_list.append({"name": client.name})

        print("Client List: ", client_list)

        return Response({"clients":client_list}, status=200)

# End new function


class HelplineCategories(APIView):
    def get(self, request):
        username = request.GET.get("username")
        user = get_object_or_404(User, username=username)
        helper = get_object_or_404(Helper, user=user)
        helpline = helper.helpline
        helpline_categories = HelperCategory.objects.filter(helpline=helpline).exclude(name='Repeat')
        helpline_categories = HelperCategorySerializer(helpline_categories, many=True)
        return Response({"categories": helpline_categories.data}, status=200)


class HelperProfile(APIView):
    def get(self, request):
        username = request.GET.get("username")
        user = get_object_or_404(User, username=username)
        helper = get_object_or_404(Helper, user=user)
        helper_cat = HelperCategorySerializer(helper.category.all(), many=True)
        helper_subcategory = helper.subcategory.all()
        helper_subcat = []
        for subcategory in helper_subcategory:
            subcategory = str(subcategory)
            pos = subcategory.index(":")
            subcat = subcategory[pos + 1:]
            helper_subcat.append(subcat)
        lang_cat = LanguageSerializer(helper.language.all(), many=True)
        pending_assigns = len(Assign.objects.filter(helper=helper, status=AssignStatusOptions.PENDING))
        accepted_assigns = len(Assign.objects.filter(helper=helper, status=AssignStatusOptions.ACCEPTED))
        completed_assigns = len(Assign.objects.filter(helper=helper, status=AssignStatusOptions.COMPLETED))
        rejected_assigns = len(Assign.objects.filter(helper=helper, status=AssignStatusOptions.REJECTED))
        timed_out_assigns = len(Assign.objects.filter(helper=helper, status=AssignStatusOptions.TIMEOUT))
        feedback_pending = len(Feedback.objects.filter(helper=helper, status='pending'))
        feedback_completed = len(Feedback.objects.filter(helper=helper, status='completed'))
        data = {
            "username": username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "phone_no": helper.helper_number,
            "gender": helper.gender,
            "college_name": helper.college_name,
            "categories": helper_cat.data,
            "languages": lang_cat.data,
            "pending_assigns": pending_assigns,
            "accepted_assigns": accepted_assigns,
            "completed_assigns": completed_assigns,
            "rejected_assigns": rejected_assigns,
            "timed_out_assigns": timed_out_assigns,
            "feedback_pending": feedback_pending,
            "feedback_completed": feedback_completed,
            "subcategories": helper_subcat

        }
        return Response(data, status=200)

    def post(self, request):
        username = request.data.get("username")
        first_name = request.data.get("first_name")
        last_name = request.data.get("last_name")
        phone_no = request.data.get("phone_no")
        email = request.data.get("email")
        gender = request.data.get("gender")
        college_name = request.data.get("college_name")
        categories = json.loads(request.data.get("categories"))
        #languages = json.loads(request.data.get("languages"))
        #print("languages: ", languages)
        user = get_object_or_404(User, username=username)
        helper = get_object_or_404(Helper, user=user)
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        helper.helper_number = phone_no
        #helper.gender = gender
        #helper.college_name = college_name
        #helpercategories = HelperCategory.objects.all()
        #langcategories = Language.objects.all()
        #for category in helpercategories:
        #    if categories.get(category.name) == "True":
        #        helper.category.add(HelperCategory.objects.get(name=category.name))
        #    else:
        #        helper.category.remove(HelperCategory.objects.get(name=category.name))
        # Added few lines to incorporate language in helper profile
        '''for lang in langcategories:
            if languages.get(lang.language) == "True":
                helper.language.add(Language.objects.get(language=lang.language))
            else:
                helper.language.remove(Language.objects.get(language=lang.language))'''

        helper.save()
        user.save()
        return Response({"notification": "successful"}, status=200)


class setHelperCategoryandLanguage(APIView):
    def post(self, request):
        username = request.data.get("username")
        user = get_object_or_404(User, username=username)
        helper = get_object_or_404(Helper, user=user)
        categories = json.loads(request.data.get("categories"))
        helpercategories = HelperCategory.objects.all()
        for category in helpercategories:
            if categories.get(category.name) == "True":
               helper.category.add(HelperCategory.objects.get(name=category.name))
            else:
                helper.category.remove(HelperCategory.objects.get(name=category.name))

        languages = json.loads(request.data.get("languages"))
        langcategories = Language.objects.all()
        print("languages: ", languages)
        # Added few lines to incorporate language in helper profile
        for lang in langcategories:
            if languages.get(lang.language) == "True":
                helper.language.add(Language.objects.get(language=lang.language))
            else:
                helper.language.remove(Language.objects.get(language=lang.language))

        helper.login_prevstatus = LoginStatus.LOGGED_IN
        helper.save()
        return Response({"notification": "successful"}, status=200)


class HelperTasks(APIView):

    def fetch_assigns(self, assign_list):
        return_list = []
        for assign in assign_list:
            task_id = assign.action.task.id
            tag_string = assign.action.task.tag_string
            if not assign.action.task.tag_string:
                tag_string = ""
            task_status=assign.status;
            client_calls = assign.action.task.client_calls
            if task_status==AssignStatusOptions.ACCEPTED:
                task_status="accepted"
            elif task_status==AssignStatusOptions.REALLOCATED:
                task_status="reallocated"
            elif task_status==AssignStatusOptions.PENDING:
                task_status="pending"
            elif task_status==AssignStatusOptions.FOLLOW_UP_ACCEPTED:
                task_status="followup"
            elif task_status==AssignStatusOptions.COMPLETED:
                task_status="completed"
                try:
                    followup = FollowUpTask.objects.get(task_id=task_id)
                    client_calls = followup.parent_task_id
                except:
                    #print("Exception helper tasks")
                    followup = FollowUpTask.objects.filter(task_id=task_id)
            if assign.action.task.category:
                task_category = assign.action.task.category.name
            else:
                task_category = ""
            caller_name = assign.action.task.call_request.client.name
            caller_number = assign.action.task.call_request.client.client_number
            caller_location = assign.action.task.call_request.client.location
            local_datetime = timezone.localtime(assign.action.task.created)
            local_date = local_datetime.strftime("%d/%m/%Y")
            local_time = local_datetime.strftime("%I:%M %p")
            try:
                task_sub_category = str(assign.action.task.tasksubcategory.all()[:1].get())
                print(str(assign.action.task.tasksubcategory.all()[:1].get()))
            except:
                task_sub_category = ""
            #print(str(assign.action.task.tasksubcategory.all()[:1].get()))

            if len(assign.action.task.language.all()) > 0:
                language = assign.action.task.language.all()[0]
            else:
                language = ""
            data = {"parent_task_id": "", "task_id": task_id, "task_status": task_status, "tag_string": tag_string, "task_category": task_category, "caller_name": caller_name,
                    "caller_location": caller_location,
                    "caller_number": caller_number, "client_calls": client_calls, "date": local_date, "time": local_time, "language": str(language)}
            return_list.append(data)
        return return_list

    def assign_survey_tasks(self, helper):
        assigned_survey_tasks = SurveyTask.objects.filter(helper=helper, status='assigned')
        all_pending_survey_tasks = SurveyTask.objects.filter(status='pending')
        num_to_be_assigned = min(MAX_SURVEY_TASKS_FOR_HELPER-len(assigned_survey_tasks), len(all_pending_survey_tasks))
        new_survey_task_assign_list = []
        for survey_task in all_pending_survey_tasks:
            if len(new_survey_task_assign_list) == num_to_be_assigned:
                break
            survey_task.helper = helper
            survey_task.status = 'assigned'
            survey_task.assignedDateTime = timezone.now()
            survey_task.save()
            new_survey_task_assign_list.append(survey_task.id)

        assigned_survey_tasks = SurveyTask.objects.filter(helper=helper, status='assigned')
        return assigned_survey_tasks

    def get(self, request):
        username = request.GET.get("username")
        user = get_object_or_404(User, username=username)
        helper = get_object_or_404(Helper, user=user)
        pending_assigns = Assign.objects.filter(helper=helper, status=AssignStatusOptions.PENDING).order_by('-created') | Assign.objects.filter(helper=helper, status=AssignStatusOptions.REALLOCATED).order_by('-modified')
        accepted_assigns = Assign.objects.filter(helper=helper, status=AssignStatusOptions.ACCEPTED).order_by('-modified') | Assign.objects.filter(helper=helper, status=AssignStatusOptions.FOLLOW_UP_ACCEPTED).order_by('-created')
        completed_assigns = Assign.objects.filter(helper=helper, status=AssignStatusOptions.COMPLETED).order_by('-modified')
        if len(completed_assigns) > 20:
            completed_assigns = completed_assigns[:20]
        reallocated_assigns = Assign.objects.filter(helper=helper, status=AssignStatusOptions.REALLOCATED).order_by('-modified')
        follow_up_assigns = Assign.objects.filter(helper=helper, status=AssignStatusOptions.FOLLOW_UP_ACCEPTED).order_by('-created')
        pending_list = self.fetch_assigns(pending_assigns)
        accepted_list = self.fetch_assigns(accepted_assigns)
        completed_list = self.fetch_assigns(completed_assigns)
        reallocated_list = self.fetch_assigns(reallocated_assigns)
        follow_up_list = self.fetch_assigns(follow_up_assigns)

        pending_feedback = Feedback.objects.filter(helper=helper, status='pending')
        completed_feedback = Feedback.objects.filter(helper=helper, status='completed')
        assigned_survey_tasks = SurveyTask.objects.filter(helper=helper, status='assigned')
        if len(assigned_survey_tasks)< MAX_SURVEY_TASKS_FOR_HELPER :
            assigned_survey_tasks = self.assign_survey_tasks(helper)

        assigned_survey_task_list = []
        for survey_task in assigned_survey_tasks:
            task_id = survey_task.id
            task_status="survey"
            client_calls = ""
            try:
                followup = FollowUpSurveyTask.objects.get(task_id=task_id)
                client_calls = followup.parent_task_id
            except:
                #print("Exception helper tasks")
                followup = FollowUpSurveyTask.objects.filter(task_id=task_id)
            if not followup:
                task_status="survey"
            else:
                task_status="survey_followup"

            survey_name = survey_task.survey.name
            client_name = survey_task.client.name
            client_number = survey_task.client.client_number
            client_location = survey_task.client.location
            tag_string  =  survey_task.tag_string
            if not survey_task.tag_string:
                tag_string = ""
            if survey_task.edit_form_url:
                form_url = survey_task.edit_form_url
                edit_url_exists = "yes"
            else:
                form_url = survey_task.survey.google_form_url
                edit_url_exists = "no"
            assigned_datetime = timezone.localtime(survey_task.assignedDateTime)
            assigned_date = assigned_datetime.strftime("%d/%m/%Y")
            assigned_time = assigned_datetime.strftime("%I:%M %p")
            assigned_date=assigned_date+", "+assigned_time
            data = {"task_id": task_id, "task_status": task_status, "survey_name": survey_name, "client_name": client_name,
                    "client_location": client_location,
                    "client_number": client_number, "assigned_date": assigned_date, "assigned_time": assigned_time, "form_url": form_url, "edit_url_exists": edit_url_exists}
            assigned_survey_task_list.append(data)
            data = {"parent_task_id": "", "task_id": task_id, "task_status": task_status, "tag_string": tag_string, "task_category": survey_name, "caller_name": client_name,
                    "caller_location": client_location,
                    "caller_number": client_number, "client_calls": client_calls, "date": assigned_date, "time": form_url, "language": edit_url_exists}            
            accepted_list.append(data)

        completed_survey_tasks = SurveyTask.objects.filter(helper=helper, status='completed')

        assigned_survey_task_list = []
        for survey_task in completed_survey_tasks:
            task_id = survey_task.id
            task_status="survey_completed"
            client_calls = ""

            survey_name = survey_task.survey.name
            client_name = survey_task.client.name
            client_number = survey_task.client.client_number
            client_location = survey_task.client.location
            tag_string  =  survey_task.tag_string
            if not survey_task.tag_string:
                tag_string = ""
            if survey_task.edit_form_url:
                form_url = survey_task.edit_form_url
                edit_url_exists = "yes"
            else:
                form_url = survey_task.survey.google_form_url
                edit_url_exists = "no"
            assigned_datetime = timezone.localtime(survey_task.assignedDateTime)
            assigned_date = assigned_datetime.strftime("%d/%m/%Y")
            assigned_time = assigned_datetime.strftime("%I:%M %p")
            assigned_date=assigned_date+", "+assigned_time
            data = {"parent_task_id": "", "task_id": task_id, "task_status": task_status, "tag_string": tag_string, "task_category": survey_name, "caller_name": client_name,
                    "caller_location": client_location,
                    "caller_number": client_number, "client_calls": client_calls, "date": assigned_date, "time": form_url, "language": edit_url_exists}            
            completed_list.append(data)


        fb_pending_list = []
        fb_completed_list = []
        for feedback in pending_feedback:
            task_id = feedback.q_a.task.id
            task_category = feedback.q_a.task.category.name
            question = feedback.q_a.question
            answer = feedback.q_a.answer
            rating = feedback.rating
            data = {'task_id': task_id, 'task_category': task_category, 'question': question, 'answer': answer,
                    'rating': rating}
            fb_pending_list.append(data)
        for feedback in completed_feedback:
            task_id = feedback.q_a.task.id
            task_category = feedback.q_a.task.category.name
            question = feedback.q_a.question
            answer = feedback.q_a.answer
            rating = feedback.rating
            data = {'task_id': task_id, 'task_category': task_category, 'question': question, 'answer': answer,
                    'rating': rating}
            fb_completed_list.append(data)

        return Response({"pending": pending_list, "accepted": accepted_list, "completed": completed_list,
                         "reallocated": reallocated_list, "followup": follow_up_list, "fb_pending": fb_pending_list,
                         "fb_completed": fb_completed_list, "survey_task_list": assigned_survey_task_list}, status=200)


# Post and get for Google Form Edit Url
class FormEditUrl(APIView):
    def post(self, request):
        username = request.data.get("username")
        task_id = request.data.get("task_id")
        edit_url = request.data.get("edit_url")
        auth = request.data.get("Authorization")
        print("TASK ID: POST", task_id, " TYPE ", type(task_id))
        print("EDIT URL: POST", edit_url)
        survey_task = SurveyTask.objects.get(id=task_id)
        user = get_object_or_404(User, username=username)
        helper = get_object_or_404(Helper, user=user)
        survey_task.edit_form_url = edit_url
        survey_task.save()
        return Response({"notification": "successful"}, status=200)

    def get(self, request):
        username = request.GET.get("username")
        task_id = request.GET.get("task_id")
        survey_task = SurveyTask.objects.get(id=task_id)
        user = get_object_or_404(User, username=username)
        helper = get_object_or_404(Helper, user=user)
        if survey_task.edit_form_url:
            form_url = survey_task.edit_form_url
        else:
            form_url = survey_task.survey.google_form_url
        data = {
            "username": username,
            "edit_url": form_url,
        }
        return Response(data, status=200)


class ClientTasks(APIView):
    def get(self, request):
        print("CLIENTTASKS")
        username = request.GET.get("username")
        user = get_object_or_404(User, username=username)
        helper = get_object_or_404(Helper, user=user)
        client_number = request.GET.get("client_number")
        print("Client Number", client_number)
        client = get_object_or_404(Client, client_number=client_number)
        completed_survey_tasks = SurveyTask.objects.filter(client=client, status='completed')
        completed_survey_tasks_list = []
        for survey_task in completed_survey_tasks:
            task_id = survey_task.id
            survey_name = survey_task.survey.name
            client_name = survey_task.client.name
            client_number = survey_task.client.client_number
            client_location = survey_task.client.location
            if survey_task.edit_form_url:
                form_url = survey_task.edit_form_url
            else:
                form_url = survey_task.survey.google_form_url
            assigned_datetime = timezone.localtime(survey_task.assignedDateTime)
            assigned_date = assigned_datetime.strftime("%B %d,%Y")
            assigned_time = assigned_datetime.strftime("%I:%M %p")
            data = {"task_id": task_id, "survey_name": survey_name, "client_name": client_name,
                    "client_location": client_location,
                    "client_number": client_number, "assigned_date": assigned_date, "assigned_time": assigned_time, "form_url": form_url}
            completed_survey_tasks_list.append(data)
        return Response({"survey_task_list": completed_survey_tasks_list}, status=200)


class HelperFeedbackTasks(APIView):
    def get(self, request):
        username = request.GET.get("username")
        user = get_object_or_404(User, username=username)
        helper = get_object_or_404(Helper, user=user)
        pending_feedback = Feedback.objects.filter(helper=helper, status='pending')
        completed_feedback = Feedback.objects.filter(helper=helper, status='completed')
        pending_list = []
        completed_list = []
        for feedback in pending_feedback:
            task_id = feedback.q_a.task.id
            task_category = feedback.q_a.task.category.name
            question = feedback.q_a.question
            answer = feedback.q_a.answer
            rating = feedback.rating
            data = {'task_id': task_id, 'task_category': task_category, 'question': question, 'answer': answer,
                    'rating': rating}
            pending_list.append(data)
        for feedback in completed_feedback:
            task_id = feedback.q_a.task.id
            task_category = feedback.q_a.task.category.name
            question = feedback.q_a.question
            answer = feedback.q_a.answer
            rating = feedback.rating
            data = {'task_id': task_id, 'task_category': task_category, 'question': question, 'answer': answer,
                    'rating': rating}
            completed_list.append(data)
        return Response({"pending": pending_list, "completed": completed_list}, status=200)


class HelperFeedbackReply(APIView):
    def post(self, request):
        username = request.data.get("username")
        task = request.data.get("task")
        rating = float(request.data.get("rating"))
        comment = request.data.get("comment")
        user = get_object_or_404(User, username=username)
        helper = get_object_or_404(Helper, user=user)
        task = Task.objects.get(id=task)
        feedback = Feedback.objects.get(helper=helper, q_a__task=task)
        feedback.rating = rating
        feedback.comment = comment
        feedback.status = 'completed'
        feedback.save()
        feedbacks = Feedback.objects.filter(q_a=feedback.q_a, status="completed")
        rating = 0
        for f in feedbacks:
            rating += f.rating
        try:
            rating /= len(feedbacks)
            feedback.q_a.rating = rating
            feedback.q_a.save()
        except:
            pass
        return Response({"notification": "successful"}, status=200)


class HelperAcceptReallocate(APIView):
    def post(self, request):
        username = request.data.get("username")
        task_id = request.data.get("task_id")
        user = get_object_or_404(User, username=username)
        helper = get_object_or_404(Helper, user=user)
        task = Task.objects.get(id=task_id)
        action = Action.objects.get(task=task, status=ActionStatusOptions.ASSIGNED)
        assign = Assign.objects.filter(action=action, status=AssignStatusOptions.ACCEPTED)
        if assign:
            return Response({"notification:task reallocation already accepted"}, status=200)
        assign = Assign.objects.get(action=action, helper=helper)
        assign.accepted = timezone.now()
        assign.status = AssignStatusOptions.ACCEPTED
        assign.save()
        return Response({"notification": "successful"}, status=200)


class HelperAccept(APIView):
    def post(self, request):
        username = request.data.get("username")
        task_id = request.data.get("task_id")
        task_status = request.data.get("task_status")
        user = get_object_or_404(User, username=username)
        helper = get_object_or_404(Helper, user=user)
        task = Task.objects.get(id=task_id)
        action = Action.objects.get(task=task, status=ActionStatusOptions.ASSIGN_PENDING)
        assign = Assign.objects.filter(action=action, status=AssignStatusOptions.ACCEPTED)
        if assign:
            return Response({"notification:task already accepted"}, status=200)
        assign = Assign.objects.get(action=action, helper=helper)
        if task_status == "accept":
            assign.status = AssignStatusOptions.ACCEPTED
            assign.accepted = timezone.now()
            assign.save()
            action.status = ActionStatusOptions.ASSIGNED
            action.save()
            assign = Assign.objects.filter(action=action).exclude(status=AssignStatusOptions.ACCEPTED)
            assign.delete()
            return Response({"notification": "successful"}, status=200)
        else:
            assign.status = AssignStatusOptions.REJECTED
            assign.save()
            assigns = Assign.objects.filter(action=action).exclude(status=AssignStatusOptions.REJECTED)
            if len(assigns) == 0:
                action.status = ActionStatusOptions.REJECTED
                action.save()
                assigns = Assign.objects.filter(action=action, status=AssignStatusOptions.REJECTED)
                rejected_helpers = []
                for assign in assigns:
                    rejected_helpers.append(assign.helper.id)
                helper_method = HelperMethods()
                data = NEW_TASK_NOTIF
                action = Action(task=task)
                action.save()
                helper_method.assign_helpers(action, task.category, data, NO_OF_HELPERS, rejected_helpers)
            return Response({"notification": "successful"}, status=200)


class ReallocateTask(APIView):
    def post(self, request):
        task_id = request.data.get("task_id")
        helper_selected = request.data.get("newhelper")
        username = request.data.get("username")
        reason = request.data.get("reason")
        user = get_object_or_404(User, username=username)
        helper = get_object_or_404(Helper, user=user)
        new_user = get_object_or_404(User, username=helper_selected)
        new_helper = get_object_or_404(Helper, user=new_user)
        task = Task.objects.get(id=task_id)
        action = Action.objects.get(task=task, status=ActionStatusOptions.ASSIGNED)
        assign_accept = Assign.objects.filter(action=action, helper=helper, status=AssignStatusOptions.ACCEPTED)
        assign_reallocate = Assign.objects.filter(action=action, helper=helper, status=AssignStatusOptions.REALLOCATED)
        assign_feedback = Assign.objects.filter(action=action, helper=helper, status=AssignStatusOptions.FOLLOW_UP_ACCEPTED)
        if assign_accept:
            assign = Assign.objects.get(action=action, helper=helper, status=AssignStatusOptions.ACCEPTED)
            assign.status = AssignStatusOptions.REALLOCATED
            assign.helper = new_helper
            assign.modified = timezone.localtime(timezone.now())
            assign.save()
        elif assign_reallocate:
            assign = Assign.objects.get(action=action, helper=helper, status=AssignStatusOptions.REALLOCATED)
            assign.helper = new_helper
            assign.modified = timezone.localtime(timezone.now())
            assign.save()
        elif assign_feedback:
            assign = Assign.objects.get(action=action, helper=helper, status=AssignStatusOptions.FOLLOW_UP_ACCEPTED)
            assign.helper = new_helper
            assign.modified = timezone.localtime(timezone.now())
            assign.save()
        
        history = TaskHistory(task=task, fromHelper=helper, toHelper=new_helper, reason=reason)
        history.save()
        helper_method = HelperMethods()
        data = REALLOCATE_TASK_NOTIF
        print("Reallocate:")
        print(action)
        print(data)
        helper_method.send_new_task_notification(action=action, data=data)
        return Response({"notification": "successful"}, status=200)

    def get(self, request):
        task_id = request.GET.get("task_id")
        username = request.GET.get("username")
        print(username)
        user = get_object_or_404(User, username=username)
        helper = get_object_or_404(Helper, user=user)
        task = Task.objects.get(id=task_id)
        histories = TaskHistory.objects.filter(task=task, toHelper=helper).order_by('-reallocateDate')
        history = histories[0]
        reallocatedby = history.fromHelper.user.username
        reason = history.reason
        print (reallocatedby)
        print (reason)
        data = {
            "reallocatedby": reallocatedby,
            "reason": reason,
        }
        return Response(data, status=200)


class CreateFollowUpTask(APIView):
    def post(self, request):
        task_id = request.data.get("task_id")
        create_date = request.data.get("create_date")
        new_date = ""
        print(create_date)
        for i in range(len(create_date)):
            if i != 5:
                new_date = new_date + create_date[i]
        print(new_date)
        username = request.data.get("username")
        print(username)
        user = get_object_or_404(User, username=username)
        helper = get_object_or_404(Helper, user=user)
        print ("task_id", task_id)
        print ("create_date", create_date)
        task = Task.objects.get(id=task_id)
        valid_datetime = datetime.strptime(create_date, '%Y-%m-%d')
        print(valid_datetime)
        print(valid_datetime.date())
        follow_up_task = FollowUpTask(parent_task=task, marked_date=create_date, created_date=date.today(), helper=helper)
        follow_up_task.save()
        # Delete after this. Just for testing
        pending_follow = FollowUpTask.objects.filter(marked_date__year=date.today().year,marked_date__month=date.today().month,marked_date__day=date.today().day, create_status = 'Inactive')
        print(date.today())
        print ("pending follow: ", pending_follow)
        for tasks in pending_follow:
            print("created_date", tasks.created_date)
            print("marked_date", tasks.marked_date)
            print(tasks.marked_date == date.today())
            
            par_task = tasks.parent_task
            tasks.create_status = 'Active'
            call_request = par_task.call_request
            hc = par_task.category
            new_task = Task.objects.create(call_request=call_request, category=hc)
            if len(par_task.language.all()) > 0:
                lang = par_task.language.all()[0]
                new_task.language.add(lang)
            helper = tasks.helper
            tasks.task = new_task
            tasks.save()
            print("new task created :", new_task)
            print("in followup task: ", tasks.task)

            current_action = Action.objects.create(
                task=new_task,
                action_type=ActionTypeOptions.PRIMARY,
                status=ActionStatusOptions.ASSIGNED,

            )
            Assign.objects.create(helper=helper, action=current_action, status=AssignStatusOptions.FOLLOW_UP_ACCEPTED)
            data = 'New Follow Up Task has been assigned for Task: ' + str(par_task.id)
            helper_methods = HelperMethods()
            helper_methods.send_new_task_notification(action=Action.objects.get(task=par_task), data=data)
        return Response({"notification": "successful"}, status=200)

class CreateSurveyFollowUpTask(APIView):
    def post(self, request):
        task_id = request.data.get("task_id")
        survey = request.data.get("survey")
        client = request.data.get("client")
        create_date = request.data.get("create_date")
        print(survey)
        print(Survey.objects.filter())
        survey = SurveyTask.objects.get(id=task_id).survey
        print(survey)
        client = Client.objects.get(client_number = request.data.get("client"))
        new_date = ""
        print(create_date)
        for i in range(len(create_date)):
            if i != 5:
                new_date = new_date + create_date[i]
        print(new_date)
        username = request.data.get("username")
        print(username)
        user = get_object_or_404(User, username=username)
        helper = get_object_or_404(Helper, user=user)
        print ("task_id", task_id)
        print ("create_date", create_date)
        task = SurveyTask.objects.get(id=task_id)
        follow_up_task = FollowUpSurveyTask(parent_task=task, marked_date=create_date, created_date=date.today(), helper=helper)
        follow_up_task.save()
        # Delete after this. Just for testing
        pending_follow = FollowUpSurveyTask.objects.filter(marked_date__year=date.today().year,marked_date__month=date.today().month,marked_date__day=date.today().day, create_status = 'Inactive')
        print ("pending follow: ", pending_follow)
        for tasks in pending_follow:
            par_task = tasks.parent_task
            tasks.create_status = 'Active'
            #edit_form_url = request.data.get("editform")
            edit_form_url = tasks.parent_task.edit_form_url
            print(edit_form_url)
            new_task = SurveyTask.objects.create(survey=survey, client=client, edit_form_url = edit_form_url, helper=helper, status = "assigned")
            helper = tasks.helper

            tasks.task = new_task
            tasks.save()
            print("new survey task created :", new_task)
            print("in followup task: ", tasks.task)

            data = 'New Follow Up Task has been assigned for Task: ' + task_id
            helper_methods = HelperMethods()
            try:
                helper_methods.send_new_task_notification_for_accepted_action(helper,data)
            except Exception as e:
                print(str(e))

        return Response({"notification": "successful"}, status=200)



class QandADetails(APIView):
    def post(self, request):
        question = request.data.get("question")
        answer = request.data.get("answer")
        task_id = request.data.get("task_id")
        client_name = request.data.get("client_name")
        categories = json.loads(request.data.get("categories"))
        subcategories = json.loads(request.data.get("subcategories"))

        task = Task.objects.get(id=task_id)
        #for category in categories:
        #    if categories.get(category) == "True":
        #        cat = CategorySubcategory.objects.filter(category=category).values('category').distinct()

        #for subcategory in subcategories:
        #    if subcategories.get(subcategory) == "True":
        #        task.tasksubcategory.add(CategorySubcategory.objects.get(subcategory=subcategory))
        #        task.taskcategory.add(CategorySubcategory.objects.get(subcategory=subcategory))

        task.save()

        if len(client_name):
            task.call_request.client.name = client_name
            task.call_request.client.save()
        calls = Call_Forward_Details.objects.filter(task=task, status='completed')
        if calls:
            q_and_a = QandA.objects.filter(task=task)
            if q_and_a:
                q_and_as = QandA.objects.get(task=task)
                q_and_as.question = question
                q_and_as.answer = answer
                q_and_as.save()
            else:
                q_and_as = QandA(task=task, question=question, answer=answer)
                q_and_as.save()
            task.call_request.client.name = client_name
            task.call_request.client.save()
            if FEEDBACK_NEEDED:
                action = Action.objects.get(task=task, status=ActionStatusOptions.ASSIGNED)
                assign = Assign.objects.get(action=action)
                helper = assign.helper
                helpers = Helper.objects.exclude(id=helper.id).filter(category=task.category)[0:NUMBER_FEEDBACK_TASKS]
                for helper in helpers:
                    feedback = Feedback(q_a=q_and_as, helper=helper)
                    feedback.save()
                # try:
                #     push_notification(helper.gcm_canonical_id,'New Feedback Task')
                # except:
                #     pass

            return Response({"notification": "successful"}, status=200)
        else:
            unanswered_calls = Call_Forward_Details.objects.filter(task=task, status='not_answered').count()
            if unanswered_calls >= MIN_CALL_ATTEMPTS:
                q_and_a = QandA.objects.filter(task=task)
                if q_and_a:
                    q_and_as = QandA.objects.get(task=task)
                    q_and_as.question = question
                    q_and_as.answer = answer
                    q_and_as.save()
                else:
                    q_and_as = QandA(task=task, question=question, answer=answer)
                    q_and_as.save()
                return Response({"notification": "successful"}, status=200)
            else:
                return Response({"notification": "unsuccessful"}, status=200)


    def get(self, request):
        task_id = request.GET.get("task_id")
        task = Task.objects.get(id=task_id)
        qanda = QandA.objects.get(task=task)
        data = {
            "question": qanda.question,
            "answer": qanda.answer,
            "rating": qanda.rating,
        }
        return Response(data, status=200)


class TaskComplete(APIView):
    def post(self, request):
        task_id = request.data.get("task_id")
        task = Task.objects.get(id=task_id)
        action = Action.objects.get(task=task, status=ActionStatusOptions.ASSIGNED)
        assign = Assign.objects.get(action=action)
        task.status = TaskStatusOptions.COMPLETED
        task.save()
        action.status = ActionStatusOptions.COMPLETED
        action.save()
        assign.status = AssignStatusOptions.COMPLETED
        assign.save()
        return Response({"notification": "successful"}, status=200)


class SurveyTaskComplete(APIView):
    def post(self, request):
        task_id = request.data.get("task_id")
        print("task_id", task_id)
        survey_task = SurveyTask.objects.get(id=task_id)
        calls = Call_Forward_Details.objects.filter(survey_task=survey_task, status='completed')
        if survey_task.edit_form_url:
            url = survey_task.edit_form_url
            page = requests.get(url)
            soup = BeautifulSoup(page.content, 'html.parser')
            tag = soup.findAll("input", {"name": "draftResponse"})[0]
            values = tag['value'].split("[null,")[1:]

            id_dict = OrderedDict()
            v_list = list()
            for v in values:
                print(v[0:v.find(",")])
                id_dict[v[0:v.find(",")]] = v[v.find("["):v.find("]") + 1]

            script_tag = soup.findAll("script", {"type": "text/javascript"})[1]
            txt = script_tag.string

            splitted = txt.split("\"")
            for key in id_dict.keys():
                print(key)
                for i in range(len(splitted)):
                    if key in splitted[i]:
                        v_list.append((splitted[i - 1], id_dict[key]))

            s = ""
            for item in v_list:
                s = s + item[0] + ":" + item[1] + ";;"
            print("string--->" , s, id_dict)
            survey_response = SurveyResponse.objects.filter(survey=survey_task.survey, survey_task=survey_task)
            if survey_response:
                SurveyResponse.objects.filter(survey=survey_task.survey, survey_task=survey_task).update(modified=timezone.localtime(timezone.now()),survey_data=s)
            else:
                SurveyResponse.objects.create(survey=survey_task.survey, survey_task=survey_task, survey_data=s)
                
        if calls :
            if survey_task.edit_form_url:
                if survey_task.status == "fo_assigned":
                    survey_task.status = "fo_completed"
                else:
                    survey_task.status = "completed"
                survey_task.completedDateTime = timezone.now()
                survey_task.save()
                return Response({"notification": "successful"}, status=200)
            else:
                unanswered_calls = Call_Forward_Details.objects.filter(survey_task=survey_task, status='not_answered').count()
                if unanswered_calls >= 3:
                    if survey_task.status == "fo_assigned":
                        survey_task.status = "fo_completed"
                    else:
                        survey_task.status = "completed"

                    survey_task.completedDateTime = timezone.now()
                    survey_task.save()
                    return Response({"notification": "successful"}, status=200)
                else:
                    return Response({"notification": "fill form"}, status=200)
        else:
            unanswered_calls = Call_Forward_Details.objects.filter(survey_task=survey_task, status='not_answered').count()
            if unanswered_calls >= 0:
                if survey_task.status == "fo_assigned":
                    survey_task.status = "fo_completed"
                else:
                    survey_task.status = "completed"

                survey_task.completedDateTime = timezone.now()
                survey_task.save()
                return Response({"notification": "successful"}, status=200)
            else:
                return Response({"notification": "call client"}, status=200)

class CallForward(APIView):
    def post(self, request):
        task_id = request.data.get("task_id")
        type = request.data.get("type")
        if type == "survey":
            survey_task = SurveyTask.objects.get(id=task_id)
            helper_no = survey_task.helper.helper_number
            client_no = survey_task.client.client_number
            Call_Forward.objects.filter(helper_no=helper_no).delete()
            call_forward = Call_Forward(helper_no=helper_no[len(helper_no)-10:], caller_no=client_no, survey_task=survey_task, type="survey")
            call_forward.save()
        else:
            task = Task.objects.get(id=task_id)
            action = Action.objects.get(task=task)
            assign = Assign.objects.get(action=action)
            helper_no = assign.helper.helper_number
            if not assign.helper.is_anonymous:
                return Response({"notification": "successful"}, status=200)
            client_no = task.call_request.client.client_number
            Call_Forward.objects.filter(helper_no=helper_no).delete()
            call_forward = Call_Forward(helper_no=helper_no[len(helper_no)-10:], caller_no=client_no, task=task, type="regular")
            call_forward.save()
        return Response({"notification": "successful"}, status=200)


class ActivateHelper(View):
    def post(self, request, id):
        helper = Helper.objects.get(user__id=id)
        level = request.POST['level']
        h_type = request.POST['type']

        for i, lev in HelperLevel.LEVEL_CHOICES:
            if lev == level:
                helper.level = i
        for i, lev in HelperType.TYPE_CHOICES:
            if lev == h_type:
                helper.helper_type = i
        helper.login_status = LoginStatus.LOGGED_OUT
        helper.save()
        if helper.helper_type == HelperType.DIRECT:
            start_time = datetime.strptime(START_TIME, '%H:%M').time()
            end_time = datetime.strptime(END_TIME, '%H:%M').time()
            days = ['SUNDAY', 'MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY']
            for day in DIRECT_DAYS:
                day_ind = days.index(day.upper())
                new_slot = AvailableSlot(helper=helper, day_of_week=day_ind, start_time=start_time, end_time=end_time)
                new_slot.save()
            AvailableSlot()
        return HttpResponseRedirect(reverse('dashboard:home'))


class ActivateAllHelper(View):
    def get(self, request):
        helpers = Helper.objects.filter(login_status=LoginStatus.PENDING)
        for helper in helpers:
            helper.login_status = LoginStatus.LOGGED_OUT
            helper.save()
        return HttpResponseRedirect(reverse('dashboard:home'))


class DeleteActivation(View):
    def get(self, request, id):
        helper = Helper.objects.get(user__id=id)
        helper.user.delete()
        return HttpResponseRedirect(reverse('dashboard:home'))


class DeactivateAllHelper(View):
    def get(self, request):
        helpers = Helper.objects.filter(login_status=LoginStatus.PENDING)
        for helper in helpers:
            helper.user.delete()
        return HttpResponseRedirect(reverse('dashboard:home'))


class Refresh_GCM(APIView):
    def post(self, request):
        gcm_id = request.data.get("gcm_id")
        username = request.data.get("username")
        user = get_object_or_404(User, username=username)
        helper = get_object_or_404(Helper, user=user)
        helper.gcm_canonical_id = gcm_id
        helper.save()
        return Response({"notification": "successful"}, status=200)


class AvailableSlots(APIView):

    def post(self, request):
        username = request.data.get("username")
        available_days = request.data.get("day_of_week")
        user = get_object_or_404(User, username=username)
        helper = get_object_or_404(Helper, user=user)
        start_time = datetime.strptime(request.data.get("start_time"), '%H:%M').time()
        end_time = datetime.strptime(request.data.get("end_time"), '%H:%M').time()
        print("TIME ", request.data.get("start_time"), end_time) 
        available_days = available_days[1:-1].split(", ")
        days = ['SUNDAY', 'MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY']
        for day in available_days:
            day_ind = days.index(day.upper())
            new_slot = AvailableSlot(helper=helper, day_of_week=day_ind, start_time=start_time, end_time=end_time)
            new_slot.save()
        return Response({"notification": "successful"}, status=200)

    def get(self, request):
        username = request.GET.get("username")
        user = get_object_or_404(User, username=username)
        helper = get_object_or_404(Helper, user=user)
        all_slots = AvailableSlot.objects.filter(helper=helper)
        slots = all_slots.values('start_time', 'end_time').annotate(str_start_time=
                                                                    Cast('start_time', CharField())).annotate(
            str_end_time=Cast('end_time', CharField())).annotate(all_days=GroupConcat('day_of_week', ','))
        data = {
            "slots": list(slots)
        }
        return JsonResponse(data=data, status=200)

    def delete(self, request):              
        username = request.GET.get("username")
        start_time = request.GET.get("start_time").split(':')
        end_time = request.GET.get("end_time").split(':')
        if start_time[1].find("PM")>-1:
            start_time = str(int(start_time[0]) + 12) + ":" + start_time[1]
        else:
            start_time = start_time[0] + ":" + start_time[1]
        if end_time[1].find("PM")>-1:
            end_time = str(int(end_time[0]) + 12) + ":" + end_time[1]    
        else:
            end_time = end_time[0] + ":" + end_time[1]
        start_time = datetime.strptime(start_time.strip(" PM").strip(" AM"), '%H:%M').time()
        end_time = datetime.strptime(end_time.strip(" PM").strip(" AM"), '%H:%M').time()
        user = get_object_or_404(User, username=username)
        helper = get_object_or_404(Helper, user=user)
        print("len--", len(AvailableSlot.objects.filter(helper=helper, start_time=start_time, end_time=end_time)))
        AvailableSlot.objects.filter(helper=helper, start_time=start_time, end_time=end_time).delete()
        return Response({"notification": "successful"}, status=200)


class DoctorAvailableSlots(APIView):

    # def __init__(self):
    #     csv_path = "/home/brserver1/demo_2/generic_helpline/doctor_slots/"
    #     for root,dirs,files in os.walk(csv_path):

    #         for file in files:
    #             if file.endswith(".csv"):
    #                 # f=open(file, 'r')
    #                 #  perform calculation
                    
    #                 with open(csv_path + file, 'r') as file_:
    #                     reader = csv.reader(file_)
                        
    #                     # for row in reader:
    #                     #     print(row)

    #                     # file_data = '/home/brserver1/demo_2/generic_helpline/doctor_slots/doctor_1_slot.csv'.read().decode("utf-8")	
    #                     # lines = file_data.split("\n")
    #                     #loop over the lines and save them in db. If error , store as string and then display
    #                     doctor_id, doctor_name = "", ""#reader[0].split(',')
    #                     for line in reader:	
    #                         if doctor_id == "":
    #                             doctor_id, doctor_name = line[0].strip(), line[1].strip()
    #                             continue
    #                         fields = line
    #                         data_dict = {}
    #                         data_dict["slot_date"] = datetime.strptime(fields[0], "%Y-%m-%d").date()
    #                         data_dict["slot_start_times"] = fields[1]
    #                         # print(data_dict)
    #                         print(type(data_dict["slot_date"]))

                            # obj = DoctorAvailableSlot.objects.filter(slot_date=data_dict["slot_date"], doctor_name=doctor_name)
                            # # print(len(obj))
                            # if len(obj) > 0:
                            #     # print(obj[0])
                            #     obj[0].slot_start_times = data_dict["slot_start_times"]
                            #     obj[0].save()
                            #     # print(obj[0])
                            # else:
                            #     new_slot = DoctorAvailableSlot(doctor_id=doctor_id, doctor_name=doctor_name, slot_date=data_dict["slot_date"], slot_start_times=data_dict["slot_start_times"])
                            #     new_slot.save()
                    # f.close()
        


    def post(self, request):
        
        username = request.data.get("username")
        user = get_object_or_404(User, username=username)
        helper = get_object_or_404(Helper, user=user)
        task_id = request.data.get("task_id")
        task = Task.objects.get(id=task_id)
        doctor_name = request.data.get("doctor_name")
        slot_time = request.data.get("slot_time")
        forBooking = request.data.get("forBooking")
        picked_date = request.data.get("picked_date")

        # DoctorBookedSlot.objects.filter(task_id=task).delete()

        if forBooking == "1":
            
            obj = DoctorAvailableSlot.objects.filter(slot_date=picked_date, doctor_name=doctor_name)
            strin = obj[0].slot_start_times
            strin = strin.replace(" " + slot_time, "")
            print(strin)
            if len(obj) > 0:
                # print(obj[0])
                slot_date = datetime.strptime(picked_date, "%Y-%m-%d").date()
                slot_picked_time = slot_time
                obj_ = DoctorBookedSlot.objects.filter(task_id=task, helper=helper, doctor_name=doctor_name, slot_date=slot_date, slot_time=slot_picked_time)
                if (len(obj_) == 0 ):
                    booked_slot = DoctorBookedSlot(task_id=task, helper=helper, doctor_name=doctor_name, slot_date=slot_date, slot_time=slot_picked_time)
                    booked_slot.save()
                print(len(DoctorBookedSlot.objects.filter(task_id=task)))
                print(booked_slot.slot_date)
                obj[0].slot_start_times = strin
                obj[0].save()
                


            # obj1 = DoctorAvailableSlot.objects.get(slot_date=picked_date, doctor_name=doctor_name)
            # print(obj1.slot_date, obj1.doctor_name, obj1.slot_start_times)
            # print(obj)
            # obj[0].slot_start_times = strin.replace(" " + slot_time, "")
            # print((obj[0].slot_start_times).replace(" " + slot_time, ""))
            # obj[0].save()
            # print(obj[0].slot_start_times)
            # print("Object saved ", obj[0])
            # print(picked_date, doctor_name)
            # print(obj[0].id)
        
        return Response({"notification": "successful"}, status=200)

    def get(self, request):
        # username = request.GET.get("username")
        # user = get_object_or_404(User, username=username)
        # helper = get_object_or_404(Helper, user=user)
        user_date = request.GET.get("slot_date")
        all_slots = DoctorAvailableSlot.objects.filter(slot_date=user_date)
        slots = all_slots.values('slot_start_times').annotate(slot_date=
                                                                    Cast('slot_date', CharField())).annotate(doctor_name=
                                                                    Cast('doctor_name', CharField()))
        data = {
            "slots": list(slots)
        }
        return JsonResponse(data=data, status=200)

    def delete(self, request):              
        username = request.GET.get("username")
        start_time = request.GET.get("start_time").split(':')
        end_time = request.GET.get("end_time").split(':')
        if start_time[1].find("PM")>-1:
            start_time = str(int(start_time[0]) + 12) + ":" + start_time[1]
        else:
            start_time = start_time[0] + ":" + start_time[1]
        if end_time[1].find("PM")>-1:
            end_time = str(int(end_time[0]) + 12) + ":" + end_time[1]    
        else:
            end_time = end_time[0] + ":" + end_time[1]
        start_time = datetime.strptime(start_time.strip(" PM").strip(" AM"), '%H:%M').time()
        end_time = datetime.strptime(end_time.strip(" PM").strip(" AM"), '%H:%M').time()
        user = get_object_or_404(User, username=username)
        helper = get_object_or_404(Helper, user=user)
        print("len--", len(DoctorAvailableSlot.objects.filter(helper=helper, start_time=start_time, end_time=end_time)))
        DoctorAvailableSlot.objects.filter(helper=helper, start_time=start_time, end_time=end_time).delete()
        return Response({"notification": "successful"}, status=200)

class DoctorBookedSlots(APIView):
    def get(self, request):
        task_id = request.GET.get("task_id")
        task = Task.objects.get(id=task_id)
        username = request.GET.get("username")
        user = get_object_or_404(User, username=username)
        helper = get_object_or_404(Helper, user=user)
        all_slots = DoctorBookedSlot.objects.filter(helper=helper, task_id=task)
        slots = all_slots.values('slot_time').annotate(str_date=
                                                                    Cast('slot_date', CharField())).annotate(doctor_name=
                                                                    Cast('doctor_name', CharField())).annotate(task_id=
                                                                    Cast('task_id', CharField()))
        data = {
            "slots": list(slots)
        }
        return JsonResponse(data=data, status=200)


    def delete(self, request):              
        username = request.GET.get("username")
        user = get_object_or_404(User, username=username)
        helper = get_object_or_404(Helper, user=user)
        # task_id = request.data.get("task_id")
        # task = Task.objects.get(id=task_id)

        task_id = request.GET.get("task_id")
        task = Task.objects.get(id=task_id)

        # doctor_name = request.data.get("doctor_name")
        # slot_time = request.data.get("slot_time")
        # forBooking = request.data.get("forBooking")
        # picked_date = request.data.get("picked_date")
#     def delete(self, request):
        obj = DoctorBookedSlot.objects.filter(helper=helper, task_id=task)
        slot_date = obj[0].slot_date
        doctor_name = obj[0].doctor_name
        slot_time = obj[0].slot_time

        obj_ = DoctorAvailableSlot.objects.get(slot_date=slot_date, doctor_name=doctor_name)

        strin = obj_.slot_start_times
        
        print(strin)
        # print(slot_time)
        strin = strin + " " + str(slot_time)
        # print(obj_.slot_start_times)
        # print(strin)
        obj_.slot_start_times = strin
        obj_.save()
        print(obj_.slot_start_times)

        DoctorBookedSlot.objects.get(task_id=task).delete()

        return Response({"notification": "successful"}, status=200)

class newClientTasks(APIView):
    def fetch_assigns(self, assign_list):
        return_list = []
        for assign in assign_list:
            task_id = assign.action.task.id
            tag_string = assign.action.task.tag_string
            if not assign.action.task.tag_string:
                tag_string = ""
            task_status=assign.status;
            client_calls = assign.action.task.client_calls
            if task_status==AssignStatusOptions.ACCEPTED:
                task_status="accepted"
            elif task_status==AssignStatusOptions.REALLOCATED:
                task_status="reallocated"
            elif task_status==AssignStatusOptions.PENDING:
                task_status="pending"
            elif task_status==AssignStatusOptions.FOLLOW_UP_ACCEPTED:
                task_status="followup"
            elif task_status==AssignStatusOptions.COMPLETED:
                task_status="completed"
                try:
                    followup = FollowUpTask.objects.get(task_id=task_id)
                    client_calls = followup.parent_task_id
                except:
                    #print("Exception helper tasks")
                    followup = FollowUpTask.objects.filter(task_id=task_id)
            if assign.action.task.category:
                task_category = assign.action.task.category.name
            else:
                task_category = ""
            caller_name = assign.action.task.call_request.client.name
            caller_number = assign.action.task.call_request.client.client_number
            caller_location = assign.action.task.call_request.client.location
            local_datetime = timezone.localtime(assign.action.task.created)
            local_date = local_datetime.strftime("%d/%m/%Y")
            local_time = local_datetime.strftime("%I:%M %p")
            try:
                task_sub_category = str(assign.action.task.tasksubcategory.all()[:1].get())
                print(str(assign.action.task.tasksubcategory.all()[:1].get()))
            except:
                task_sub_category = ""
            #print(str(assign.action.task.tasksubcategory.all()[:1].get()))

            if len(assign.action.task.language.all()) > 0:
                language = assign.action.task.language.all()[0]
            else:
                language = ""
            data = {"parent_task_id": "", "task_id": task_id, "task_status": task_status, "tag_string": tag_string, "task_category": task_category, "caller_name": caller_name,
                    "caller_location": caller_location,
                    "caller_number": caller_number, "client_calls": client_calls, "date": local_date, "time": local_time, "language": str(language)}
            return_list.append(data)
        return return_list
    
    def get(self, request):
            # print("CLIENTTASKS")
            phno = request.GET.get("phno")
            # user = get_object_or_404(User, username=username)
            # helper = get_object_or_404(Helper, user=user)
            # client_number = request.GET.get("client_number")
            # phno = "9881246601"
            # print("Client Number", phno)
            client = get_object_or_404(Client, client_number=phno)
            call_req = CallRequest.objects.filter(client=client)
            tasks = Task.objects.filter(call_request__in=call_req)
            actions = Action.objects.filter(task__in=tasks)
            completed_assigns = Assign.objects.filter(action__in=actions, status=AssignStatusOptions.COMPLETED)
            accepted_assigns = Assign.objects.filter(action__in=actions, status=AssignStatusOptions.ACCEPTED)
            completed_tasks = self.fetch_assigns(completed_assigns)
            accepted_tasks = self.fetch_assigns(accepted_assigns)

            
            # return Response({"accepted": accepted_tasks, "completed": completed_tasks}, status=200)
            data = {
                    "accepted": accepted_tasks, "completed": completed_tasks
                }
            return JsonResponse(data=data, status=200)





