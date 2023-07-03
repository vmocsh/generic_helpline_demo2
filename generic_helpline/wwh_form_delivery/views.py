import loguru
import requests
from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template import loader
from rest_framework import status, generics
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from register_client.models import Client
from registercall.models import Task, CallRequest
from registercall.options import TaskStatusOptions, CallRequestStatusOptions

from wwh_form_delivery import util, service
from wwh_form_delivery.models import WhatsAppUser, WhatsAppMessage 
from .forms import ContactForm
from management.models import HelperCategory
from ivr.models import Language
from .serializers import WhatsAppUserSerializer, WhatsAppMessageSerializer
from loguru import logger 



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_otp(request):
    wa_user = WhatsAppUser.objects.filter(contact=request.data['contact']).first()
    if wa_user:
        if util.verify(wa_user.base32, otp=wa_user.otp):
            logger.info('existing OPT is valid')
            # verified
            pass
        else:
            # refresh otp
            logger.info('refreshing existing OTP')
            new_otp = util.get_new_otp(wa_user.base32)
            wa_user.otp = new_otp
    else:
        # new user
        logger.info('creating new user with OTP')
        wa_user = WhatsAppUser()
        wa_user.base32 = util.get_random_base32()
        wa_user.otp = util.get_new_otp(wa_user.base32)
        wa_user.contact = request.data['contact']
    wa_user.save()
    data = {'contact': wa_user.contact, 'otp': wa_user.otp}

    return Response(data)


def submit_form(request):
    if request.method == 'POST':
        form = ContactForm(request.POST, request.FILES)
        if form.is_valid():

            data = {
                'client_name': form.cleaned_data['name'],
                'location': form.cleaned_data['location'],
                'language': form.cleaned_data['language'],
                'message': form.cleaned_data['message'],
                'category': form.cleaned_data['category'],
                'contact': form.cleaned_data['contact']
            }

            wwh_task_id = service.create_or_update_task(data)

            try:
                file_list = request.FILES.getlist('files')
            except:
                file_list = []
            util.update_user_and_messages(form, file_list, wwh_task_id)
            message = 'Your response has been recorded. We will get back to you shortly!'

        else:
            print("Form Invalid")
            print("Form Errors : ", str(form.errors))

            message = 'Form has errors. Please try again!'

    else:
        message = 'This url does not support GET request!'

    template = loader.get_template("form_response.html")
    context = {'message': message}
    return HttpResponse(template.render(context, request))


def load_task(request, task_id, otp):
    if request.method == 'GET':
        form = []
        try:
            form, previous_messages = util.build_form(task_id, otp)
            available_categories = HelperCategory.objects.all()
            available_categories_list = []
            for category in available_categories:
                available_categories_list.append(str(category))

            available_languages = Language.objects.all()
            available_languages_list = []
            for language in available_languages:
                available_languages_list.append(str(language))

            return render(request, 'query_form.html', {'form': form, 'available_categories_list' : available_categories_list, 'available_languages_list': available_languages_list,'previous_messages': previous_messages})
        except Exception:
            message = 'Exception occured while fetching previous forms!'

    else:
        message = 'This url does not support POST request!'

    template = loader.get_template("form_response.html")
    context = {'message': message}

    return HttpResponse(template.render(context, request))


def generate_otp(request):
    if request.method == 'POST':

        ''' Begin reCAPTCHA validation '''
        recaptcha_response = request.POST.get('g-recaptcha-response')
        data = {
            'secret': settings.GOOGLE_RECAPTCHA_SECRET_KEY,
            'response': recaptcha_response
        }
        r = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)
        result = r.json()
        ''' End reCAPTCHA validation '''

        if result['success']:
            try:
                wa_user = WhatsAppUser.objects.filter(contact=request.POST['contact']).first()
                if wa_user:
                    if util.verify(base32=wa_user.base32, otp=wa_user.otp):
                        # verified
                        pass
                    else:
                        # refresh otp
                        new_otp = util.get_new_otp(wa_user.base32)
                        wa_user.otp = new_otp
                    wa_user.is_updated = True
                    wa_user.save()
                    # TODO: show a message telling the user to check for OTP on their WhatsApp
                else:
                    # new user
                    wa_user = WhatsAppUser()
                    wa_user.base32 = util.get_random_base32()
                    wa_user.otp = util.get_new_otp(wa_user.base32)
                    wa_user.contact = request.POST['contact']
                    wa_user.is_updated = True
                    wa_user.save()

                template = loader.get_template("login_otp.html")
                context = {}
            except Exception as e:
                message = 'You have entered invalid number!'
                print(e)
                context = {'message': message}
                template = loader.get_template("form_response.html")
        else:
            message = 'There was an issue with Captcha Verification'
            context = {'message': message}
            template = loader.get_template("form_response.html")

    else:
        template = loader.get_template("generate_otp.html")
        context = {}

    return HttpResponse(template.render(context, request))


class UpdatedUserList(generics.ListAPIView):
    serializer_class = WhatsAppUserSerializer
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]

    def get_queryset(self):
        queryset = WhatsAppUser.objects.filter(is_updated=True)
        return queryset


class WhatsAppUserView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        wa_user = WhatsAppUser.objects.filter(contact=request.data['contact']).first()
        serializer = WhatsAppUserSerializer(wa_user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def validate_credentials(request):
    if request.method == 'POST':

        ''' Begin reCAPTCHA validation '''
        recaptcha_response = request.POST.get('g-recaptcha-response')
        data = {
            'secret': settings.GOOGLE_RECAPTCHA_SECRET_KEY,
            'response': recaptcha_response
        }
        r = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)
        result = r.json()
        ''' End reCAPTCHA validation '''

        if result['success']:
            logger.info('captcha verified')
            submitted_otp = request.POST['otp']
            user = WhatsAppUser.objects.filter(otp=submitted_otp).first()
            try:
                submitted_otp = request.POST['otp']
                if util.verify(user.base32, submitted_otp):
                    logger.info('opt verified!')
                    client = Client.objects.filter(client_number=user.contact).first()
                    pending_tasks = Task.objects.filter(
                        status=TaskStatusOptions.PENDING,
                        call_request__client=client)

                    return render(request, 'task_list.html', {'tasks': pending_tasks, 'otp': submitted_otp})

                else:
                    logger.info('failed to verify otp')
                    message = 'Invalid OTP Entered'

            except Exception as e:
                message = 'Exception occured while verifying otp!'
                logger.error(str(message))

        else:
            logger.debug('failed to verify captcha')
            message = 'There was an issue with Captcha Verification'

        template = loader.get_template("form_response.html")
        context = {'message': message}

        return HttpResponse(template.render(context, request))


class WhatsAppMessageListView(generics.ListCreateAPIView):
    serializer_class = WhatsAppMessageSerializer
    permission_classes = [IsAuthenticated]
    queryset = WhatsAppMessage.objects.all()
    renderer_classes = [JSONRenderer]

    def get_queryset(self):
        wwh_task_id = self.request.query_params.get('task_id')
        if wwh_task_id:
            # Android App
            queryset = WhatsAppMessage.objects.filter(wwh_task_id=wwh_task_id)
        else:
            # Wappy
            queryset = WhatsAppMessage.objects.filter(sent=False)
        return queryset


class WhatsAppMessageDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = WhatsAppMessage.objects.all()
    serializer_class = WhatsAppMessageSerializer
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]
