from django.contrib.auth.models import User
from django.test import TestCase, RequestFactory
from rest_framework import status
from rest_framework.test import force_authenticate

from ivr.models import Language
from management.models import HelpLine, HelperCategory, HelplineSetting
from register_helper.models import Helper
from register_helper.options import LoginStatus
from registercall.models import Task
from registercall.views import RegisterCall
from wwh_form_delivery import views, util
from wwh_form_delivery.models import WhatsAppUser, WhatsAppMessage


class FormTestCase(TestCase):

    def setUp(self):
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
        hcat1.name = 'below12'
        hcat1.save()

        hcat2 = HelperCategory()
        hcat2.helpline = help
        hcat2.name = 'above12'
        hcat2.save()

        hcat3 = HelperCategory()
        hcat3.helpline = help
        hcat3.name = 'women'
        hcat3.save()

        hcat4 = HelperCategory()
        hcat4.helpline = help
        hcat4.name = 'others'
        hcat4.save()

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
        h1.category.add(hcat4)
        h1.language.add(lg1)
        h1.language.add(lg2)
        h1.language.add(lg3)
        h1.helper_number = "8866879841"
        h1.gender = 'Male'
        h1.college_name = 'IITB'
        h1.login_status = LoginStatus.LOGGED_IN
        h1.save()

        wa_user = WhatsAppUser()
        wa_user.base32 = util.get_random_base32()
        wa_user.otp = util.get_new_otp(wa_user.base32)
        wa_user.contact = 9999999999
        wa_user.save()

    def test_query_form(self):
        otp = WhatsAppUser.objects.first().otp
        request = self.factory.post('/hospital/kem/query_form_accept/', {
            "name": "Chirag Chauhan",
            "location": "Ahmedabad",
            "language": "English",
            "message": "Test message 1",
            "category": "below12",
            "phone": "9999999999",
            "task_type": "non_direct",
            "otp": otp,
        }, format='form-data')
        request.FILES['files'] = []
        response = views.query_form_accept(request)

        task_id = Task.objects.first().id

        request = self.factory.post('/hospital/kem/api/whatsapp_message', {
            "text": "Doctor Reply-1",
            "wwh_task_id": task_id,
            "language": "English",
            "from_doctor": True,
            "category": "below12",
            "contact": "9999999999",
            "task_type": "non_direct",
        }, format='json')
        force_authenticate(request, user=self.user)
        response = views.WhatsAppMessageListView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
