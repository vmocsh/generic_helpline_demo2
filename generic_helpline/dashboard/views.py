import codecs
import csv
import json
import os
import datetime
import traceback
import requests
from io import StringIO
from .forms import AddTask


from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.db.models import Q
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import View
from django.core.files import File
from django.http import FileResponse

from authentication.models import Forgot_Password
from authentication.send_email import email_to
from constants import *
from ivr.models import Call_Forward_Details
from management.models import HelperCategory, HelpLine, Tag_List, DoctorAvailableSlot
from management.views import DoctorAvailableSlots
from ivr.models import Language
from registercall.views import RegisterCall
from register_helper.models import Helper
from register_helper.options import LoginStatus, HelperLevel, HelperType
from registercall.models import Task, CallRequest, Client
from surveys.models import Survey, SurveyTask, SurveyResponse
from task_manager.models import Assign, QandA, AssignStatusOptions, ActionStatusOptions, Action ,TaskHistory
from registercall.options import CallRequestStatusOptions
from urllib.request import urlopen, urlretrieve
from bs4 import BeautifulSoup
from tempfile import NamedTemporaryFile
import csv
from tempfile import TemporaryFile
import pandas as pd

# Create your views here.


class Clientwise_Surveys(LoginRequiredMixin, View):
    login_url = '/web_auth/login/'
    redirect_field_name = 'redirect_to'

    def get(self, request):
        surveytasks = SurveyTask.objects.all()
        clients = Client.objects.all()
        client_stats = []
        for client in clients:
            client_survey_tasks = surveytasks.filter(client=client)
            stat=[]
            if client.name:
                stat.append(client)
                number_of_surveys = len(client_survey_tasks)
                completed_survey_tasks = len(client_survey_tasks.filter(status='completed'))
                stat.append(number_of_surveys)
                stat.append(completed_survey_tasks)
                client_stats.append(stat)
        context = {
            'url': BASE_URL,
            'client_stats': client_stats,
        }
        return render(request, "clientwise_surveys.html", context)

class Client_Profile(LoginRequiredMixin, View):
    login_url = '/web_auth/login/'
    redirect_field_name = 'redirect_to'

    def get(self, request, pk):
        client = Client.objects.get(pk=pk)
        surveytasks = SurveyTask.objects.all()
        client_survey_tasks = surveytasks.filter(client=client)
        print("Client:", client.name)
        context = {
            'url': BASE_URL,
            'client': client,
            'client_survey_tasks': client_survey_tasks,
        }
        return render(request, 'client_profile.html', context)

class download_csv(LoginRequiredMixin, View):
    login_url = '/web_auth/login/'
    redirect_field_name = 'redirect_to'

    def get(self, request, pk):
        survey = Survey.objects.get(pk=pk)
        survey_responses = SurveyResponse.objects.filter(survey=survey).order_by('modified')
        url = survey.response_csv_url
        url = url[0:url.find("/edit")]+"/export?format=csv"
        urlretrieve(url, "survey_csv/"+str(survey.id) + "_" + str(survey.name)+".csv")
        csv_file = "survey_csv/" + str(survey.id) + "_" + str(survey.name) + ".csv"
        csv_file_out = "survey_csv/" + str(survey.id) + "_" + str(survey.name) + "_out.csv"
        with open(csv_file, 'r') as csvinput:
            with open(csv_file_out, 'w') as csvoutput:
                writer = csv.writer(csvoutput, lineterminator='\n')
                reader = csv.reader(csvinput)
                row0 = next(reader)
                row0.append('Client name')
                row0.append('Phone no')
                writer.writerow(row0)
                for response in survey_responses:
                    response_data = response.survey_data
                    row = []
                    data = response_data.split(";;")
                    row.append(response.modified)
                    for i in range(len(data)-1):
                        row.append( data[i].split(":[\"")[1].split("\"]")[0])
                    row.append(response.survey_task.client.name)
                    row.append(response.survey_task.client.client_number)
                    writer.writerow(row)
        with open(csv_file_out) as csvfile:
            response = HttpResponse(csvfile, content_type='text/csv')
            response['Content-Disposition'] = "attachment; filename="+ str(survey.id) + "_" + str(survey.name)+".csv"
            return response
class Home(LoginRequiredMixin, View):
    login_url = LOGIN_URL
    redirect_field_name = 'redirect_to'

    def get(self, request):
        user = request.user
        helper = Helper.objects.filter(user=user)
        helper_stats = []
        if helper:
            assigns = Assign.objects.filter(helper__helpline=helper[0].helpline).order_by('-id')
            helpers = Helper.objects.filter(helpline=helper[0].helpline).exclude(login_status=3)
            pending_users = Helper.objects.filter(helpline=helper[0].helpline, login_status=3)
            pending = 0
            completed = 0
            rejected = 0
            timeout = 0
            total = 0
            actions = set()
            for assign in assigns:
                actions.add(assign.action)
            for action in actions:
                if action.status == ActionStatusOptions.ASSIGN_PENDING or action.status == ActionStatusOptions.ASSIGNED:
                    pending += 1
                elif action.status == ActionStatusOptions.COMPLETED:
                    completed += 1
                elif action.status == ActionStatusOptions.REJECTED:
                    rejected += 1
                elif action.status == ActionStatusOptions.ASSIGN_TIMEOUT:
                    timeout += 1
                total += 1
            for h in helpers:
                stat=[]
                stat.append(h)
                #assigns = Assign.objects.filter(helper__helpline=helper[0].helpline, helper=h, action__status=ActionStatusOptions.ASSIGNED)
                assigns = Assign.objects.filter(helper__helpline=helper[0].helpline,helper=h).order_by('created')
                assigns_completed = Assign.objects.filter(helper__helpline=helper[0].helpline, helper=h,
                                                          action__status=ActionStatusOptions.COMPLETED)
                total_assigns = len(assigns_completed)
                total_time = datetime.timedelta(0)
                for assign_completed in assigns_completed:
                    created_date = assign_completed.created
                    if QandA.objects.filter(task=assign_completed.action.task).count() < 1:
                        print("No QandA object for Task id----->", assign_completed.action.task.id, "<--------\n\n")
                    if QandA.objects.filter(task=assign_completed.action.task).count() > 1:
                        print("Multiple QandA objects for Task id----->", assign_completed.action.task.id,
                              "<------\n\n")
                    qanda = QandA.objects.get(task=assign_completed.action.task)
                    completed_date = qanda.created
                    total_time += completed_date - created_date
                try:
                    average_completion_time = total_time / total_assigns
                    hours, remainder = divmod(average_completion_time.total_seconds(), 3600)
                    minutes, seconds = divmod(remainder, 60)
                    average_completion_time = "%d hours %d mins" % (hours, minutes)
                except ZeroDivisionError:
                    average_completion_time = "%d hours %d mins" % (0, 0)

                total_assigns = 0
                total_time = datetime.timedelta(0)
                for i in range(len(assigns)):
                    if assigns[i].accepted:
                        total_time += assigns[i].accepted - assigns[i].created
                        total_assigns += 1
                try:
                    average_assignment_time = total_time / total_assigns
                    hours, remainder = divmod(average_assignment_time.total_seconds(), 3600)
                    minutes, seconds = divmod(remainder, 60)
                    average_assignment_time = "%d hours %d mins" % (hours, minutes)
                except ZeroDivisionError:
                    average_assignment_time = "%d hours %d mins" % (0, 0)

                total_assigns = 0
                total_time = datetime.timedelta(0)
                for i in range(len(assigns)):
                    call_forward_details = Call_Forward_Details.objects.filter(task=assigns[i].action.task).order_by('created')
                    if len(call_forward_details) != 0:
                        total_time += call_forward_details[0].created - assigns[i].created
                        total_assigns += 1
                try:
                    average_response_time = total_time / total_assigns
                    hours, remainder = divmod(average_response_time.total_seconds(), 3600)
                    minutes, seconds = divmod(remainder, 60)
                    average_response_time = "%d hours %d mins" % (hours, minutes)
                except ZeroDivisionError:
                    average_response_time = "%d hours %d mins" % (0, 0)

                stat.append(average_assignment_time)
                stat.append(average_response_time)
                stat.append(average_completion_time)

                task_dict = dict()
                pending_tasks = 0
                completed_tasks = 0
                rejected_tasks = 0
                timed_out_tasks = 0
                for assign in assigns:
                    if assign.status == AssignStatusOptions.PENDING or assign.status == AssignStatusOptions.ACCEPTED:
                        pending_tasks += 1
                    elif assign.status == AssignStatusOptions.COMPLETED:
                        completed_tasks += 1
                    elif assign.status == AssignStatusOptions.REJECTED:
                        rejected_tasks += 1
                    elif assign.status == AssignStatusOptions.TIMEOUT:
                        timed_out_tasks += 1
                    try:
                        task_dict[assign.created.date()] += 1
                    except KeyError:
                        task_dict[assign.created.date()] = 1
                stat.append(pending_tasks)
                stat.append(completed_tasks)
                stat.append(rejected_tasks)
                stat.append(timed_out_tasks)
                values = task_dict.values()
                try:
                    avg_tasks = sum(values) / len(values)
                except ZeroDivisionError:
                    avg_tasks = 0

                stat.append(avg_tasks)
                helper_stats.append(stat)
            assigns = Assign.objects.filter(helper__helpline=helper[0].helpline).order_by('-id')

        else:
            assigns = Assign.objects.all().order_by('-id')
            helpers = Helper.objects.all().order_by('-id')
            pending_users = Helper.objects.filter(login_status=3)
            pending = 0
            completed = 0
            rejected = 0
            timeout = 0
            total = 0
            actions = set()
            for assign in assigns:
                actions.add(assign.action)
            for action in actions:
                if action.status == ActionStatusOptions.ASSIGN_PENDING or action.status == ActionStatusOptions.ASSIGNED:
                    pending += 1
                elif action.status == ActionStatusOptions.COMPLETED:
                    completed += 1
                elif action.status == ActionStatusOptions.REJECTED:
                    rejected += 1
                elif action.status == ActionStatusOptions.ASSIGN_TIMEOUT:
                    timeout += 1
                total += 1
        if helper:
            helper = helper[0]
        else:
            helper = None

        helper_levels = []
        helper_types = []

        for i in range(len(HelperLevel.LEVEL_CHOICES)):
            _, level = HelperLevel.LEVEL_CHOICES[i]
            print(level)
            if level in HELPER_LEVELS:
                helper_levels.append(HelperLevel.LEVEL_CHOICES[i])

        for i in range(len(HelperType.TYPE_CHOICES)):
            _, h_type = HelperType.TYPE_CHOICES[i]
            print(h_type)
            if h_type in HELPER_TYPES:
                helper_types.append(HelperType.TYPE_CHOICES[i])

        context = {
            'url': STATIC_URL_APPEND,
            'helper': helper,
            'helper_stats': helper_stats,
            'assigns': assigns,
            'pending': pending,
            'completed': completed,
            'rejected': rejected,
            'timeout': timeout,
            'total': total,
            'helpers': helpers,
            'pending_users': pending_users,
            'helper_levels': helper_levels,
            'helper_types': helper_types,
        }

        return render(request, 'dashboard.html', context)


class Helper_Profile(LoginRequiredMixin, View):
    login_url = '/web_auth/login/'
    redirect_field_name = 'redirect_to'

    def get(self, request, pk, year, cat):
        helper = Helper.objects.get(pk=pk)

        if cat != 'All':
            assigns = Assign.objects.filter(created__year=year, helper=helper, action__task__category__name=cat)
        else:
            assigns = Assign.objects.filter(created__year=year, helper=helper)
        actions = set()
        for assign in assigns:
            actions.add(assign.action)
        helper_cats = HelperCategory.objects.filter(helpline=helper.helpline).exclude(name='Repeat')

        pending_list = []
        completed_list = []
        rejected_list = []
        to_list = []
        for month in range(1, 13):
            pending_list.append(assigns.filter((Q(action__status=ActionStatusOptions.ASSIGN_PENDING) | Q(
                                                          action__status=ActionStatusOptions.ASSIGNED)),
                                               action__created__month=month).count())
            completed_list.append(assigns.filter(action__status=ActionStatusOptions.COMPLETED,
                                                 action__created__month=month).count())
            rejected_list.append(Assign.objects.filter(action__status=ActionStatusOptions.REJECTED,
                                                       action__created__month=month).count())

            to_list.append(Assign.objects.filter(action__status=ActionStatusOptions.ASSIGN_TIMEOUT,
                                                 action__created__month=month).count())

        assigns = Assign.objects.filter(helper=helper)
        years = set()
        for assign in assigns:
            years.add(assign.created.year)

        categories = helper.category.all()
        assigned_category = ""
        try:
            if len(categories) > 1:
                for category in categories:
                    assigned_category += category.name + ", "
                assigned_category = assigned_category[:len(assigned_category) - 2]
            else:
                assigned_category = categories[0].name
        except ValueError:
            pass
        context = {
            'url': BASE_URL,
            'pk': pk,
            'helper_cats': helper_cats,
            'category_assigned': assigned_category,
            'helper': helper,
            'assigns': assigns,
            'cur_cat': cat,
            'years': years,
            'pending_list': pending_list,
            'completed_list': completed_list,
            'rejected_list': rejected_list,
            'to_list': to_list,
            'cur_year': year,
        }
        return render(request, 'helper_profile.html', context)


class Yearly_Stats(LoginRequiredMixin, View):
    login_url = '/web_auth/login/'
    redirect_field_name = 'redirect_to'

    def get(self, request, cat, year):
        user = request.user
        helper = Helper.objects.filter(user=user)
        if cat != 'All':
            assigns = Assign.objects.filter(created__year=year, action__task__category__name=cat,
                                            action__task__call_request__helpline=helper[0].helpline).order_by('created')
        else:
            assigns = Assign.objects.filter(created__year=year,
                                            action__task__call_request__helpline=helper[0].helpline).order_by('created')
        actions = set()
        for assign in assigns:
            actions.add(assign.action)
        helper_cats = HelperCategory.objects.filter(helpline=helper[0].helpline).exclude(name='Repeat')
        pen_jan, pen_feb, pen_mar, pen_apr, pen_may, pen_jun, pen_jul, pen_aug, pen_sep, pen_oct, pen_nov, pen_dec = 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
        com_jan, com_feb, com_mar, com_apr, com_may, com_jun, com_jul, com_aug, com_sep, com_oct, com_nov, com_dec = 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
        rej_jan, rej_feb, rej_mar, rej_apr, rej_may, rej_jun, rej_jul, rej_aug, rej_sep, rej_oct, rej_nov, rej_dec = 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
        to_jan, to_feb, to_mar, to_apr, to_may, to_jun, to_jul, to_aug, to_sep, to_oct, to_nov, to_dec = 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0

        for action in actions:
            if action.created.month == 1:
                if action.status == ActionStatusOptions.ASSIGN_PENDING or action.status == ActionStatusOptions.ASSIGNED:
                    pen_jan += 1
                elif action.status == ActionStatusOptions.COMPLETED:
                    com_jan += 1
                elif action.status == ActionStatusOptions.REJECTED:
                    rej_jan += 1
                elif action.status == ActionStatusOptions.ASSIGN_TIMEOUT:
                    to_jan += 1
            elif action.created.month == 2:
                if action.status == ActionStatusOptions.ASSIGN_PENDING or action.status == ActionStatusOptions.ASSIGNED:
                    pen_feb += 1
                elif action.status == ActionStatusOptions.COMPLETED:
                    com_feb += 1
                elif action.status == ActionStatusOptions.REJECTED:
                    rej_feb += 1
                elif action.status == ActionStatusOptions.ASSIGN_TIMEOUT:
                    to_feb += 1
            elif action.created.month == 3:
                if action.status == ActionStatusOptions.ASSIGN_PENDING or action.status == ActionStatusOptions.ASSIGNED:
                    pen_mar += 1
                elif action.status == ActionStatusOptions.COMPLETED:
                    com_mar += 1
                elif action.status == ActionStatusOptions.REJECTED:
                    rej_mar += 1
                elif action.status == ActionStatusOptions.ASSIGN_TIMEOUT:
                    to_mar += 1
            elif action.created.month == 4:
                if action.status == ActionStatusOptions.ASSIGN_PENDING or action.status == ActionStatusOptions.ASSIGNED:
                    pen_apr += 1
                elif action.status == ActionStatusOptions.COMPLETED:
                    com_apr += 1
                elif action.status == ActionStatusOptions.REJECTED:
                    rej_apr += 1
                elif action.status == ActionStatusOptions.ASSIGN_TIMEOUT:
                    to_apr += 1
            elif action.created.month == 5:
                if action.status == ActionStatusOptions.ASSIGN_PENDING or action.status == ActionStatusOptions.ASSIGNED:
                    pen_may += 1
                elif action.status == ActionStatusOptions.COMPLETED:
                    com_may += 1
                elif action.status == ActionStatusOptions.REJECTED:
                    rej_may += 1
                elif action.status == ActionStatusOptions.ASSIGN_TIMEOUT:
                    to_may += 1
            elif action.created.month == 6:
                if action.status == ActionStatusOptions.ASSIGN_PENDING or action.status == ActionStatusOptions.ASSIGNED:
                    pen_jun += 1
                elif action.status == ActionStatusOptions.COMPLETED:
                    com_jun += 1
                elif action.status == ActionStatusOptions.REJECTED:
                    rej_jun += 1
                elif action.status == ActionStatusOptions.ASSIGN_TIMEOUT:
                    to_jun += 1
            elif action.created.month == 7:
                if action.status == ActionStatusOptions.ASSIGN_PENDING or action.status == ActionStatusOptions.ASSIGNED:
                    pen_jul += 1
                elif action.status == ActionStatusOptions.COMPLETED:
                    com_jul += 1
                elif action.status == ActionStatusOptions.REJECTED:
                    rej_jul += 1
                elif action.status == ActionStatusOptions.ASSIGN_TIMEOUT:
                    to_jul += 1
            elif action.created.month == 8:
                if action.status == ActionStatusOptions.ASSIGN_PENDING or action.status == ActionStatusOptions.ASSIGNED:
                    pen_aug += 1
                elif action.status == ActionStatusOptions.COMPLETED:
                    com_aug += 1
                elif action.status == ActionStatusOptions.REJECTED:
                    rej_aug += 1
                elif action.status == ActionStatusOptions.ASSIGN_TIMEOUT:
                    to_aug += 1
            elif action.created.month == 9:
                if action.status == ActionStatusOptions.ASSIGN_PENDING or action.status == ActionStatusOptions.ASSIGNED:
                    pen_sep += 1
                elif action.status == ActionStatusOptions.COMPLETED:
                    com_sep += 1
                elif action.status == ActionStatusOptions.REJECTED:
                    rej_sep += 1
                elif action.status == ActionStatusOptions.ASSIGN_TIMEOUT:
                    to_sep += 1
            elif action.created.month == 10:
                if action.status == ActionStatusOptions.ASSIGN_PENDING or action.status == ActionStatusOptions.ASSIGNED:
                    pen_oct += 1
                elif action.status == ActionStatusOptions.COMPLETED:
                    com_oct += 1
                elif action.status == ActionStatusOptions.REJECTED:
                    rej_oct += 1
                elif action.status == ActionStatusOptions.ASSIGN_TIMEOUT:
                    to_oct += 1
            elif action.created.month == 11:
                if action.status == ActionStatusOptions.ASSIGN_PENDING or action.status == ActionStatusOptions.ASSIGNED:
                    pen_nov += 1
                elif action.status == ActionStatusOptions.COMPLETED:
                    com_nov += 1
                elif action.status == ActionStatusOptions.REJECTED:
                    rej_nov += 1
                elif action.status == ActionStatusOptions.ASSIGN_TIMEOUT:
                    to_nov += 1
            elif action.created.month == 12:
                if action.status == ActionStatusOptions.ASSIGN_PENDING or action.status == ActionStatusOptions.ASSIGNED:
                    pen_dec += 1
                elif action.status == ActionStatusOptions.COMPLETED:
                    com_dec += 1
                elif action.status == ActionStatusOptions.REJECTED:
                    rej_dec += 1
                elif action.status == ActionStatusOptions.ASSIGN_TIMEOUT:
                    to_dec += 1

        assigns = Assign.objects.filter(action__task__call_request__helpline=helper[0].helpline)
        years = set()
        for assign in assigns:
            years.add(assign.created.year)
        categories = HelperCategory.objects.filter(helpline=helper[0].helpline)

        cat_count = []

        for cata in categories:
            cat_assigns = Assign.objects.filter(created__year=year, action__task__category__name=cata,
                                                action__task__call_request__helpline=helper[0].helpline)
            cat_actions = set()
            for cat_assign in cat_assigns:
                cat_actions.add(cat_assign.action.task)
            cat_count.append(len(cat_actions))

        if cat != 'All':
            assigns_completed = Assign.objects.filter(created__year=year, action__task__category__name=cat,
                                                      action__task__call_request__helpline=helper[0].helpline,
                                                      action__status=ActionStatusOptions.COMPLETED)
        else:
            assigns_completed = Assign.objects.filter(created__year=year,
                                                      action__task__call_request__helpline=helper[0].helpline,
                                                      action__status=ActionStatusOptions.COMPLETED)
        total_assigns = len(assigns_completed)
        total_time = datetime.timedelta(0)
        for assign_completed in assigns_completed:
            created_date = assign_completed.created
            qanda = QandA.objects.get(task=assign_completed.action.task)
            completed_date = qanda.created
            total_time += completed_date-created_date

        try:
            average_completion_time = total_time/total_assigns
            hours, remainder = divmod(average_completion_time.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
        except ZeroDivisionError:
            hours, minutes = 0, 0

        average_completion_time = "%d hours %d mins" % (hours, minutes)

        if cat != 'All':
            assigns = Assign.objects.filter(created__year=year, action__task__category__name=cat,
                                            action__task__call_request__helpline=helper[0].helpline).order_by('created')
        else:
            assigns = Assign.objects.filter(created__year=year,
                                            action__task__call_request__helpline=helper[0].helpline).order_by('created')
        total_assigns = len(assigns)
        total_time = datetime.timedelta(0)
        for i in range(total_assigns-1):
            total_time += assigns[i+1].created - assigns[i].created

        try:
            average_assignment_time = total_time / total_assigns
            hours, remainder = divmod(average_assignment_time.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
        except ZeroDivisionError:
            hours, minutes = 0, 0
        average_assignment_time = "%d hours %d mins" % (hours, minutes)

        task_dict = dict()
        for assign in assigns:
            try:
                task_dict[assign.created.date()] += 1
            except KeyError:
                task_dict[assign.created.date()] = 1

        values = task_dict.values()
        try:
            max_tasks = max(values)
            min_tasks = min(values)
            avg_tasks = sum(values)/len(values)
        except ValueError:
            max_tasks = 0
            min_tasks = 0
            avg_tasks = 0

        context = {
            'url': BASE_URL,
            'helper': helper[0],
            'years': years,
            'helper_cats': helper_cats,
            'cur_year': year,
            'cur_cat': cat,
            'cat_count': cat_count,
            'average_completion_time': average_completion_time,
            'average_assignment_time': average_assignment_time,
            'max_tasks': max_tasks,
            'min_tasks': min_tasks,
            'avg_tasks': avg_tasks,
            'pen_jan': pen_jan,
            'pen_feb': pen_feb,
            'pen_mar': pen_mar,
            'pen_apr': pen_apr,
            'pen_may': pen_may,
            'pen_jun': pen_jun,
            'pen_jul': pen_jul,
            'pen_aug': pen_aug,
            'pen_sep': pen_sep,
            'pen_oct': pen_oct,
            'pen_nov': pen_nov,
            'pen_dec': pen_dec,
            'com_jan': com_jan,
            'com_feb': com_feb,
            'com_mar': com_mar,
            'com_apr': com_apr,
            'com_may': com_may,
            'com_jun': com_jun,
            'com_jul': com_jul,
            'com_aug': com_aug,
            'com_sep': com_sep,
            'com_oct': com_oct,
            'com_nov': com_nov,
            'com_dec': com_dec,
            'rej_jan': rej_jan,
            'rej_feb': rej_feb,
            'rej_mar': rej_mar,
            'rej_apr': rej_apr,
            'rej_may': rej_may,
            'rej_jun': rej_jun,
            'rej_jul': rej_jul,
            'rej_aug': rej_aug,
            'rej_sep': rej_sep,
            'rej_oct': rej_oct,
            'rej_nov': rej_nov,
            'rej_dec': rej_dec,
            'to_jan': to_jan,
            'to_feb': to_feb,
            'to_mar': to_mar,
            'to_apr': to_apr,
            'to_may': to_may,
            'to_jun': to_jun,
            'to_jul': to_jul,
            'to_aug': to_aug,
            'to_sep': to_sep,
            'to_oct': to_oct,
            'to_nov': to_nov,
            'to_dec': to_dec,
        }
        return render(request, 'stats_year.html', context)


class Monthly_Stats(LoginRequiredMixin, View):
    login_url = '/web_auth/login/'
    redirect_field_name = 'redirect_to'

    def get(self, request, cat, month, year):
        user = request.user
        helper = Helper.objects.filter(user=user)
        month_list = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        cur_month = month_list.index(month)+1

        if cat != 'All':
            #assigns = Assign.objects.filter(created__month=cur_month, created__year=year,
            #                                action__task__category__name=cat,
            #                                action__task__call_request__helpline=helper[0].helpline)
            actions = Action.objects.filter(created__month=cur_month, created__year=year,
                                            task__category__name=cat,
                                            task__call_request__helpline=helper[0].helpline)
        else:
            #assigns = Assign.objects.filter(created__month=cur_month, created__year=year,
            #                                action__task__call_request__helpline=helper[0].helpline)
            actions = Action.objects.filter(created__month=cur_month, created__year=year,
                                            task__call_request__helpline=helper[0].helpline)
        #actions = set()
        #for assign in assigns:
        #    actions.add(assign.action)
        helper_cats = HelperCategory.objects.filter(helpline=helper[0].helpline).exclude(name='Repeat')
        pen_week1, pen_week2, pen_week3, pen_week4, pen_week5 = 0, 0, 0, 0, 0
        com_week1, com_week2, com_week3, com_week4, com_week5 = 0, 0, 0, 0, 0
        rej_week1, rej_week2, rej_week3, rej_week4, rej_week5 = 0, 0, 0, 0, 0
        to_week1, to_week2, to_week3, to_week4, to_week5 = 0, 0, 0, 0, 0

        for action in actions:
            if 1 <= action.created.day <= 7:
                if action.status == ActionStatusOptions.ASSIGN_PENDING or action.status == ActionStatusOptions.ASSIGNED:
                    pen_week1 += 1
                elif action.status == ActionStatusOptions.COMPLETED:
                    com_week1 += 1
                elif action.status == ActionStatusOptions.REJECTED:
                    rej_week1 += 1
                elif action.status == ActionStatusOptions.ASSIGN_TIMEOUT:
                    to_week1 += 1
            elif 8 <= action.created.day <= 14:
                if action.status == ActionStatusOptions.ASSIGN_PENDING or action.status == ActionStatusOptions.ASSIGNED:
                    pen_week2 += 1
                elif action.status == ActionStatusOptions.COMPLETED:
                    com_week2 += 1
                elif action.status == ActionStatusOptions.REJECTED:
                    rej_week2 += 1
                elif action.status == ActionStatusOptions.ASSIGN_TIMEOUT:
                    to_week2 += 1
            elif 15 <= action.created.day <= 21:
                if action.status == ActionStatusOptions.ASSIGN_PENDING or action.status == ActionStatusOptions.ASSIGNED:
                    pen_week3 += 1
                elif action.status == ActionStatusOptions.COMPLETED:
                    com_week3 += 1
                elif action.status == ActionStatusOptions.REJECTED:
                    rej_week3 += 1
                elif action.status == ActionStatusOptions.ASSIGN_TIMEOUT:
                    to_week3 += 1
            elif 22 <= action.created.day <= 28:
                if action.status == ActionStatusOptions.ASSIGN_PENDING or action.status == ActionStatusOptions.ASSIGNED:
                    pen_week4 += 1
                elif action.status == ActionStatusOptions.COMPLETED:
                    com_week4 += 1
                elif action.status == ActionStatusOptions.REJECTED:
                    rej_week4 += 1
                elif action.status == ActionStatusOptions.ASSIGN_TIMEOUT:
                    to_week4 += 1
            elif 29 <= action.created.day <= 31:
                if action.status == ActionStatusOptions.ASSIGN_PENDING or action.status == ActionStatusOptions.ASSIGNED:
                    pen_week5 += 1
                elif action.status == ActionStatusOptions.COMPLETED:
                    com_week5 += 1
                elif action.status == ActionStatusOptions.REJECTED:
                    rej_week5 += 1
                elif action.status == ActionStatusOptions.ASSIGN_TIMEOUT:
                    to_week5 += 1

        assigns = Assign.objects.filter(action__task__call_request__helpline=helper[0].helpline)
        years = set()
        for assign in assigns:
            years.add(assign.created.year)

        categories = HelperCategory.objects.filter(helpline=helper[0].helpline)

        cat_count=[]
        for cata in categories:
            cat_assigns = Assign.objects.filter(created__month=cur_month, created__year=year,
                                                action__task__category__name=cata,
                                                action__task__call_request__helpline=helper[0].helpline)
            cat_actions = set()
            for cat_assign in cat_assigns:
                cat_actions.add(cat_assign.action.task)
            cat_count.append(len(cat_actions))

        if cat != 'All':
            assigns_completed = Assign.objects.filter(created__month=cur_month,created__year=year,
                                                      action__task__category__name=cat,
                                                      action__task__call_request__helpline=helper[0].helpline,
                                                      action__status=ActionStatusOptions.COMPLETED)
        else:
            assigns_completed = Assign.objects.filter(created__month=cur_month,created__year=year,
                                                      action__task__call_request__helpline=helper[0].helpline,
                                                      action__status=ActionStatusOptions.COMPLETED)
        try:
            total_assigns = len(assigns_completed)
            total_time = datetime.timedelta(0)
            for assign_completed in assigns_completed:
                created_date = assign_completed.created
                qanda = QandA.objects.get(task=assign_completed.action.task)
                completed_date = qanda.created
                total_time += completed_date - created_date
            average_completion_time = total_time / total_assigns
            hours, remainder = divmod(average_completion_time.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            average_completion_time = "%d hours %d mins" % (hours, minutes)
        except ZeroDivisionError:
            average_completion_time = "%d hours %d mins" % (0, 0)

        if cat != 'All':
            assigns = Assign.objects.filter(created__month=cur_month,created__year=year, action__task__category__name=cat,
                                            action__task__call_request__helpline=helper[0].helpline).order_by('created')

        else:
            assigns = Assign.objects.filter(created__month=cur_month,created__year=year,
                                            action__task__call_request__helpline=helper[0].helpline).order_by('created')
        try:
            total_assigns = len(assigns)
            total_time = datetime.timedelta(0)
            for i in range(total_assigns - 1):
                total_time += assigns[i + 1].created - assigns[i].created
            average_assignment_time = total_time / total_assigns
            hours, remainder = divmod(average_assignment_time.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            average_assignment_time = "%d hours %d mins" % (hours, minutes)
        except:
            average_assignment_time = "%d hours %d mins" % (0, 0)

        task_dict = dict()
        for assign in assigns:
            try:
                task_dict[assign.created.date()] += 1
            except:
                task_dict[assign.created.date()] = 1

        values = task_dict.values()
        try:
            max_tasks = max(values)
        except:
            max_tasks = 0
        try:
            min_tasks = min(values)
        except:
            min_tasks = 0
        try:
            avg_tasks = sum(values) / len(values)
        except:
            avg_tasks = 0
        context = {
            'url': BASE_URL,
            'helper': helper[0],
            'years': years,
            'helper_cats': helper_cats,
            'cur_year': year,
            'cur_month': month,
            'cur_cat' : cat,
            'average_completion_time': average_completion_time,
            'average_assignment_time': average_assignment_time,
            'max_tasks': max_tasks,
            'min_tasks': min_tasks,
            'avg_tasks': avg_tasks,
            'cat_count': cat_count,
            'pen_week1': pen_week1,
            'pen_week2': pen_week2,
            'pen_week3': pen_week3,
            'pen_week4': pen_week4,
            'pen_week5': pen_week5,
            'com_week1': com_week1,
            'com_week2': com_week2,
            'com_week3': com_week3,
            'com_week4': com_week4,
            'com_week5': com_week5,
            'rej_week1': rej_week1,
            'rej_week2': rej_week2,
            'rej_week3': rej_week3,
            'rej_week4': rej_week4,
            'rej_week5': rej_week5,
            'to_week1': to_week1,
            'to_week2': to_week2,
            'to_week3': to_week3,
            'to_week4': to_week4,
            'to_week5': to_week5,
        }
        return render(request, 'stats_month.html', context)


class Task_Details(LoginRequiredMixin, View):
    login_url = '/web_auth/login/'
    redirect_field_name = 'redirect_to'

    def get(self, request, pk):
        user = request.user
        helper = Helper.objects.filter(user=user)
        helpers = Helper.objects.filter()
        task = Task.objects.get(id=pk)
        call_forward = Call_Forward_Details.objects.filter(task=task).order_by('-created')
        feedback = None
        try:
            feedback = QandA.objects.filter(task=task)[0]
        except:
            pass
        assigns = Assign.objects.filter(action__task=task).exclude(status=AssignStatusOptions.REJECTED).exclude(status=AssignStatusOptions.TIMEOUT)
        actions = Action.objects.filter(task=task).exclude(status = ActionStatusOptions.REJECTED)
        for action in actions:
            if action.status == ActionStatusOptions.ASSIGN_PENDING:
                status="Pending"
            if action.status == ActionStatusOptions.ASSIGNED:
                for assign in assigns:
                    if assign.status == AssignStatusOptions.REALLOCATED:
                        status = "Reallocated"
                    else:
                        status = "Accepted"
            if action.status == ActionStatusOptions.COMPLETED:
                status="Completed"
        helper_name = ""
        prev_helpers = TaskHistory.objects.filter(task=task).order_by('reallocateDate')
        if len(assigns) > 1:
            for assign in assigns:
                helper_name += assign.helper.user.first_name+" "+assign.helper.user.last_name+", "
            helper_name = helper_name[:len(helper_name)-2]
        elif len(assigns) == 1:
            helper_name = assigns[0].helper.user.first_name + " " + assigns[0].helper.user.last_name
        else:
            helper_name = ""
        context = {
            'helper': helper[0],
            'helpers':helpers,
            'call_forward': call_forward,
            'task': task,
            'prev_helpers':prev_helpers,
            'status': status,
            'feedback': feedback,
            "helper_name": helper_name
        }
        return render(request, 'task_details.html', context)

class BulkHelperRegistration(LoginRequiredMixin, View):
    login_url = '/web_auth/login/'
    redirect_field_name = 'redirect_to'

    def get(self, request):
        helper = Helper.objects.get(user=request.user)
        return render(request, 'bulk_registration.html', {'helper':helper})

    def post(self, request):
        try:
            print('before')
            csv_file = request.FILES['csvfile']
            #dialect = csv.Sniffer().sniff(codecs.EncodedFile(csv_file, "utf-8").read(1024))
            
            htmltext = csv_file.read().decode('utf-8')
            print(htmltext)

            f = StringIO(htmltext)
            reader = csv.reader(f, delimiter=",")
            for row in reader:
                if row:
                    username = row[0]
                    first_name = row[1]
                    #last_name = row[2]
                    #email = row[2]
                    phone_no = row[2]
                    helpline = row[3]
                    password = make_password(row[4])
                    user = User(username=username, first_name=first_name, password=password)
                    #user = User(username=username, first_name=first_name, last_name=last_name, email=email)
                    print('Here')
                    user.save()
                    print('Done user')
                    helpline = HelpLine.objects.get(name=helpline)
                    helper = Helper(user=user, helpline=helpline, helper_number=phone_no,
                                login_status=LoginStatus.LOGGED_OUT,login_prevstatus=LoginStatus.LOGGED_OUT,
                                level=HelperLevel.PRIMARY)
                    helper.save()
                    #category = HelperCategory.objects.get(name="2-1")
                    language = Language.objects.get(language="English")
                    #helper.category.add(category)
                    helper.language.add(language)
                    
                    print('Done helper')
                #forgot_password = Forgot_Password(user=user)
                #forgot_password.save()
                #body = "Click on the link to reset password" + BASE_URL + "auth/reset_password/" + str(
                #    forgot_password.id) + "/"
                #email_to(recipient=user.email, subject="Password Reset", body=body, files=None)
            return render(request, 'bulk_registration.html', {'message': 'Registration Success'})
        except Exception as e:
            trace_back = traceback.format_exc()
            message = str(e)+ " " + str(trace_back)
            print(message)
            return render(request, 'bulk_registration.html', {'message': 'Registration Failed'})

class DoctorSlots(LoginRequiredMixin, View):
    login_url = '/web_auth/login/'
    redirect_field_name = 'redirect_to'

    def get(self, request):
        helper = Helper.objects.get(user=request.user)
        return render(request, 'doctor_slots.html', {'helper':helper})

    def post(self, request):
        try:
            print('before')
            csv_file = request.FILES['csvfile']
            #dialect = csv.Sniffer().sniff(codecs.EncodedFile(csv_file, "utf-8").read(1024))
            
            # htmltext = csv_file.read().decode('utf-8')
            # print(htmltext)

            file_data = csv_file.read().decode("utf-8")		
 
            lines = file_data.split("\n")
            doctor_id, doctor_name = "", ""#reader[0].split(',')
            for line in lines:
                print(line)
                
                # if line:
                if doctor_id == "":
                    doctor_id, doctor_name = line.split(',')[0].strip(), line.split(',')[1].strip()
                    continue
                fields = line.split(',')
                data_dict = {}
                data_dict["slot_date"] = datetime.datetime.strptime(str(fields[0]), "%Y-%m-%d").date()
                data_dict["slot_start_times"] = fields[1]
                # print(data_dict)
                # print(type(data_dict["slot_date"]))
                
                obj = DoctorAvailableSlot.objects.filter(slot_date=data_dict["slot_date"], doctor_name=doctor_name)
                # print(len(obj))
                if len(obj) > 0:
                    # print(obj[0])
                    obj[0].slot_start_times = data_dict["slot_start_times"]
                    obj[0].save()
                    # print(obj[0])
                else:
                    new_slot = DoctorAvailableSlot(doctor_id=doctor_id, doctor_name=doctor_name, slot_date=data_dict["slot_date"], slot_start_times=data_dict["slot_start_times"])
                    new_slot.save()
            # f.close()

            return render(request, 'doctor_slots.html', {'message': 'Upload Successful'})
        except Exception as e:
            trace_back = traceback.format_exc()
            message = str(e)+ " " + str(trace_back)
            print(message)
            return render(request, 'doctor_slots.html', {'message': 'Upload Failed'})


class tag_list(LoginRequiredMixin, View):
    login_url = '/web_auth/login/'
    redirect_field_name = 'redirect_to'

    def get(self, request):
        return render(request, 'tag_list.html')

    def post(self, request):
        try:
            print('before')
            csv_file = request.FILES['csvfile']
            #dialect = csv.Sniffer().sniff(codecs.EncodedFile(csv_file, "utf-8").read(1024))
            
            tag_list = Tag_List.objects.filter().delete();
            htmltext = csv_file.read().decode('utf-8')
            print(htmltext)
            f = StringIO(htmltext)
            reader = csv.reader(f, delimiter="*")
            for row in reader:
                if row:
                    tag = Tag_List.objects.create(tag = row[0])
                    tag.save()
            tag_list = Tag_List.objects.all().values('tag');
            print(tag_list)
            return render(request, 'tag_list.html', {'message': 'Update Success'})
        except Exception as e:
            trace_back = traceback.format_exc()
            message = str(e)+ " " + str(trace_back)
            print(message)
            return render(request, 'tag_list.html', {'message': 'Update Failed'})


class Create_Survey(LoginRequiredMixin, View):
    login_url = '/web_auth/login/'
    redirect_field_name = 'redirect_to'

    def get(self, request):
        helper = Helper.objects.get(user=request.user)
        return render(request, 'create_survey.html', {'helper':helper})

    def post(self, request):
        try:
            csv_file = request.FILES['csv_file']
            google_form_url = request.POST["form_url_field"]
            response_csv_url = request.POST["response_url_field"]
            print("FORM URL: ", google_form_url)
            print("CSV URL: ", response_csv_url)
            if "google.com/forms" not in google_form_url:
                return render(request, 'create_survey.html', {'message': 'The Form URL was incorrect.'})

            if "google.com/spreadsheets" not in response_csv_url:
                return render(request, 'create_survey.html', {'message': 'The CSV URL was incorrect.'})


            response = urlopen(google_form_url)
            print(" RESPONSE CODE: ", response.getcode())
            if not (200 <= response.getcode() <= 299):
                return render(request, 'create_survey.html', {'message': 'The Form URL was incorrect.'})

            csv_response = urlopen(response_csv_url)
            print(" RESPONSE CODE: ", csv_response.getcode())
            if not (200 <= csv_response.getcode() <= 299):
                return render(request, 'create_survey.html', {'message': 'The CSV URL was incorrect.'})

            soup = BeautifulSoup(response.read(), "html.parser")
            survey_title = soup.find('title')
            survey = Survey.objects.filter(google_form_url=google_form_url)
            #if survey:
            #    print("SURVEY EXISTS")
            #    return render(request, 'create_survey.html', {'message': 'Survey with this Url already exists.'})

            reader = csv_file.read().decode('utf-8').split("\n")      #Load csv
            if len(request.FILES) != 0:
                url = response_csv_url[0:response_csv_url.find('/edit?')] + '/export?format=csv'
                response = urlretrieve(url)
                print("response")
                print(response)
                contents = open(response[0]).read()
                print(contents)
                f = open('google_response.csv','w')
                f.write(contents)
                f.close()
                print(f)
                survey = Survey.objects.create(name=survey_title.string, google_form_url=google_form_url, response_csv_url=response_csv_url, number_of_people=len(reader)-1,initial_csv = csv_file, google_response_csv = File(open('google_response.csv')))
                
            print("NEW SURVEY CREATED: ", survey_title.string, google_form_url)

            for row in reader[1:]:
                if any(row):
                    fields = row.split(",")
                    print("Row: ", row)
                    client_name = fields[0]
                    client_number = fields[1]
                    client_number = self.fetch_number(client_number)
                    print("number: ", client_number)
                    # Trying to get client instance and if doesn't exist, create one
                    try:
                        client = Client.objects.get(client_number=client_number)
                    except Client.DoesNotExist:
                        client = Client.objects.create(name=client_name, client_number=client_number)
                        print("CREATED NEW CLIENT", client_name, client_number)
                    try:
                        prev_task = SurveyTask.objects.filter(client = client, status = "completed" , survey__google_form_url = google_form_url, edit_form_url__isnull=False)
                        pending_task = SurveyTask.objects.filter(client = client, status = "assigned" , survey__google_form_url = google_form_url) | SurveyTask.objects.filter(client = client, status = "pending" , survey__google_form_url = google_form_url)
                        if prev_task:
                            first = prev_task.first()
                            edit_form = first.edit_form_url
                            survey_task = SurveyTask.objects.create(survey=survey, client=client, edit_form_url=edit_form)
                        elif pending_task:
                            print("pending task exists for" + client_number)
                        else:
                            survey_task = SurveyTask.objects.create(survey=survey, client=client)
                    except Exception as e:
                        print("Survey task could not be created")
                    print("NEW SURVEY TASK CREATED for ", client.name)

            return render(request, 'create_survey.html', {'message': 'Survey created successfully'})
        except Exception as e:
            return render(request, 'create_survey.html', {'message': 'Survey creation failed'+str(e)})

    def fetch_number(self, url_number):
        contact = url_number.strip()
        if len(contact) > 10:
            contact = contact[len(contact) - 10:]

        try:
            contact_num = int(contact)
        except ValueError:
            print('Number is invalid !!')

        return str(contact_num)

class Update_Survey_Users(LoginRequiredMixin, View):
    login_url = '/web_auth/login/'
    redirect_field_name = 'redirect_to'

    def get(self, request, pk):
        user = request.user
        helper = Helper.objects.filter(user=user)
        helpers = Helper.objects.filter()
        survey = Survey.objects.get(id=pk)
        print("get")
        print(survey.id)

        context = {
             'survey_id': survey.id,
        }
        return render(request, 'update_survey_users.html', context)


    def post(self, request, pk):
        try:
            csv_file = request.FILES['csv_file']
            survey = Survey.objects.get(id=pk)
            print("post")
            print(survey.id)
            #if survey:
            #    print("SURVEY EXISTS")
            #    return render(request, 'update_survey_users', {'message': 'Survey with this Url already exists.'})

            reader = csv_file.read().decode('utf-8').split("\n")      #Load csv
            survey.number_of_people = survey.number_of_people + (len(reader)-1)
            survey.save()

            #survey = Survey.objects.create(name=survey_title.string, google_form_url=google_form_url, response_csv_url=response_csv_url, number_of_people=len(reader)-1)
            #print("NEW SURVEY CREATED: ", survey_title.string, google_form_url)

            for row in reader[1:]:
                if any(row):
                    fields = row.split(",")
                    print("Row: ", row)
                    client_name = fields[0]
                    client_number = fields[1]
                    print(client_name)
                    print(client_number)
                    client_number = self.fetch_number(client_number)
                    print("number: ", client_number)
                    # Trying to get client instance and if doesn't exist, create one
                    try:
                        client = Client.objects.get(client_number=client_number)
                    except Client.DoesNotExist:
                        client = Client.objects.create(name=client_name, client_number=client_number)
                        print("CREATED NEW CLIENT", client_name, client_number)
                    try:
                        prev_task = SurveyTask.objects.filter(client = client, status = "completed" ,survey=survey, edit_form_url__isnull=False)
                        pending_task = SurveyTask.objects.filter(client = client, status = "assigned" ,survey=survey) | SurveyTask.objects.filter(client = client, status = "pending" , survey=survey)
                        initial_csv = survey.initial_csv
                        if prev_task:
                            first = prev_task.first()
                            edit_form = first.edit_form_url
                            survey_task = SurveyTask.objects.create(survey=survey, client=client, edit_form_url=edit_form)
                            print("NEW SURVEY TASK CREATED for ", client.name)

                        elif pending_task:
                            print("pending task exists for" + client_number)
                        else:
                            survey_task = SurveyTask.objects.create(survey=survey, client=client)
                            for line in csv_file:
                                initial_csv.write(line)
                            survey.initialcsv = initial_csv
                            print("NEW SURVEY TASK CREATED for ", client.name)
                    except Exception as e:
                        print("Survey task could not be created")


            survey=Survey.objects.get(id=pk)
            context = {
             'survey_id': survey.id,
             'message': 'Survey created successfully',
            }
            return render(request, 'update_survey_users.html',context)
        except Exception as e:
            survey=Survey.objects.get(id=pk)
            context = {
             'survey_id': survey.id,
             'message': 'Survey creation failed'+str(e),
            }
            return render(request, 'update_survey_users.html', context)

    def fetch_number(self, url_number):
        contact = url_number.strip()
        if len(contact) > 10:
            contact = contact[len(contact) - 10:]

        try:
            contact_num = int(contact)
        except ValueError:
            print('Number is invalid !!')

        return str(contact_num)


class Create_Tasks(LoginRequiredMixin, View):
    login_url = '/web_auth/login/'
    redirect_field_name = 'redirect_to'

    def get(self, request):
        helper = Helper.objects.get(user=request.user)
        return render(request, 'create_tasks.html', {'helper':helper})

    def post_data(self, url, data):
        base_url = BASE_URL  # "http://vmocsh.cse.iitb.ac.in/nutrition/"
        #base_url = 'http://vmocsh.cse.iitb.ac.in:9030/hospital/'
        authentication = (USERNAME, PASSWORD)
        print("IVR post data")
        headers = {'Content-type': 'application/json'}
        resp = requests.post(base_url + url, data=json.dumps(data), headers=headers, auth=authentication, verify=True)
        print("Register call post response: ", resp.status_code)


    def post(self, request):
        try:
            
            #csv_file = request.FILES['csv_file']
            text = request.POST["Text"]
            print(text)
            print(type(text))
            for row in text.split('\n'):
                if any(row):
                    fields = row.split(",")
                    print("Row: ", row)
                    #client_name = fields[0]
                    client_number = fields[0]
                    client_number = self.fetch_number(client_number)
                    print("number: ", client_number)

                    try:
                        helpline = HelpLine.objects.first();
                        data = {
                            "client_number": client_number,
                            "helpline_number": helpline.helpline_number,
                            "location": "Default",
                            "category": "Default",
                            "language": "Hindi",
                            "task_type": "Indirect"
                        }
                        print('Task is being created with :', data)
                        self.post_data("registercall/", data)
                    except Exception as e:
                        print('Failed to upload to ftp: '+ str(e))
                        print("task could not be created")
                        return render(request, 'create_tasks.html', {'message': 'Tasks creation failed'+str(e)})
                
            #reader = csv_file.read().decode('utf-8').split("\n")      #Load csv
            #survey = Survey.objects.create(name=survey_title.string, google_form_url=google_form_url, response_csv_url=response_csv_url, number_of_people=len(reader)-1)
            
            """
            for row in reader[1:]:
                if any(row):
                    fields = row.split(",")
                    print("Row: ", row)
                    #client_name = fields[0]
                    client_number = fields[0]
                    client_number = self.fetch_number(client_number)
                    print("number: ", client_number)
                    # Trying to get client instance and if doesn't exist, create one
                    #try:
                    #    client = Client.objects.get(client_number=client_number)
                    #except Client.DoesNotExist:
                    #    client = Client.objects.create(name=client_name, client_number=client_number)
                    #    print("CREATED NEW CLIENT", client_name, client_number)
                    #          "sub_category": "",              

                    try:
                        helpline = HelpLine.objects.first();
                        data = {
                            "client_number": client_number,
                            "helpline_number": helpline.helpline_number,
                            "location": "Default",
                            "category": "Default",
                            "language": "Hindi",
                            "task_type": "Indirect"
                        }
                        print('Task is being created with :', data)
                        self.post_data("registercall/", data)
                    except Exception as e:
                        print('Failed to upload to ftp: '+ str(e))
                        print("task could not be created")
                        return render(request, 'create_tasks.html', {'message': 'Tasks creation failed'+str(e)})
            """

            return render(request, 'create_tasks.html', {'message': 'Tasks created successfully'})
        except Exception as e:
            print('Failed to upload to ftp: '+ str(e))
            return render(request, 'create_tasks.html', {'message': 'Tasks creation failed'+str(e)})

    def fetch_number(self, url_number):
        contact = url_number.strip()
        if len(contact) > 10:
            contact = contact[len(contact) - 10:]

        try:
            contact_num = int(contact)
        except ValueError:
            print('Number is invalid !!')

        return str(contact_num)


class view_surveys(LoginRequiredMixin, View):
    login_url = '/web_auth/login/'
    redirect_field_name = 'redirect_to'

    def get(self, request):
        surveys = Survey.objects.all()
        print("no_of_surveys: ", len(surveys))
        #url = response_csv_url[0:response_csv_url.find('/edit?')] + '/export?format=csv'
        #response = urlretrieve(url)
        #contents = open(response[0]).read()
        #f = open('google_response.csv','w')
        #f.write(contents)
        #f.close()
        #print(f)

        context = {
            'url': BASE_URL,
            'surveys': surveys,
        }
        return render(request, "view_surveys.html", context)


class combined_csv(LoginRequiredMixin, View):
    login_url = '/web_auth/login/'
    redirect_field_name = 'redirect_to'

    def get(self, request):
        pk = int(request.GET['survey_id'])
        survey = Survey.objects.get(pk=pk)
        url = survey.response_csv_url[0:survey.response_csv_url.find('/edit?')] + '/export?format=csv'
        response = urlretrieve(url)
        contents = open(response[0]).read()
        f1 = open('google_response.csv','w')
        f1.write(contents)
        f1.close()        
        input_df = pd.read_csv('google_response.csv')
        df = pd.read_csv(survey.initial_csv.path)
        print(input_df)
        print(df)
        df['Mobile Number'] = df['Mobile Number'].astype(str)
        input_df['Mobile Number'] = input_df['Mobile Number'].astype(str)
        output_df = input_df.merge(df, how='left', on='Mobile Number')
        output_df.to_csv('result.csv')
        return FileResponse(open('result.csv','rb'))

class Survey_Users(LoginRequiredMixin, View):
    login_url = '/web_auth/login/'
    redirect_field_name = 'redirect_to'

    def get(self, request, pk):
        user = request.user
        helper = Helper.objects.filter(user=user)
        helpers = Helper.objects.filter()
        survey = Survey.objects.get(id=pk)
        surveytasks = SurveyTask.objects.filter(survey=survey).order_by('id')
        context = {
             'url': BASE_URL,
             'surveytasks': surveytasks,
             'survey': survey,
        }
        return render(request, 'survey_details.html', context)

class DeleteHelper(LoginRequiredMixin, View):
    login_url = '/web_auth/login/'
    redirect_field_name = 'redirect_to'

    def get(self, request, pk):
        helper = Helper.objects.get(pk=pk)
        helper.user.delete()
        return HttpResponseRedirect(reverse('dashboard:home'))


class QandA_Category(LoginRequiredMixin, View):
    login_url = '/web_auth/login/'
    redirect_field_name = 'redirect_to'

    def get(self, request, cat):
        helper = Helper.objects.get(user=request.user)
        if cat !='All':
            qandas = QandA.objects.filter(task__category__name=cat)
        else:
            qandas = QandA.objects.all()
        helper_cats = HelperCategory.objects.filter(helpline=helper.helpline).exclude(name='Repeat')
        context = {
            'url': BASE_URL,
            'helper': helper,
            'cur_cat': cat,
            "qandas": qandas,
            "helper_cats": helper_cats,
        }
        return render(request, "qanda.html", context)

def AddTaskDashboard(request):
    form = AddTask(request.POST or None, request.FILES or None)
    if request.method =='POST': 
    
                if form.is_valid(): 
                    form.save()
                    form = AddTask()   
                else :
                    print(form.errors) 
    return render(request,'input.html',{ 'form':form })

