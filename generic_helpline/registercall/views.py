"""
Register Call Views
"""

from django.http import JsonResponse
from rest_framework.views import APIView

from ivr.models import Language
from management.models import HelperCategory, CategorySubcategory
from registercall.models import CallRequest, Client, HelpLine, Task
from registercall.options import (CallRequestStatusOptions,
                                  TaskStatusOptions, TaskType)
from task_manager.helpers import AssignAction
from constants import *


class RegisterCall(APIView):
    """
    Register call used to handle incoming call requests
    """
    def assign_helper(self, action):
        pass

    def register_call(self, data):
        """
        Handler for valid requests
        """
        print("In register call get")
        # req_status is the status used to keep track of current call request, it is initialized to
        # CREATED and might update its state to BLOCKED/MERGED before inserting into the model
        req_status = CallRequestStatusOptions.CREATED
        client_number = data.get('client_number')
        helpline_number = data.get('helpline_number')
        location = data.get('location')
        category = data.get('category')
        language = data.get('language')
        sub_category = data.get("sub_category")
        task_type = data.get("task_type")

        hc = HelperCategory.objects.get(name=category)
        print("category retrieved is :", hc)
        lang = Language.objects.get(language=language)
        print("language retrieved is : ", lang)

        # Trying to get client instance and if doesn't exist, create one
        try:
            client = Client.objects.get(client_number=client_number)
            # To check if client is blocked
            if client.is_blocked():
                req_status = CallRequestStatusOptions.BLOCKED

        except Client.DoesNotExist:
            client = Client.objects.create(client_number=client_number, location=location)

        if task_type == "Direct":
            print("In direct register call")
            try:
                call_request = CallRequest.objects.create(
                    helpline=HelpLine.objects.get(helpline_number=helpline_number),
                    client=client,
                    status=req_status,
                    )
            except HelpLine.DoesNotExist:
                req_status = CallRequestStatusOptions.INVALID_HELPLINE
            print("CallRequestStatusOptions status direct :", req_status)

            if req_status == CallRequestStatusOptions.CREATED:
                new_task = Task.objects.create(call_request=call_request, category=hc, task_type=TaskType.DIRECT)
                if sub_category is not None:
                    new_task.tasksubcategory.add(CategorySubcategory.objects.get(subcategory=sub_category,category=hc))
                new_task.language.add(lang)
                print("new task created :", new_task)
                action = AssignAction()
                action.direct_action_assign(new_task)
                return new_task
        else:
            print("-----------In register call:normal call")
            client_has_pending_tasks = Task.objects.filter(
                status=TaskStatusOptions.PENDING,
                call_request__client=client,
                category=hc
            ).exists()

            if client_has_pending_tasks:
                req_status = CallRequestStatusOptions.MERGED
                task = Task.objects.get(
                    status=TaskStatusOptions.PENDING,
                    call_request__client=client,
                    category=hc
                )
                task.client_calls=task.client_calls+1
                task.save()
            try:
                # Creating call request instance
                call_request = CallRequest.objects.create(
                    helpline=HelpLine.objects.get(helpline_number=helpline_number),
                    client=client,
                    status=req_status,
                    )
            except HelpLine.DoesNotExist:
                req_status = CallRequestStatusOptions.INVALID_HELPLINE

            print("CallRequestStatusOptions status indirect:", req_status)

            # Creating new task if client isn't blocked and task not pending for client
            if req_status == CallRequestStatusOptions.CREATED:
                print("-----------In register call:creating new task")
                hc = HelperCategory.objects.get(name=category)
                new_task = Task.objects.create(call_request=call_request, category=hc)
                if sub_category is not None:
                    new_task.tasksubcategory.add(CategorySubcategory.objects.get(category=hc,subcategory=sub_category))
                new_task.language.add(lang)

                print("new task created :", new_task)
                action = AssignAction()
                action.assign_action(new_task)

        return req_status

    def post(self, request):
        """
        Post request handler
        """
        print("In register call POST")
        state = self.register_call(data=request.data)

        if state == CallRequestStatusOptions.CREATED:
            return JsonResponse({"notification": "new_task_created"}, status=201)
        elif state == CallRequestStatusOptions.MERGED:
            return JsonResponse({"notification": "merged_with_pending_task"}, status=202)
        elif state == CallRequestStatusOptions.INVALID_HELPLINE:
            return JsonResponse({"notification": "invalid_helpline"}, status=400)
        elif state == CallRequestStatusOptions.BLOCKED:
            return JsonResponse({"notification": "client_blocked"}, status=406)


