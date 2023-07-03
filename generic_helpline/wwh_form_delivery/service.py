from unicodedata import category

from ivr.models import Language
from management.models import HelpLine, HelperCategory
from register_client.models import Client
from registercall.models import Task, CallRequest
from registercall.options import TaskStatusOptions, CallRequestStatusOptions
from task_manager.helpers import AssignAction
from loguru import logger


def create_or_update_task(data):
    """
    The interface through which we add queries that come from hospital form
    (Similar to what happens when IVR calls WWH API to register new task)
    """
    helpline = HelpLine.objects.first()
    helpline_number = helpline.helpline_number
    lang = Language.objects.get(language=data['language'])
    req_status = CallRequestStatusOptions.CREATED
    client = Client.objects.filter(client_number=data['contact']).first()
    client_has_pending_tasks = False
    if client:
        logger.info('existing client')
        client_has_pending_tasks = Task.objects.filter(
            status=TaskStatusOptions.PENDING,
            call_request__client=client,
            category=HelperCategory.objects.filter(name=data['category']).first()
        ).exists()
    else:
        logger.info('creating new client')
        client = Client.objects.create(client_number=data['contact'], location=data['location'])

    if client_has_pending_tasks:
        logger.info('there exists a task for this client with same category')
        # same category tasks from the same user will be merged
        req_status = CallRequestStatusOptions.MERGED

    try:
        # Creating call request instance
        call_request = CallRequest.objects.create(
            helpline=HelpLine.objects.get(helpline_number=helpline_number),
            client=client,
            status=req_status,
        )
    except HelpLine.DoesNotExist:
        call_request = None
        req_status = CallRequestStatusOptions.INVALID_HELPLINE

    # Creating new task if client isn't blocked and task not pending for client
    if req_status == CallRequestStatusOptions.CREATED:
        logger.info('creating new wwh task')
        hc = HelperCategory.objects.get(name=data['category'])
        new_task = Task.objects.create(call_request=call_request, category=hc, from_whatsapp=True)
        # TODO: do we need sub_category for hospital apps?
        # if sub_category is not None:
        #     new_task.tasksubcategory.add(CategorySubcategory.objects.get(subcategory=sub_category))
        new_task.language.add(lang)
        new_task.save()

        # Note: Action is like task meta data and Assign is to track which helper is assigned on which task
        action = AssignAction()
        action.assign_action(new_task)
        return new_task.id
    elif req_status == CallRequestStatusOptions.MERGED:
        logger.info('merging with existing wwh task')
        existing_task = Task.objects.filter(
            status=TaskStatusOptions.PENDING,
            call_request__client=client,
            category=HelperCategory.objects.filter(name=data['category']).first()).first()
        existing_task.from_whatsapp = True
        existing_task.save()
        return existing_task.id


def convert_queryset_to_list_of_tuples(queryset):
    output_list_of_tuples = []
    for element in queryset:
        output_list_of_tuples.append((str(element), str(element)))
    print(output_list_of_tuples)
    return output_list_of_tuples
