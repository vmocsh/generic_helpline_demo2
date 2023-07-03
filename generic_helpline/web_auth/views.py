from django.shortcuts import render
from django.urls import reverse
from django.views.generic import View
from django.contrib.auth import authenticate,login,logout
from django.http import HttpResponseRedirect

# Create your views here.


class Login(View):

    def get(self, request):
        return render(request, 'login.html', {})

    def post(self, request):
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user:
            if user.is_staff:
                login(request, user)
                return HttpResponseRedirect(reverse('dashboard:home'))
            else:
                return render(request, 'login.html', {'error': 'You are do not have Admin Privileges'})
        else:
            return render(request, 'login.html', {'error': 'Incorrect Credentials'})


class Logout(View):

    def get(self, request):
        logout(request)
        return HttpResponseRedirect(reverse('web_auth:login'))

