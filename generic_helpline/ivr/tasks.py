from celery.decorators import periodic_task
from celery.task.schedules import crontab
from celery.utils.log import get_task_logger
from ivr.models import FeedbackType, Feedback

logger = get_task_logger(__name__)
from urllib.request import urlopen

'''
@periodic_task(
    run_every=(crontab(hour=10, minute=34)),
    name="GetFeedback",
    ignore_result=True
)


def GetFeedback():
	print ("INFO: GetFeedback Job occured !")
	number_of_questions = len(FeedbackType.objects.all())

	while len(Feedback.objects.exclude(current_question=number_of_questions).exclude(isCallRaised=True))!=0:
		feedback_obj = Feedback.objects.exclude(current_question=number_of_questions).exclude(isCallRaised = True).order_by('-id')[0]


		if not feedback_obj.isCallRaised:
			feedback_obj.isCallRaised = True
			feedback_obj.save()
			contactnumber = feedback_obj.task.call_request.client.client_number
			appurl="http://safestreet.cse.iitb.ac.in/helplinefeedback/"
			apikey="KKdfb62acea9b25be2363b8e3a4281d0ee"

			url = "http://www.kookoo.in/outbound/outbound.php?phone_no="+contactnumber+"&api_key="+apikey+"%20&outbound_version=2&url="+appurl
			print (url)
			response = urlopen(url)
			headers = response.info()
'''


'''
@periodic_task(
    run_every=(crontab(hour=16, minute=44)),
    name="ResetFeedbacks",
    ignore_result=True
)
def ResetFeedbacks():
	print ("INFO: ResetFeedbacks Job occured !")
	while len(Feedback.objects.filter(isFeedbackTaken=False).filter(isCallRaised=True))!=0:
		feedback_obj = Feedback.objects.filter(isFeedbackTaken=False).filter(isCallRaised=True).order_by('-id')[0]
		feedback_obj.isCallRaised = False
		feedback_obj.current_question = 0
		feedback_obj.save()
'''
