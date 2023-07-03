"""
Helper methods to handle incoming requests
"""

from django.utils import timezone

from register_helper.models import Helper
from registercall.options import TaskStatusOptions
from task_manager.models import Action, Assign, QandA
from task_manager.options import (ActionStatusOptions, ActionTypeOptions,
                                  AssignStatusOptions)
from management.notifications import push_notification
from register_helper.options import HelperLevel, LoginStatus
from management.models import CategorySubcategory
from constants import *


class AssignAction:
    """
    Class to handle Assign Action
    """

    def direct_action_assign(self, task):

        current_action = Action.objects.create(
            task=task,
            action_type=ActionTypeOptions.PRIMARY,
        )
        return current_action

    def primary_assign(self, task, data):
        """
        Assign Action handle for first time, primary is assigned
        """
        helper_methods = HelperMethods()

        exiting_action = Action.objects.filter(task=task)
        if exiting_action:
            current_action = Action.objects.get(task=task)
            if current_action.status == ActionStatusOptions.COMPLETE_TIMEOUT:
                current_action.status = ActionStatusOptions.ASSIGN_PENDING
                current_action.save()
        else:
            current_action = Action.objects.create(
                task=task,
                action_type=ActionTypeOptions.PRIMARY,
            )
        if data == NEW_TASK_NOTIF:
            helper_methods.assign_helpers(
                action=current_action,
                category=task.category,
                data=data,
                no_of_helpers=NO_OF_HELPERS,
                level=HelperLevel.PRIMARY,
                exclude_helpers=None
            )
        elif data == TIMEOUT_TASK_NOTIF:
            assigns = Assign.objects.filter(action=current_action, status=AssignStatusOptions.PENDING)
            timeout_helpers = []
            for assign in assigns:
                timeout_helpers.append(assign.helper.id)
                assign.status = AssignStatusOptions.TIMEOUT
                assign.save()
            assigns = Assign.objects.filter(action=current_action, status=AssignStatusOptions.ACCEPTED)
            for assign in assigns:
                timeout_helpers.append(assign.helper.id)
                assign.status = AssignStatusOptions.TIMEOUT
                assign.save()
            assigns = Assign.objects.filter(action=current_action, status=AssignStatusOptions.TIMEOUT)
            for assign in assigns:
                #timeout_helpers.append(assign.helper.id)
                #assign.status = AssignStatusOptions.TIMEOUT
                assign.delete()
            if MULTILEVEL_ALLOCATION:
                level = HelperLevel.SECONDARY
            else:
                level = HelperLevel.PRIMARY
            helper_methods.assign_helpers(
                action=current_action,
                category=task.category,
                data=data,
                no_of_helpers=NO_OF_HELPERS,
                level=level,
                exclude_helpers=timeout_helpers
            )

    def specialist_assign(self, task):
        """
        Assign action handle once primary assign
        """
        helper_methods = HelperMethods()

        qna = QandA.objects.get(task=task)

        current_action = Action.objects.create(
            task=task,
            action_type=ActionTypeOptions.SPECIALIST,
        )
        data = "New Task Has Been Assigned"
        helper_methods.assign_helpers(
            action=current_action,
            category=task.category,
            data=data,
            no_of_helpers=2,
            level=HelperLevel.PRIMARY,
            exclude_helpers=None
        )

    def feedback_assign(self, task):
        """
        Assign action handle once specialist assign completes
        """
        helper_methods = HelperMethods()

        current_action = Action.objects.create(
            task=task,
            action_type=ActionTypeOptions.FEEDBACK,
        )
        data = "New Feedback Task Has Been Assigned"
        helper_methods.assign_helpers(
            action=current_action,
            category="General",
            data=data,
            no_of_helpers=2,
            level=HelperLevel.PRIMARY,
            exclude_helpers=None
        )

    def specialist_confirm_assign(self, task):
        """
        Assign action handle once feedback completes
        """
        helper_methods = HelperMethods()

        # Fetches the QandA for the task
        qna = QandA.objects.get(task=task)

        current_action = Action.objects.create(
            task=task,
            action_type=ActionTypeOptions.SPECIALIST_CONFIRM,
        )
        data = "New Confirm Task Has Been Assigned"
        helper_methods.assign_helpers(
            action=current_action,
            category=task.category,
            data=data,
            no_of_helpers=2,
            level=HelperLevel.PRIMARY,
            exclude_helpers=None
        )

    def specialist_confirm_complete(self, task):
        """
        Task completion
        """
        task.status = TaskStatusOptions.COMPLETED
        task.save()

    def timeout(self, task, previous_action):
        """
        Complete/Assign action timeout handler
        """
        action_to = ActionTypeOptions()

        if action_to.get_action_type(previous_action.action_type) == "Primary":
            self.primary_assign(task, TIMEOUT_TASK_NOTIF)
        elif action_to.get_action_type(previous_action.action_type) == "Specialist":
            self.specialist_assign(task)
        elif action_to.get_action_type(previous_action.action_type) == "Feedback":
            self.feedback_assign(task)
        elif action_to.get_action_type(previous_action.action_type)\
                == "Specialist Confirm":
            self.specialist_confirm_assign(task)

    def assign_action(self, task):
        """
        Method to assigning new action to task based on current action
        """

        # Fetching the previous action
        try:
            previous_action = Action.objects.filter(task=task).latest('created')
        except Action.DoesNotExist:
            previous_action = None

        # If task is incoming is being assigned an action for the first time
        if previous_action is None:
            self.primary_assign(task, NEW_TASK_NOTIF)

        # In case of Primary Task completes
        elif previous_action.action_type == ActionTypeOptions.PRIMARY and\
                previous_action.status == ActionStatusOptions.COMPLETED:
            self.specialist_assign(task)

        # In case of Specialist Task completes
        elif previous_action.action_type == ActionTypeOptions.SPECIALIST and \
                previous_action.status == ActionStatusOptions.COMPLETED:
            self.feedback_assign(task)

        # In case of Feedback completes
        elif previous_action.action_type == ActionTypeOptions.FEEDBACK and \
                previous_action.status == ActionStatusOptions.COMPLETED:
            self.specialist_confirm_assign(task)

        # In case of task complete
        elif previous_action.action_type == ActionTypeOptions.SPECIALIST_CONFIRM and \
                previous_action.status == ActionStatusOptions.COMPLETED:
            self.specialist_confirm_complete(task)

        # In case of Assigned timeout/ Complete timeout/ Rejected by all helpers, reassign action
        elif previous_action.status == ActionStatusOptions.ASSIGN_TIMEOUT or \
                previous_action.status == ActionStatusOptions.COMPLETE_TIMEOUT or \
                previous_action.status == ActionStatusOptions.REJECTED:
            self.timeout(task, previous_action)

        return True


class HelperMethods:

    def fetch_helpers(self, category, language, pending, accepted, level, subcategory):

        print(type(category))

        helpers = Helper.objects.all().exclude(login_status=LoginStatus.PENDING)
        if category is not None:
            helpers = helpers.filter(category__name=category)
        if language is not None:
            helpers = helpers.filter(language__language=language)
        if pending:
            helpers = helpers.exclude(assigned_to__status=AssignStatusOptions.PENDING)
        if accepted:
            helpers = helpers.exclude(assigned_to__status=AssignStatusOptions.ACCEPTED)
        if MULTILEVEL_ALLOCATION and level is not None:
            helpers = helpers.filter(level=level)
        if SUB_CATEGORY_ALLOCATION and subcategory is not None:
            helpers = helpers.filter(subcategory=CategorySubcategory.objects.get(category=category,subcategory=subcategory))

        helpers = helpers.order_by('last_assigned')
        return helpers

    """
    Class used to define helper methods
    """
    def assign_helpers(self, action, category, data, no_of_helpers, level, exclude_helpers):
        """
        Used to assign helpers to a particular action
            param action: Action to which we need to assign helpers
            param category: Category of helpers
            param data: Data Message to be sent to helpers
            param no_of_helpers: The number of helpers we need to assign
        """
        # Initially tries to assign free helpers
        # Added filter of subcategories to enable task allocation based on category, subcategory and language
        task_subcat = action.task.tasksubcategory.all()
        subcat = None
        for subcategory in task_subcat:
            subcategory = str(subcategory)
            pos = subcategory.index(":")
            subcat = subcategory[pos + 1:]

        free_helpers_assigned = 0
        count = 0
        accepted = True
        pending = True
        all_possible_checked = False
        language = None
        assigning_list = []
        assigning_list_id = []
        if action.task.language.all():
            language = action.task.language.all()[0]
        while no_of_helpers > free_helpers_assigned and not all_possible_checked:

            if count == 1:
                accepted = False
                pending = False
            #elif count == 2:
            #    subcat = None
            #    all_possible_checked = True
            elif count == 2:
            #    subcat = None
                all_possible_checked = True

            #elif count == 3:
            #    level = None
            #elif count == 4:
            #    category = None
            #    all_possible_checked = True

            helpers = self.fetch_helpers(category, language, pending, accepted, level, subcat)
            print("----count: ", count, " helpers: ", helpers, "---------------")
            for helper in assigning_list:
                assigning_list_id.append(helper.id)

            if assigning_list_id is not None:
                helpers = helpers.exclude(id__in=assigning_list_id)

            print('exclude_helpers: ', exclude_helpers)

            if exclude_helpers is not None:
                helpers = helpers.exclude(id__in=exclude_helpers)
            free_helpers_assigned += helpers.count()
            assigning_list.extend(helpers)
            count += 1

        count = 0
        for helper in assigning_list:
            print('In helpers assignment: ', helper)
            if count == no_of_helpers:
                break
            # Used to prioritize helpers for later selection
            helper.last_assigned = timezone.localtime(timezone.now())
            helper.save()
            Assign.objects.create(helper=helper, action=action)
            count += 1
        # Send new task notifications to clients
        self.send_new_task_notification(action=action, data=data)

    def send_new_task_notification(self, action, data):
        """
        Sends task notifications to respective helpers for specified action
        """
        assignments = Assign.objects.filter(
            action=action
        )
        print(assignments)

        for assignment in assignments:
            # Send notification to all GCM ids of helpers
            push_notification(assignment.helper.gcm_canonical_id, data)

    def send_new_task_notification_for_accepted_action(self, helper, data):
        """
        Sends task notifications to respective helpers for accepted actions
        """        
        push_notification(helper.gcm_canonical_id, data)

    def terminate_and_assign_new_action(self, action):
        """
        Terminates current assign and action and creates new action
        """
        try:
            assign = Assign.objects.filter(
                action__task=action.task,
                status=AssignStatusOptions.ACCEPTED,
            ).latest("created")
        except Assign.DoesNotExist:
            return False

        # Completing current assign and action
        assign.status = AssignStatusOptions.COMPLETED
        assign.save()
        assign.action.status = ActionStatusOptions.COMPLETED
        assign.action.save()

        # Assigning new action
        new_action = AssignAction()

        return new_action.assign_action(action.task)

    def set_helper_rating(self, task, rating):
        """
        logic for helper rating to be implemented
        """
        pass
