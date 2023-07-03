import pyotp
from django.utils import timezone

from registercall.models import Task
from wwh_form_delivery.models import WhatsAppUser, WhatsAppMessage
from .forms import ContactForm


def get_random_base32():
    return pyotp.random_base32()


def get_new_otp(base32):
    totp = pyotp.TOTP(base32, interval=1800)
    return totp.now()


def verify(base32, otp):
    totp = pyotp.TOTP(base32, interval=1800)
    return totp.verify(otp)


def update_user_and_messages(form, file_list, wwh_task_id):
    f_client_name = form.cleaned_data['name']
    f_otp = form.cleaned_data['otp']
    f_location = form.cleaned_data['location']
    f_language = form.cleaned_data['language']
    f_message = form.cleaned_data['message']

    # update user record
    user_obj = WhatsAppUser.objects.filter(otp=f_otp).first()
    user_obj.name = f_client_name
    user_obj.location = f_location
    user_obj.save()

    wwh_task = Task.objects.get(id=wwh_task_id)

    # create message records
    message_obj = WhatsAppMessage(text=f_message, language=f_language, sent=1,
                                  wwh_task_id=wwh_task, from_doctor=False,
                                  contact=user_obj)
    message_obj.save()
    for file in file_list:
        msg_obj = WhatsAppMessage(text="", sent=1, from_doctor=False, attachment=file,
                                  contact=user_obj, wwh_task_id=wwh_task)
        msg_obj.save()


def build_form(task_id, otp):
    user = WhatsAppUser.objects.filter(otp=otp).first()
    if int(task_id) == 0:
        if user.name:
            # User wants to fill a new form and has filled several old forms
            form = ContactForm(
                initial={'name': user.name, 'otp': otp, 'contact': user.contact, 'location': user.location,
                            'category': None,
                            'language': None, 'message': None, 'files': None})
        else:
            # User wants to fill a new form and has not filled any form before
            form = ContactForm(
                initial={'name': None, 'otp': otp, 'contact': user.contact, 'location': None, 'category': None,
                            'language': None, 'message': None, 'files': None})
        return form, None

    previous_message_objects = WhatsAppMessage.objects.filter(wwh_task_id=task_id)
    previous_messages = []

    for i in range(len(previous_message_objects)):
        temp = {}
        if previous_message_objects[i].from_doctor:
            # previous_messages.append("Doctor: " + str(previous_message_objects[i].text))
            temp['username'] = 'Doctor'
        else:
            temp['username'] = user.name

        if previous_message_objects[i].attachment:
            temp['url'] = previous_message_objects[i].attachment.url
            temp['filename'] = previous_message_objects[i].attachment.name
            temp['type'] = 'attachment'
        else:
            temp['text'] = previous_message_objects[i].text
            temp['type'] = 'text'

        previous_messages.append(temp)

    task = Task.objects.filter(id=task_id).first()
    if len(previous_messages) == 0:
        form = ContactForm(initial={'name': user.name, 'otp': otp, 'contact': user.contact, 'location': user.location,
                                    'category': task.category,
                                    'language': None, 'previous_messages': None, 'message': None, 'files': None})
        return form, None

    form = ContactForm(
        initial={'name': user.name, 'otp': otp, 'contact': user.contact, 'location': user.location,
                 'category': task.category,
                 'language': previous_message_objects.first().language, 'previous_messages': previous_messages,
                 'message': None, 'files': None})

    return form, previous_messages
