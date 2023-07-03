from django.test import TestCase, RequestFactory
from rest_framework.test import APIRequestFactory
from rest_framework import status
from rest_framework.test import APITestCase
from management.models import HelpLine, HelperCategory, HelplineSetting
from django.contrib.auth.models import AnonymousUser, User
from register_helper.models import Helper
from ivr.models import Language
from registercall.views import RegisterCall
from registercall.models import Task
from task_manager.models import Assign, Action
from register_helper.options import LoginStatus
from register_client.models import Client
import json
from .views import NoteView


class NotesTestCase(APITestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='chirag', email='chirag.holmes@gmail.com', password='chirag@28')

        help = HelpLine()
        help.name = "IITB Helpline"
        help.helpline_number = "1234"
        help.helpline_tollfree_number = "1234"
        help.save()

        lg1 = Language()
        lg1.language = 'English'
        lg1.helpline = help
        lg1.save()

        lg2 = Language()
        lg2.language = 'Hindi'
        lg2.helpline = help
        lg2.save()

        lg3 = Language()
        lg3.language = 'Marathi'
        lg3.helpline = help
        lg3.save()

        hcat1 = HelperCategory()
        hcat1.helpline = help
        hcat1.name = '12yearsabove'
        hcat1.save()

        hcat2 = HelperCategory()
        hcat2.helpline = help
        hcat2.name = '12yearsbelow'
        hcat2.save()

        hcat3 = HelperCategory()
        hcat3.helpline = help
        hcat3.name = 'general'
        hcat3.save()

        hset = HelplineSetting()
        hset.helpline = help
        hset.reminder_time = 1
        hset.reassignment_time = 3
        hset.save()

        h1 = Helper()
        h1.user = self.user
        h1.helpline = help
        h1.save()
        h1.category.add(hcat1)
        h1.category.add(hcat2)
        h1.category.add(hcat3)
        h1.language.add(lg1)
        h1.language.add(lg2)
        h1.language.add(lg3)
        h1.helper_number = "8866879841"
        h1.gender = 'Male'
        h1.college_name = 'IITB'
        h1.login_status = LoginStatus.LOGGED_IN
        h1.save()
        request = self.factory.post('/demo/registerhelper', {
            "client_number": "9898751717",
            "helpline_number": "1234",
            "location": "Ahmedabad",
            "category": "12yearsabove",
            "language": "English",
            "task_type": "non_direct"
        }, format='json')
        response = RegisterCall.as_view()(request)

    def test_create_note(self):
        task = Task.objects.first()
        helper = Helper.objects.filter(helper_number='8866879841').first()
        client = Client.objects.filter(client_number='9898751717').first()
        request = self.factory.post('/demo/api/notes/',
                                    {'task_id': task.id, 'client_id': client.client_number, 'helper_id': helper.helper_number,
                                     'text': 'test note'},
                                    format='json')
        response = NoteView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
