"""
Script used to manage schedule jobs using celery-redis.
	All four tasks will be need to be added in models related to task
	management in celery which runs after intervals
"""

import csv
import datetime

from celery.decorators import periodic_task
from celery.task.schedules import crontab
from celery.utils.log import get_task_logger
from django.db.models import Q
from django.utils import timezone

from authentication.send_email import email_to
from constants import *
from ivr.models import Call_Forward_Details
from management.models import HelplineSetting
# from task_manager.options import ActionTypeOptions
from register_client.models import Client
from register_helper.models import Helper
# from registercall.models import FollowUpTask, Task
from registercall.models import CallRequest, Task
from registercall.options import TaskStatusOptions
from task_manager.helpers import HelperMethods, AssignAction
from task_manager.models import Action, Assign, QandA, TaskHistory
from task_manager.options import ActionStatusOptions, AssignStatusOptions

logger = get_task_logger(__name__)



# @periodic_task(
#     run_every=(crontab(hour=01, minute=17)),
#     name="GetFeedback",
#     ignore_result=True
# )


'''@periodic_task(
	run_every=(crontab(minute=5, hour=[10,17])),   #crontab(minute=5, hour=[10,17])
	name="pending_task_remainder",
	ignore_result=True
)

def pending_task_remainder():
	"""
	New task remainder to helper to accept/reject new task
	"""
	print("PENDING TASK REMINDER------")
	helpline_objects = HelplineSetting.objects.all()


	for helpline in helpline_objects:
		pending_actions = Action.objects.filter(Q(status=ActionStatusOptions.ASSIGN_PENDING) | Q(status=ActionStatusOptions.ASSIGNED))

		# For each pending action, send remainder
		for pending_action in pending_actions:

			data = 'PENDING TASKS REMINDER : Task %d is pending.' %pending_action.task.id
			print("Pending TASK____id:", data)
			helper_methods = HelperMethods()
			helper_methods.send_new_task_notification(action=pending_action, data=data)'''


# @periodic_task(
# run_every=(crontab(hour=9, minute=30)),
# 	name="create_follow_up",
# 	ignore_result=True
# )
#
# def create_follow_up():
# 	pending_follow = FollowUpTask.objects.filter(created_date=date.today())
# 	for tasks in pending_follow:
# 		par_task = tasks.parent_task
# 		tasks.create_status = 'Active'
# 		call_request = par_task.call_request
# 		hc = par_task.category
# 		lang = par_task.language.all()[0]
# 		new_task = Task.objects.create(call_request=call_request, category=hc)
# 		new_task.language.add(lang)
# 		helper = tasks.helper
#
# 		tasks.task = new_task
# 		print("new task created :", new_task)
#
# 		current_action = Action.objects.create(
# 			task=new_task,
# 			action_type=ActionTypeOptions.PRIMARY,
# 		)
# 		Assign.objects.create(helper=helper, action=current_action, status=AssignStatusOptions.FOLLOW_UP_ACCEPTED)
# 		data = 'New Follow Up Task has been assigned for Task: '%par_task.id
# 		helper_methods = HelperMethods()
# 		helper_methods.send_new_task_notification(action=par_task.action, data=data)


'''@periodic_task(
	run_every=(crontab(minute=10, hour=[9,19])), #crontab(minute=10, hour=[9,19])
	name="accepted_task_remainder",
	ignore_result=True
)

def accepted_task_remainder():
	"""
	Task remainder to helper for accepted Tasks
	"""
	print("ACCEPTED TASK REMINDER------")
	helpers = Helper.objects.all()

	for helper in helpers:
		accepted_assigns = Assign.objects.filter(helper=helper, status=AssignStatusOptions.ACCEPTED)

		task_ids = []

		# For each accepted action, collect task ids
		for accepted_assign in accepted_assigns:
			task_ids.append(accepted_assign.action.task.id)


		taskIdString = ','.join([str(i) for i in task_ids])
		print(taskIdString)
		data = 'ACCEPTED TASKS REMINDER : Tasks %s requires your attention.' %taskIdString
		print("ACCEPTED TASK____id:", data)
		helper_methods = HelperMethods()
		helper_methods.send_new_task_notification_for_accepted_action(helper=helper, data=data)'''




@periodic_task(
	run_every=(crontab(minute=30, hour=[12, 21])),  #crontab(minute=30, hour=[12,15,18,21])
	name="reallocated_Task_timeout",
	ignore_result=True
)

def reallocated_Task_timeout():
	"""
	The reallocated task was not accepted therefore, reallocate to a dedicated senior helper
	"""
	print("REALLOCATED TASK TIMEOUT------")
	# Start time below which assigns have to be picked
	start = timezone.localtime(timezone.now())-datetime.timedelta(hours=24)     #datetime.timedelta(minutes=1) #- datetime.timedelta(hours=6)

	timeout_assigns = Assign.objects.filter(
		status=AssignStatusOptions.REALLOCATED,
		action__status=ActionStatusOptions.ASSIGNED,
		created__lte=start,
	)
	helper_index = 0;
	new_helpers = [249, 250, 272]
	# For each timed out assign, change status to timeout
	for timeout_assign in timeout_assigns:
		new_helper =  Helper.objects.get(id=new_helpers[helper_index])  #fixed secondary helper to whom the task will be reallocated
		helper_index = (helper_index + 1) % len(new_helpers)
		old_helper = timeout_assign.helper
		timeout_assign.helper = new_helper
		timeout_assign.modified = timezone.localtime(timezone.now())
		timeout_assign.save()

		old_history = TaskHistory.objects.filter(task=timeout_assign.action.task, toHelper=old_helper).order_by('-reallocateDate')[0]
		reason = old_history.reason
		if "TIMED OUT:" not in reason:
			reason = "TIMED OUT: " + reason
		history = TaskHistory(task=timeout_assign.action.task, fromHelper=old_helper, toHelper=new_helper, reason=reason)
		history.save()
		helper_method = HelperMethods()
		data = "TIMED OUT Task has been reallocated"
		helper_method.send_new_task_notification(action=timeout_assign.action, data=data)


@periodic_task(
	run_every=(crontab(minute=10, hour=[15, 18])),  #crontab(minute=10, hour=[12,15,18,21])
	name="pending_task_timeout",
	ignore_result=True
)

def pending_task_timeout():
	"""
	None of the helpers accepted in given time, leading to new action and assigns
	"""
	print("PENDING TASK TIMEOUT------")
	reassign_action_tasks = []

	# Start time below which assigns have to be picked
	start = timezone.localtime(timezone.now()) - datetime.timedelta(hours=24) ###############datetime.timedelta(minutes=1)

	timeout_assigns = Assign.objects.filter(
		status=AssignStatusOptions.PENDING,
		action__status=ActionStatusOptions.ASSIGN_PENDING,
		created__lte=start,
	)
	print("TIMEOUT ASSIGNS:-----", timeout_assigns)
	# For each timed out assign, change status to timeout
	for timeout_assign in timeout_assigns:
		timeout_assign.status = AssignStatusOptions.TIMEOUT
		timeout_assign.save()

		# If task not in reassign action task list, append
		if timeout_assign.action.task not in reassign_action_tasks:
			reassign_action_tasks.append(timeout_assign.action.task)
			timeout_assign.action.status = ActionStatusOptions.COMPLETE_TIMEOUT
			timeout_assign.action.save()

	assign_act = AssignAction()
	# For all tasks in reassign action, run assign_action helper method
	for task in reassign_action_tasks:
		assign_act.assign_action(task)


		
'''
@periodic_task(
	run_every=(crontab(hour=11, minute=45)),
	name="send_promotional_sms",
	ignore_result=True
)

def send_promotional_sms():

    """
    Method to send promotional sms to clients every month
    """

    client_list = Client.objects.all()
    for client in client_list:
        all_call_requests = CallRequest.objects.filter(client=client).order_by('-created')
        current_time = timezone.localtime(timezone.now())
        last_sms_date = client.lastSMSSent
        if all_call_requests:
        	if last_sms_date == "" or last_sms_date is None:
				last_call_time_diff = current_time - all_call_requests[0].created
				# print "last_call_time_diff ", last_call_time_diff
				if last_call_time_diff.days > 30:
					message = PROMOTIONAL_SMS
					print('caller_number ', client.client_number)
					caller_number = client.client_number
					user_name = SMS_USER
					password = SMS_PWD
					sender_id = SMS_SENDERID
					msg_url = 'http://smscloud.ozonetel.com/GatewayAPI/rest?send_to=' + caller_number + '&msg=' + message \
					      + '&msg_type=text&loginid=' + user_name + '&auth_scheme=plain&password=' + password + \
					      '&v=1.1&format=text&method=sendMessage&mask=' + sender_id
					urlopen(msg_url)
					client.save()
        	else:
		        last_sms_time_diff = current_time - last_sms_date
		        # print "last_sms_time_diff ", last_sms_time_diff
		        # print "last_sms_time_diff days ", last_sms_time_diff.days
        		if last_sms_time_diff.days > 30:
					last_call_time_diff = current_time - all_call_requests[0].created
					# print "last_call_time_diff ", last_call_time_diff
					if last_call_time_diff.days > 30:
						message = PROMOTIONAL_SMS
						print('caller_number ', client.client_number)
						caller_number = client.client_number
						user_name = SMS_USER
						password = SMS_PWD
						sender_id = SMS_SENDERID
						msg_url = 'http://smscloud.ozonetel.com/GatewayAPI/rest?send_to=' + caller_number + '&msg=' + message \
						          + '&msg_type=text&loginid=' + user_name + '&auth_scheme=plain&password=' + password + \
						          '&v=1.1&format=text&method=sendMessage&mask=' + sender_id
						urlopen(msg_url)
						client.save()

'''

'''

@periodic_task(
	run_every=(crontab(hour=7, minute=30, day_of_week=6)),
	name="weekly_report",
	ignore_result=True
)

def weekly_report():

	with open(HELPER_WEEKLY_REPORT, 'w') as csvfile:
	    fieldnames = ['Helper', 'Total tasks', 'Tasks pending', 'Tasks accepted', 'Tasks completed', 'Average Acceptance Time(hours)', 'Average Response Time(hours)', 'Average Completion Time(hours)']
	    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
	    writer.writeheader()
	    helper_assign_mapping = {}
	    total_assigns = Assign.objects.filter(created__gte=timezone.now()-datetime.timedelta(days=30))

	    for assign in total_assigns:
	    	if helper_assign_mapping.get(assign.helper.user.username):
	    		helper_assign_mapping[assign.helper.user.username].append(assign)
	    	else:
	    		helper_assign_mapping[assign.helper.user.username] = [assign]
	    dictList = []

	    print(helper_assign_mapping)
	    assign_list = []
	    for helper, assign_list in helper_assign_mapping.iteritems():
	    	pending_count = 0
	    	accepted_count = 0
	    	completed_count = 0
	    	response_count = 0
	    	accepted_time = 0
	    	completed_time = 0
	    	response_time = 0
	    	total_count = len(assign_list)
	    	for assign in assign_list:
	    		call_forward_details = Call_Forward_Details.objects.filter(task=assign.action.task).order_by('created')
	    		if assign.status == AssignStatusOptions.PENDING:
	    			pending_count += 1
	    		elif assign.status == AssignStatusOptions.ACCEPTED:
	    			accepted_count += 1
	    			accepted_time += (int(assign.accepted.strftime('%s'))-int(assign.created.strftime('%s')))/3600
	    		elif assign.status == AssignStatusOptions.COMPLETED:
	    			completed_count += 1
	    			qanda = QandA.objects.get(task=assign.action.task)
	    			qanda_time = qanda.created
	    			accepted_time += (int(assign.accepted.strftime('%s'))-int(assign.created.strftime('%s')))/3600
	    			completed_time += (int(qanda_time.strftime('%s'))-int(assign.accepted.strftime('%s')))/3600
	    		if len(call_forward_details) != 0:
	    			response_time += (int(call_forward_details[0].created.strftime('%s'))-int(assign.accepted.strftime('%s')))/3600
	    			response_count += 1

	    	if response_count == 0:
	    		avg_response_time = float('inf')
	    	else:
	    		avg_response_time = response_time/response_count

	    	if accepted_count == 0 and completed_count == 0:
	    		avg_accepted_time = float('inf')
	    		avg_completed_time = float('inf')
	    	else:
	    		avg_accepted_time = accepted_time/(accepted_count+completed_count)
	    		
	    	if completed_count == 0:
				avg_completed_time = float('inf')
	    	else:
	    		avg_completed_time = completed_time/completed_count

	    	dictRow = {'Helper': helper, 'Total tasks': total_count, 'Tasks pending': pending_count, 'Tasks accepted': accepted_count, 'Tasks completed': completed_count, 'Average Acceptance Time(hours)': avg_accepted_time, 'Average Response Time(hours)': avg_response_time, 'Average Completion Time(hours)': avg_completed_time}
	    	dictList.append(dictRow)
	    	writer.writerow(dictRow)
	files = [HELPER_WEEKLY_REPORT]
	subject = SUBJECT
	body = BODY+'\n'
	number_of_tasks = Task.objects.filter(created__gte=timezone.now()-datetime.timedelta(days=7)).count()
	pending_tasks = Task.objects.filter(status=TaskStatusOptions.PENDING, created__gte=timezone.now()-datetime.timedelta(days=7)).count()
	completed_tasks = Task.objects.filter(status=TaskStatusOptions.COMPLETED, created__gte=timezone.now()-datetime.timedelta(days=7)).count()
	body = body + '\t Total tasks:\t'+ str(number_of_tasks) + '\n'
	body = body + '\t Total pending tasks:\t'+ str(pending_tasks) + '\n'
	body = body + '\t Total completed tasks:\t'+ str(completed_tasks) + '\n'

	total_accepted = 0
	total_completed = 0
	total_response = 0

	for ind in range(0,len(dictList)):
		total_accepted += dictList[ind].get('Average Acceptance Time(hours)')
		total_response += dictList[ind].get('Average Response Time(hours)')
		total_completed += dictList[ind].get('Average Completion Time(hours)')

	if len(dictList) != 0:
		body = body + '\t Average Acceptance Time(in hours):\t'+ str(total_accepted/len(dictList)) + '\n'
		body = body + '\t Average Response Time(hours):\t'+ str(total_response/len(dictList)) + '\n'
		body = body + '\t Average Completion Time(hours):\t'+ str(total_completed/len(dictList)) + '\n'	

	for helper in RECIPIENT_LIST:
		recipient = Helper.objects.get(user__username=helper).user.email
		email_to(recipient, subject, body, files)


	# with open('task-wise.csv', 'w') as csvfile:
	#     fieldnames = ['Task_Id', 'Allocated To', 'Accepted Time(hours)', 'Completed Time(hours)']
	#     writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
	#     writer.writeheader()
	#     total_assigns = Assign.objects.filter(created__gte=timezone.now()-datetime.timedelta(days=7))
	#     for assign in total_assigns:
	#     	accepted_time = 'Not accepted'
	#     	if assign.accepted:
	#     		accepted_time = (int(assign.accepted.strftime('%s'))-int(assign.created.strftime('%s')))/3600
	#     	qanda = QandA.objects.filter(task=assign.action.task)
	#     	completed_time = 'Not completed'
	#     	if qanda:
	#     		qanda_time = qanda[0].created
	#     		completed_time = (int(qanda_time.strftime('%s'))-int(assign.accepted.strftime('%s')))/3600
	#     	writer.writerow({'Task_Id': assign.action.task.id, 'Allocated To': assign.helper.user.username, 'Accepted Time(hours)':accepted_time, 'Completed Time(hours)': completed_time})

'''

# def GetFeedback():
# 	print "Job occured !"

# 	number_of_questions = len(FeedbackType.objects.all())

# 	feedback_objects = Feedback.objects.exclude(current_question=number_of_questions).exclude(isCallRaised=True).order_by('-id')

# 	while (len(Feedback.objects.exclude(current_question=number_of_questions).exclude(isCallRaised=True))!=0):
# 		feedback_obj = Feedback.objects.exclude(current_question=number_of_questions).exclude(isCallRaised = True).order_by('-id')[0]
# 		print "inside while"
# 		print feedback_obj.isCallRaised

# 		if not feedback_obj.isCallRaised:

# 			print "setting isCallRaised to true"
# 			feedback_obj.isCallRaised = True
# 			feedback_obj.save()
# 			contactnumber = feedback_obj.task.call_request.client.client_number
# 			print "Contact number"
# 			print contactnumber
# 			#contactnumber= "8149599012"
# 			appurl="http://safestreet.cse.iitb.ac.in/helplinefeedback/"
# 			apikey="KK7a90e699849af7b22114bb564eae644b"

# 			url = "http://www.kookoo.in/outbound/outbound.php?phone_no="+contactnumber+"&api_key="+apikey+"%20&outbound_version=2&url="+appurl
# 			print "calling to url"
# 			print url
# 			response = urllib2.urlopen(url)
# 			headers = response.info()
# 			time.sleep(5)
# 			print "Sleep done after url call!!"






#################################################################################################

# @periodic_task(
# 	run_every=(crontab(hour=23, minute=30)),
# 	name="call recordings",
# 	ignore_result=True
# )

# def call_recordings():
# 	calls = Call_Forward_Details.objects.filter(status='completed', updated__year=date.today().year,
# 												updated__month=date.today().month, updated__day=date.today().day)
# 	for call in calls:
# 		recording = call.call_recording_name
# 		with open("/tmp/tmpfile.mp3", "wb") as f:
# 			f.write(recording.content)



# # Commenting for not bwing used in application 29Jun17

# from datetime import timedelta

# from django.utils import timezone

# from dtss.celery import app
# from task_manager.helpers import AssignAction, HelperMethods
# from task_manager.models import Action, Assign
# from task_manager.options import (ActionStatusOptions, ActionTypeOptions,
#                                   AssignStatusOptions)


# @app.task
# def new_task_remainder():
#     """
#     New task remainder to helper to accept/reject new task
#     """

#     # Start time below which actions have to be picked
#     start = timezone.localtime(timezone.now()) - timedelta(hours=4)

#     pending_actions = Action.objects.select_related('task__call_request__client').filter(
#         status=ActionStatusOptions.ASSIGN_PENDING,
#         modified__lte=start,
#     )

#     # For each pending action, send remainder
#     for pending_action in pending_actions:

#         # Change action modified timestamp, to track last remainder sent
#         pending_action.save()

#         action_to = ActionTypeOptions()
#         task_type = action_to.get_action_type(pending_action.action_type)
#         data = {
#             "notification": "new_task_pending",
#             "client_number": pending_action.task.call_request.client.client_number,
#             "task_id": pending_action.task.pk,
#             "task_type": task_type,
#         }

#         helper_methods = HelperMethods()
#         helper_methods.send_new_task_notification(action=pending_action, data=data)


# @app.task
# def pending_task_remainder():
#     """
#     Task pending remainder to assigned helper to complete assigned task
#     """

#     # Start time below which assigns have to be picked
#     start = timezone.localtime(timezone.now()) - timedelta(hours=4)

#     pending_assigns = Assign.objects.select_related('action__task__call_request__client').filter(
#         status=AssignStatusOptions.ACCEPTED,
#         modified__lte=start,
#     )

#     # For each pending assign, send remainder
#     for pending_assign in pending_assigns:
#         # Change assign modified timestamp, to track last remainder sent
#         pending_assign.save()

#         action_to = ActionTypeOptions()
#         task_type = action_to.get_action_type(pending_assigns.action.action_type)
#         data = {
#             "notification": "assigned_task_pending",
#             "client_number": pending_assign.action.task.call_request.client.client_number,
#             "task_id": pending_assign.action.task.pk,
#             "task_type": task_type,
#         }

#         gcm_canonical_id = [pending_assign.helper.gcm_canonical_id]
#         helper_methods = HelperMethods()
#         helper_methods.send_gcm_message(gcm_canonical_id, data)


# @app.task
# def complete_timeout():
#     """
#     None of the helpers accepted in given time, leading to new action and assigns
#     """
#     reassign_action_tasks = []

#     # Start time below which assigns have to be picked
#     start = timezone.localtime(timezone.now()) - timedelta(hours=12)

#     timeout_assigns = Assign.objects.select_related('action__task').filter(
#         status=AssignStatusOptions.PENDING,
#         action__status=ActionStatusOptions.ASSIGN_PENDING,
#         created__lte=start,
#     )

#     # For each timed out assign, change status to timeout
#     for timeout_assign in timeout_assigns:
#         timeout_assign.status = AssignStatusOptions.TIMEOUT
#         timeout_assign.save()

#         # If task not in reassign action task list, append
#         if timeout_assign.action.task not in reassign_action_tasks:
#             reassign_action_tasks.append(timeout_assign.action.task)
#             timeout_assign.action.status = ActionStatusOptions.COMPLETE_TIMEOUT
#             timeout_assign.action.save()

#     assign_act = AssignAction()
#     # For all tasks in reassign action, run assign_action helper method
#     for task in reassign_action_tasks:
#         assign_act.assign_action(task)


# @periodic_task(
#     run_every=crontab(minute=0, hour="*/3"),
#     name="assign_timeout",
#     ignore_result=True
# )

# def assign_timeout():
#     """
#     None of the helpers accepted in given time, leading to new action and assigns
#     """
#     reassign_action_tasks = []

#     # Start time below which assigns have to be picked
#     start = timezone.localtime(timezone.now())-timedelta(hours=TIMEOUT_HOURS)
#     print timezone.localtime(timezone.now())-timedelta(hours=TIMEOUT_HOURS)
#     timeout_assigns = Assign.objects.select_related('action__task').filter(
#         status=AssignStatusOptions.PENDING,
#         action__status=ActionStatusOptions.ASSIGN_PENDING,
#         created__lte=start
#     )

#     # For each timed out assign, change status to timeout
#     for timeout_assign in timeout_assigns:
#         timeout_assign.status = AssignStatusOptions.TIMEOUT
#         print timeout_assign
#         timeout_assign.save()

#         # If task not in reassign action task list, append
#         if timeout_assign.action.task not in reassign_action_tasks:
#             reassign_action_tasks.append(timeout_assign.action.task)
#             timeout_assign.action.status = ActionStatusOptions.ASSIGN_TIMEOUT
#             timeout_assign.action.save()

#     assign_act = AssignAction()
#     # For all tasks in reassign action, run assign_action helper method
#     for task in reassign_action_tasks:
#         print task.id
#         if task.id == '218':
#             assign_act.assign_action(task)
