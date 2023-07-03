"""
Response Views
"""
import re

from django.http import JsonResponse
from django.utils import timezone
from rest_framework.views import APIView

from management.models import HelperCategory
from task_manager.helpers import AssignAction, HelperMethods
from task_manager.models import (Action, ActionStatusOptions, Assign,
                                 AssignStatusOptions, QandA)


class NewTaskResponse(APIView):
    """
    New Task Response view
        meant for all - primary, specialist, feedback and specialist confirm
    """

    def validate_input(self, request):
        """
        Incoming input validator
        """
        data = request.data

        # Checking for required fields
        if data.get('helper_number') is None or data.get('accept') is None \
                or data.get('task_id') is None:
            return False

        # Validating phone pattern
        phone_pattern = r'^(\+91|0)?\d{10}$'
        if re.match(phone_pattern, data.get('helper_number')) is not None and \
                (data.get('accept') == "True" or data.get('accept') == "False"):
            return data
        else:
            return False

    def handler(self, action, data):
        """
        Assigns helper to task
        Returns: True on assign success, False if already assigned to some other helper
        """

        if action.status == ActionStatusOptions.ASSIGNED:
            return AssignStatusOptions.CLOSED
        else:
            try:
                assign = Assign.objects.get(
                    helper__helper_number=data.get('helper_number'),
                    action=action,
                )
            except Assign.DoesNotExist:
                return False

            # If its an accept
            if data.get('accept') == "True":

                # change both assign and action status
                action.status = ActionStatusOptions.ASSIGNED
                action.save()
                assign.status = AssignStatusOptions.ACCEPTED
                # Update assigned time, used in scheduled jobs for timeout
                assign.accepted = timezone.localtime(timezone.now())
                assign.save()
                # To end other assigns
                other_assigns = Assign.objects.filter(action=action).\
                    exclude(helper__helper_number=data.get('helper_number'))
                # Don't allow other helpers to assign here after
                for other_assign in other_assigns:
                    other_assign.status = AssignStatusOptions.CLOSED
                    other_assign.save()

            # If its an reject
            else:
                assign.status = AssignStatusOptions.REJECTED
                assign.save()
                # If all rejects the task
                all_rejected = True
                assigns = Assign.objects.filter(
                    action=action,
                )
                for other_assign in assigns:
                    if other_assign.status != AssignStatusOptions.REJECTED:
                        all_rejected = False
                        break

                # If everyone has rejected, create new action
                if all_rejected:
                    action.status = ActionStatusOptions.REJECTED
                    action.save()
                    new_action = AssignAction()
                    new_action.assign_action(action.task)

            return assign.status

    def post(self, request):
        """
        Post request handler
        """
        data = self.validate_input(request=request)

        if data:

            try:
                action = Action.objects.select_related('task').filter(
                    task__pk=data.get('task_id')
                ).latest("created")
            except Action.DoesNotExist:
                return JsonResponse({"notification": "Action Doesn't Exist"}, status=400)

            assigned = self.handler(action, data)

            if assigned == AssignStatusOptions.ACCEPTED:
                return JsonResponse({
                    "notification": "new_task_assigned",
                    "task_id": action.task.id,
                    "task_type": action.action_type
                }, status=202)
            elif assigned == AssignStatusOptions.REJECTED:
                return JsonResponse({"notification": "new_task_rejected"}, status=200)
            elif assigned == AssignStatusOptions.CLOSED:
                return JsonResponse({"notification": "task_already_assigned"}, status=205)
            else:
                return JsonResponse({"notification": "helper_never_assigned"}, status=400)

        else:
            return JsonResponse({"notification": "bad_request"}, status=400)


class PrimaryResponse(APIView):
    """
    Primary Task Response handler
    """

    def validate_input(self, request):
        """
        Incoming input validator
        """
        data = request.data

        # Checking for required fields
        if data.get('question') is None or data.get('category') is None \
                or data.get('task_id') is None:
            return False
        else:
            return data

    def handler(self, action, data):
        """
        Terminate the assign and action, store question & category, and call assign_action
        """
        try:
            action.task.category = HelperCategory.objects.get(name=data.get("category"))
            action.task.save()
        except HelperCategory.DoesNotExist:
            return JsonResponse({"notification": "helper_category_doesnt_exist"}, status=400)

        QandA.objects.create(
            task=action.task,
            question=data.get('question'),
        )

        helper_methods = HelperMethods()
        if helper_methods.terminate_and_assign_new_action(action):
            return JsonResponse({"notification": "Accepted"}, status=202)
        else:
            return JsonResponse({"notification": "task_not_assigned_to_helper"}, status=400)

    def post(self, request):
        """
        Post request handler
        """
        data = self.validate_input(request=request)

        if data:

            try:
                action = Action.objects.select_related('task').filter(
                    task__pk=data.get('task_id')
                ).latest("created")
                response = self.handler(action, data)
            except Action.DoesNotExist:
                return JsonResponse({"notification": "action_doesnt_exist"}, status=400)

            return response
        else:
            return JsonResponse({"notification": "bad_request"}, status=400)


class SpecialistResponse(APIView):
    """
    Specialist Response Handler
    """

    def validate_input(self, request):
        """
        Incoming input validator
        """
        data = request.data

        # Checking for required fields
        if data.get('question') is None or data.get('answer') is None \
                or data.get('task_id') is None:
            return False
        else:
            return data

    def handler(self, action, data):
        """
        Handler function
        """
        qna = QandA.objects.get(task=action.task)
        qna.question = data.get('question')
        qna.answer = data.get('answer')
        qna.save()

        helper_methods = HelperMethods()
        helper_methods.terminate_and_assign_new_action(action)

    def post(self, request):
        """
        Post request handler
        """
        data = self.validate_input(request=request)

        if data:

            try:
                action = Action.objects.select_related('task').filter(
                    task__pk=data.get('task_id')
                ).latest("created")
                self.handler(action, data)
            except Action.DoesNotExist:
                return JsonResponse({"notification": "action_doesnt_exist"}, status=400)

            return JsonResponse({"notification": "Accepted"}, status=202)
        else:
            return JsonResponse({"notification": "bad_request"}, status=400)


class FeedbackResponse(APIView):
    """
    Feedback Response Handler
    """

    def validate_input(self, request):
        """
        Incoming input validator
        """
        data = request.data

        # Checking for required fields
        if data.get('question') is None or data.get('answer') is None \
                or data.get('task_id') is None:
            return False
        else:
            return data

    def handler(self, action, data):
        """
        Update QandA and assign next action
        """
        qna = QandA.objects.get(task=action.task)
        qna.feedback_question = data.get('question')
        qna.feedback_answer = data.get('answer')
        qna.save()

        helper_methods = HelperMethods()
        helper_methods.terminate_and_assign_new_action(action)

    def post(self, request):
        """
        Post request handler
        """
        data = self.validate_input(request=request)

        if data:

            try:
                action = Action.objects.select_related('task').filter(
                    task__pk=data.get('task_id')
                ).latest("created")
                self.handler(action, data)
            except Action.DoesNotExist:
                return JsonResponse({"notification": "action_doesnt_exist"}, status=400)

            return JsonResponse({"notification": "Accepted"}, status=202)
        else:
            return JsonResponse({"notification": "bad_request"}, status=400)


class SpecialistConfirmResponse(APIView):
    """
    Specialist Confirm Response View
    """

    def validate_input(self, request):
        """
        Incoming input validator
        """
        data = request.data

        # Checking for required fields
        if data.get('verified') is None or data.get('rating') is None \
                or data.get('task_id') is None:
            return False

        # Checking for validity of sent data
        if (data.get('verified') == "True" or data.get('verified') == "False") and \
                data.get('rating') >= 0 and \
                data.get('rating') <= 5:
            return data
        else:
            return False

    def handler(self, action, data):
        """
        Updating task status
        """
        qna = QandA.objects.get(task=action.task)
        qna.verified = int(data.get("verified") == "True")
        qna.save()

        helper_methods = HelperMethods()
        helper_methods.set_helper_rating(action.task, data.get('rating'))
        helper_methods.terminate_and_assign_new_action(action)

    def post(self, request):
        """
        Post request handler
        """
        data = self.validate_input(request=request)

        if data:
            try:
                action = Action.objects.select_related('task').filter(
                    task__pk=data.get('task_id')
                ).latest("created")
                self.handler(action, data)
            except Action.DoesNotExist:
                return JsonResponse({"notification": "action_doesnt_exist"}, status=400)
            return JsonResponse({"notification": "Accepted"}, status=202)
        else:
            return JsonResponse({"notification": "bad_request"}, status=400)
