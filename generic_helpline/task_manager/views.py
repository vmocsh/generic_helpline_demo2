"""
Task Manager Views
"""
import re
from django.http import JsonResponse
from rest_framework.views import APIView
from task_manager.models import (ActionTypeOptions, Assign,
                                 AssignStatusOptions, QandA)


class GetHelperTasks(APIView):
    """
    View used to get all tasks related to a particular helper
    """

    def validate_input(self, request):
        """
        Incoming input validator
        """
        data = request.data

        # Checking for required fields
        if data.get('helper_number') is None:
            return False

        phone_pattern = r'^(\+91|0)?\d{10}$'

        if re.match(phone_pattern, data.get('helper_number')) is not None:
            return data
        else:
            return False

    def handler(self, data):
        """
        Returns the list of tasks for current helper
        """
        action_to = ActionTypeOptions()
        assign_so = AssignStatusOptions()
        task_list = []

        try:
            assigns = Assign.objects.select_related('action__task').filter(
                helper__helper_number=data.get('helper_number'),
            ).order_by(
                'action__task_id',
                '-created',
            ).distinct('action__task_id')
        except Assign.DoesNotExist:
            return JsonResponse({"notification": "assign_doesnt_exist"}, status=400)

        for assign in assigns:
            record = {
                'task_id': assign.action.task.pk,
                'task_type': action_to.get_action_type(assign.action.action_type),
                'status': assign_so.get_status(assign.status)
            }
            task_list.append(record)

        return JsonResponse({'task_list': task_list}, status=200)

    def post(self, request):
        """
        Post request handler
        """
        data = self.validate_input(request=request)

        if data:
            response = self.handler(data)
            return response
        else:
            return JsonResponse({"notification": "bad_request"}, status=400)


class GetTaskDetails(APIView):
    """
    View used to get details of particular task
    """
    def validate_input(self, request):
        """
        Incoming input validator
        """
        data = request.data

        # Checking for required fields
        if data.get('helper_number') is None \
                or data.get('task_id') is None:
            return False

        phone_pattern = r'^(\+91|0)?\d{10}$'

        if re.match(phone_pattern, data.get('helper_number')) is not None:
            return data
        else:
            return False

    def handler(self, data):
        """
        Returns particular task details
        """
        assign_so = AssignStatusOptions()
        action_to = ActionTypeOptions()

        try:
            assign = Assign.objects.select_related('action__task').filter(
                helper__helper_number=data.get('helper_number'),
                action__task=data.get('task_id'),
            ).latest('created')
        except Assign.DoesNotExist:
            return JsonResponse({"notification": "assign_doesnt_exist"}, status=400)

        task_type = action_to.get_action_type(assign.action.action_type)
        data = {
            'task_id': assign.action.task.pk,
            'task_type': task_type,
            'status': assign_so.get_status(assign.status),
            'client_number': assign.action.task.call_request.client.client_number,
        }

        if task_type == 'Specialist':
            qna = QandA.objects.get(task=assign.action.task)
            data['question'] = qna.question

        elif task_type == 'Specialist Confirm':
            qna = QandA.objects.get(task=assign.action.task)
            data['question'] = qna.question
            data['answer'] = qna.answer
            data['feedback_question'] = qna.feedback_question
            data['feedback_answer'] = qna.feedback_answer

        return JsonResponse(data, status=200)

    def post(self, request):
        """
        Post request handler
        """
        data = self.validate_input(request=request)

        if data:
            response = self.handler(data)
            return response
        else:
            return JsonResponse({"notification": "bad_request"}, status=400)
