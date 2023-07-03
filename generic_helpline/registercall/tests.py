"""
Script for register call test cases
"""
import json

from django import test
from django.utils.six import BytesIO
from rest_framework.parsers import JSONParser

from .models import CallRequest, Client, HelpLine, Task


class RegisterCallTest(test.TestCase):
    """
    Testing Class
    """
    url = '/RegisterCall/'

    def setUp(self):
        """
        Setup Database
        """
        HelpLine.objects.create(name="General", helpline_number="+919423689096")

        # Blocked client creation
        client = Client.objects.create(client_number="+919444870256")
        client.status = 2
        client.save()

        # Creating prior task for Merging task later
        client = Client.objects.create(client_number="+918888888888")
        call_request = CallRequest.objects.create(
            helpline=HelpLine.objects.get(helpline_number="+919423689096"),
            client=client,
        )
        Task.objects.create(call_request=call_request)

    def create_register_request(self, client_number, helpline_number="+919423689096",
                                content_type="application/json"):
        """
        Creates register requests
        """
        response = self.client.post(
            self.url,
            json.dumps({'helpline_number': helpline_number, 'client_number': client_number}),
            content_type=content_type,
        )
        return response

    def test_new_task(self):
        """
        New task creation request
        """
        response = self.create_register_request(client_number='+912222222222')
        stream = BytesIO(response.content)
        data = JSONParser().parse(stream)

        self.assertEqual(data.get("notification"), "new_task_created")
        self.assertEqual(response.status_code, 201)

    def test_new_task2(self):
        """
        New task creation request
        """
        response = self.create_register_request(client_number='+914428140517')
        stream = BytesIO(response.content)
        data = JSONParser().parse(stream)

        self.assertEqual(data.get("notification"), "new_task_created")
        self.assertEqual(response.status_code, 201)

    def test_blocked_client(self):
        """
        Blocked client
        """
        response = self.create_register_request(client_number='+919444870256')
        stream = BytesIO(response.content)
        data = JSONParser().parse(stream)
        self.assertEqual(data.get("notification"), "client_blocked")
        self.assertEqual(response.status_code, 406)

    def test_merged_task(self):
        """
        Merged Task
        """
        response = self.create_register_request(client_number='+918888888888')
        stream = BytesIO(response.content)
        data = JSONParser().parse(stream)
        self.assertEqual(data.get("notification"), "merged_with_pending_task")
        self.assertEqual(response.status_code, 202)

    def test_empty_helpline(self):
        """
        Empty helpline number
        """
        response = self.create_register_request(client_number='+918888888888', helpline_number='')
        stream = BytesIO(response.content)
        data = JSONParser().parse(stream)
        self.assertEqual(data.get("notification"), "bad_request")
        self.assertEqual(response.status_code, 400)

    def test_invalid_helpline(self):
        """
        Invalid Helpline Number
        """
        response = self.create_register_request(
            client_number='+918888888888',
            helpline_number='+919423666666',
        )
        stream = BytesIO(response.content)
        data = JSONParser().parse(stream)
        self.assertEqual(data.get("notification"), "invalid_helpline")

    def test_empty_client(self):
        """
        Empty client number
        """
        response = self.create_register_request(client_number='')
        stream = BytesIO(response.content)
        data = JSONParser().parse(stream)
        self.assertEqual(data.get("notification"), "bad_request")
        self.assertEqual(response.status_code, 400)

    def test_invalid_content_type(self):
        """
        Invalid Content type
        """
        response = self.create_register_request(
            client_number='+918888888888',
            content_type='application/xml',
        )
        stream = BytesIO(response.content)
        data = JSONParser().parse(stream)
        self.assertEqual(
            data.get('detail'),
            'Unsupported media type "application/xml" in request.'
        )
        self.assertEqual(response.status_code, 415)

    def test_invalid_json_request(self):
        """
        Invalid JSON request by dumping wrong request fields
        """
        response = self.client.post(
            self.url,
            json.dumps({'helpline_numbers': '+919423689096', 'client_numbers': '+918888888888'}),
            content_type='application/json',
        )
        stream = BytesIO(response.content)
        data = JSONParser().parse(stream)
        self.assertEqual(data.get("notification"), "bad_request")
        self.assertEqual(response.status_code, 400)

    def test_get_response(self):
        """
        Get response
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_posting_normal_string(self):
        """
        Posting a normal string instead of JSON
        """
        response = self.client.post(
            self.url,
            {'helpline_numbers': '+919423689096', 'client_numbers': '+918888888888'},
            content_type='application/json',
        )
        stream = BytesIO(response.content)
        data = JSONParser().parse(stream)
        self.assertEqual(response.status_code, 400)
