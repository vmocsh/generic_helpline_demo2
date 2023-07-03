"""
Script for test cases for task manager app
"""
import json

from django.test import TestCase
from django.utils.six import BytesIO
from rest_framework.parsers import JSONParser

from registercall.models import Helper, HelperCategory, HelpLine


class TaskManagerTest(TestCase):
    """
    Testing Class
    """
    register_call_url = '/RegisterCall/'
    new_task_response_url = '/TaskManager/NewTaskResponse/'
    primary_response_url = '/TaskManager/PrimaryResponse/'
    specialist_confirm_response_url = '/TaskManager/SpecialistConfirmResponse/'
    feedback_response_url = '/TaskManager/FeedbackResponse/'
    specialist_response_url = '/TaskManager/SpecialistResponse/'
    get_helper_tasks_url = '/TaskManager/GetHelperTasks/'
    get_task_details_url = '/TaskManager/GetTaskDetails/'

    def setUp(self):
        """
        Setup Database
        """
        canonical_id = "ABC"

        HelpLine.objects.create(name="General", helpline_number="+919423689096")
        HelpLine.objects.create(name="Education", helpline_number="+919423689097")
        HelpLine.objects.create(name="Health", helpline_number="+919423689098")

        general = HelperCategory.objects.create(name="General")
        education = HelperCategory.objects.create(name="Education")
        health = HelperCategory.objects.create(name="Health")

        helper1 = Helper.objects.create(
            first_name="Prashanth",
            helper_number="+919444870256",
            gcm_canonical_id=canonical_id
        )
        helper1.category.add(general)
        helper1.category.add(education)
        helper1.category.add(health)

        helper2 = Helper.objects.create(
            first_name="Swaresh",
            helper_number="+919444870257",
            gcm_canonical_id=canonical_id
        )
        helper2.category.add(general)
        helper2.category.add(health)

        helper3 = Helper.objects.create(
            first_name="Rohit",
            last_name="Singh",
            helper_number="+919444870258",
            gcm_canonical_id=canonical_id
        )
        helper3.category.add(general)
        helper3.category.add(health)

        helper4 = Helper.objects.create(
            first_name="Jaspreet",
            last_name="Singh",
            helper_number="+919444870259",
            gcm_canonical_id=canonical_id
        )
        helper4.category.add(general)
        helper4.category.add(education)

    def create_register_request(
            self, client_number, helpline_number="+919423689096",
            content_type="application/json"):
        """
        Creates register requests
        """
        response = self.client.post(
            self.register_call_url,
            json.dumps({'helpline_number': helpline_number, 'client_number': client_number}),
            content_type=content_type,
        )
        return response

    def create_new_task_response(
            self, helper_number="+919444870256", task_id=1,
            accept="True", content_type="application/json"):
        """
        Creates new task responses
        """
        response = self.client.post(
            self.new_task_response_url,
            json.dumps({'helper_number': helper_number, 'task_id': task_id, 'accept': accept}),
            content_type=content_type,
        )
        return response

    def create_primary_response(
            self, task_id=1, question="Some random query here",
            category="Health", content_type="application/json"):
        """
        Creates primary responses
        """
        response = self.client.post(
            self.primary_response_url,
            json.dumps({'task_id': task_id, 'question': question, 'category': category}),
            content_type=content_type,
        )
        return response

    def create_specialist_feedback(
            self, task_id=1, question="Some random query here",
            answer="Answer goes here", content_type="application/json"):
        """
        Creates specialist responses
        """
        response = self.client.post(
            self.specialist_response_url,
            json.dumps({'task_id': task_id, 'question': question, 'answer': answer}),
            content_type=content_type,
        )
        return response

    def create_specialist_confirm(
            self, task_id=1, verified="True", rating=3,
            content_type="application/json"):
        """
        Creates specialist responses
        """
        response = self.client.post(
            self.specialist_confirm_response_url,
            json.dumps({'task_id': task_id, 'verified': verified, 'rating': rating}),
            content_type=content_type,
        )
        return response

    def get_helper_tasks_request(self, helper_number="+919444870256",
                                 content_type="application/json"):
        """
        Creates specialist responses
        """
        data = json.dumps({'helper_number': helper_number})
        response = self.client.post(
            self.get_helper_tasks_url,
            data,
            content_type=content_type,
        )
        return response

    def get_task_details(self, helper_number="+919444870256", task_id=1,
                         content_type="application/json"):
        """
        Creates specialist responses
        """
        data = json.dumps({'helper_number': helper_number, 'task_id': task_id})
        response = self.client.post(
            self.get_task_details_url,
            data,
            content_type=content_type,
        )
        return response

    def test_new_task(self):
        """
        Test new task creation
        """
        response = self.create_register_request(
            client_number='+919444870256',
            helpline_number='+919423689097',
        )
        stream = BytesIO(response.content)
        data = JSONParser().parse(stream)
        self.assertEqual(data.get("notification"), "new_task_created")
        self.assertEqual(response.status_code, 201)

        response = self.create_register_request(
            client_number='+919444870257',
            helpline_number='+919423689097',
        )
        stream = BytesIO(response.content)
        data = JSONParser().parse(stream)
        self.assertEqual(data.get("notification"), "new_task_created")
        self.assertEqual(response.status_code, 201)

    def test_helpers_exhaust(self):
        """
        Testing how system behaves when helpers exhaust
        """
        response = self.create_register_request(
            client_number='+919444870256',
            helpline_number='+919423689096',
        )
        stream = BytesIO(response.content)
        data = JSONParser().parse(stream)
        self.assertEqual(data.get("notification"), "new_task_created")
        self.assertEqual(response.status_code, 201)

        response = self.create_register_request(
            client_number='+919444870257',
            helpline_number='+919423689097',
        )
        stream = BytesIO(response.content)
        data = JSONParser().parse(stream)
        self.assertEqual(data.get("notification"), "new_task_created")
        self.assertEqual(response.status_code, 201)

    def test_get_task_details(self):
        """
        Testing get task details view
        """
        task_id = 18

        response = self.create_register_request(client_number='+917045800338')
        stream = BytesIO(response.content)
        data = JSONParser().parse(stream)
        self.assertEqual(data.get("notification"), "new_task_created")
        self.assertEqual(response.status_code, 201)

        response = self.get_task_details(
            task_id=task_id,
            helper_number='+919444870256'
        )
        self.assertEqual(response.status_code, 200)

    def test_get_helper_tasks(self):
        """
        Testing get tasks for a particular helper
        """
        response = self.create_register_request(client_number='+917045800338')
        stream = BytesIO(response.content)
        data = JSONParser().parse(stream)
        self.assertEqual(data.get("notification"), "new_task_created")
        self.assertEqual(response.status_code, 201)

        response = self.create_register_request(client_number='+917045800339')
        stream = BytesIO(response.content)
        data = JSONParser().parse(stream)
        self.assertEqual(data.get("notification"), "new_task_created")
        self.assertEqual(response.status_code, 201)

        response = self.create_register_request(client_number='+917045800340')
        stream = BytesIO(response.content)
        data = JSONParser().parse(stream)
        self.assertEqual(data.get("notification"), "new_task_created")
        self.assertEqual(response.status_code, 201)

        response = self.get_helper_tasks_request()
        stream = BytesIO(response.content)
        data = JSONParser().parse(stream)
        self.assertEqual(response.status_code, 200)

    def test_complete_task_execution(self):
        """
        Testing complete task execution loop
        """
        task_id = 14

        response = self.create_register_request(client_number='+917045800338')
        stream = BytesIO(response.content)
        data = JSONParser().parse(stream)
        self.assertEqual(data.get("notification"), "new_task_created")
        self.assertEqual(response.status_code, 201)

        response = self.create_new_task_response(task_id=task_id, accept="False")
        stream = BytesIO(response.content)
        data = JSONParser().parse(stream)
        self.assertEqual(data.get("notification"), "new_task_rejected")
        self.assertEqual(response.status_code, 200)

        response = self.create_new_task_response(
            task_id=task_id,
            helper_number="+919444870257",
        )
        stream = BytesIO(response.content)
        data = JSONParser().parse(stream)
        self.assertEqual(data.get("notification"), "new_task_assigned")
        self.assertEqual(response.status_code, 202)

        response = self.create_new_task_response(task_id=task_id)
        stream = BytesIO(response.content)
        data = JSONParser().parse(stream)
        self.assertEqual(data.get("notification"), "task_already_assigned")
        self.assertEqual(response.status_code, 205)

        response = self.create_primary_response(task_id=task_id)
        stream = BytesIO(response.content)
        data = JSONParser().parse(stream)
        self.assertEqual(data.get("notification"), "Accepted")
        self.assertEqual(response.status_code, 202)

        response = self.create_new_task_response(
            task_id=task_id,
            helper_number="+919444870256",
        )
        stream = BytesIO(response.content)
        data = JSONParser().parse(stream)
        self.assertEqual(data.get("notification"), "new_task_assigned")
        self.assertEqual(response.status_code, 202)

        response = self.create_specialist_feedback(task_id=task_id)
        stream = BytesIO(response.content)
        data = JSONParser().parse(stream)
        self.assertEqual(data.get("notification"), "Accepted")
        self.assertEqual(response.status_code, 202)

        response = self.create_new_task_response(
            task_id=task_id,
            helper_number="+919444870257",
        )
        stream = BytesIO(response.content)
        data = JSONParser().parse(stream)
        self.assertEqual(data.get("notification"), "new_task_assigned")
        self.assertEqual(response.status_code, 202)

        response = self.create_specialist_feedback(task_id=task_id)
        stream = BytesIO(response.content)
        data = JSONParser().parse(stream)
        self.assertEqual(data.get("notification"), "Accepted")
        self.assertEqual(response.status_code, 202)

        response = self.get_task_details(task_id=task_id)
        self.assertEqual(response.status_code, 200)

        response = self.create_new_task_response(
            task_id=task_id,
            helper_number="+919444870256"
        )
        stream = BytesIO(response.content)
        data = JSONParser().parse(stream)
        self.assertEqual(data.get("notification"), "new_task_assigned")
        self.assertEqual(response.status_code, 202)

        response = self.create_specialist_confirm(task_id=task_id)
        stream = BytesIO(response.content)
        data = JSONParser().parse(stream)
        self.assertEqual(data.get("notification"), "Accepted")
        self.assertEqual(response.status_code, 202)

    def test_multiple_assigns_helper(self):
        """
        Testing multiple assign helpers
        """
        response = self.create_register_request(client_number='+917045800338')
        stream = BytesIO(response.content)
        data = JSONParser().parse(stream)
        self.assertEqual(data.get("notification"), "new_task_created")
        self.assertEqual(response.status_code, 201)

        response = self.create_register_request(client_number='+917045800339')
        stream = BytesIO(response.content)
        data = JSONParser().parse(stream)
        self.assertEqual(data.get("notification"), "new_task_created")
        self.assertEqual(response.status_code, 201)

    def test_reject_all(self):
        """
        Reject all testing
        """
        task_id = 25

        response = self.create_register_request(client_number='+917045800338')
        stream = BytesIO(response.content)
        data = JSONParser().parse(stream)
        self.assertEqual(data.get("notification"), "new_task_created")
        self.assertEqual(response.status_code, 201)

        response = self.create_new_task_response(
            helper_number="+919444870256",
            task_id=task_id,
            accept="False",
        )
        stream = BytesIO(response.content)
        data = JSONParser().parse(stream)
        self.assertEqual(data.get("notification"), "new_task_rejected")
        self.assertEqual(response.status_code, 200)

        response = self.create_new_task_response(
            helper_number="+919444870257",
            task_id=task_id,
            accept="False",
        )
        stream = BytesIO(response.content)
        data = JSONParser().parse(stream)
        self.assertEqual(data.get("notification"), "new_task_rejected")
        self.assertEqual(response.status_code, 200)

        response = self.create_new_task_response(
            task_id=task_id,
            helper_number="+919444870258",
        )
        stream = BytesIO(response.content)
        data = JSONParser().parse(stream)
        self.assertEqual(data.get("notification"), "new_task_assigned")
        self.assertEqual(response.status_code, 202)
