from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.views.generic import View
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.send_email import email_to
from constants import BASE_URL
from register_helper.models import Helper
from register_helper.options import LoginStatus
from .models import Forgot_Password


# Create your views here.
class Login(APIView):

    def post(self, request):
        data = request.data
        username = data.get("username")
        password = data.get("password")
        print("HERE------>AUTH")
        user = authenticate(username=username, password=password)
        print(user)
        if user is not None:
            helper = get_object_or_404(Helper, user=user)
            if helper.login_status != LoginStatus.PENDING:
                helper.login_status = LoginStatus.LOGGED_IN
                helper.save()
                if helper.login_prevstatus == LoginStatus.PENDING:
                    return Response({"notification": "firstlogin", "is_helper_anonymous": helper.is_anonymous}, status=200)
                else:
                    return Response({"notification": "successful", "is_helper_anonymous": helper.is_anonymous}, status=200)
            else:
                return Response({"notification": "pending"}, status=200)
        else:
            return Response({"notification": "failed"}, status=200)


class Logout(APIView):

    def post(self, request):
        data = request.data
        username = data.get("username")
        user = get_object_or_404(User, username=username)
        if user is not None:
            helper = get_object_or_404(Helper, user=user)
            helper.login_status = LoginStatus.LOGGED_OUT
            helper.save()
            return Response({"notification": "successful"}, status=200)
        else:
            return Response({"notification": "failed"}, status=200)


class GenerateResetPassword(APIView):
    def post(self, request):
        data = request.data
        username = data.get("username")
        email = data.get("email")
        user = get_object_or_404(User, username=username,email=email)
        if user is not None:
            forgot_password = Forgot_Password(user=user)
            forgot_password.save()
            body = "Click on the link to reset password" + BASE_URL + "auth/reset_password/"+str(forgot_password.id)+"/"
            email_to(recipient=user.email, subject="Password Reset", body=body, files=None)
            return Response({"notification": "successful"}, status=200)
        else:
            return Response({"notification": "failed"}, status=200)


class ResetPassword(View):

    def get(self, request, id):
        return render(request, "reset_password.html", {})

    def post(self, request, id):
        password = request.POST['password']
        fp = get_object_or_404(Forgot_Password, id=id)
        fp.user.set_password(password)
        fp.user.save()
        fp.delete()
        return render(request, "password_change_success.html", {})
