"""
Register Call Views
"""
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from management.models import HelpLine
from .models import Helper
from .serializers import HelperSerializer


class RegisterHelper(APIView):
    """
    Register call used to handle incoming call requests
    """

    def register_call(self, data):
        """
        Register call handler
        """
        helpline = data.get("helpline")
        username = data.get("username")
        first_name = data.get("first_name")
        last_name = data.get("last_name")
        password = data.get("password")
        phone_no = data.get("phone_no")
        email = data.get("email")
        gender = data.get("gender")
        college_name = data.get("college_name")
        gcm_canonical_id = data.get('gcm_canonical_id')

        # Creating new helper object
        helper = Helper(
            gcm_canonical_id=gcm_canonical_id,
        )

        # Adding multiple categories for newly created helper
        # present_hc = []
        #
        # categories = data.get('category').split(',')
        # helper_categories = HelperCategory.objects.filter(name__in=categories)
        #
        # for helper_category in helper_categories:
        #     present_hc.append(helper_category.name)

        # If all categories sent are not present
        # if len(set(categories) - set(present_hc)):
        #     return False
        user = User(username=username, first_name=first_name, last_name=last_name, email=email)
        user.set_password(password)
        user.save()

        # Get helpline
        helpline = get_object_or_404(HelpLine, name=helpline)
        helper.user = user
        helper.helper_number = phone_no
        helper.college_name = college_name
        helper.gender = gender
        helper.helpline = helpline
        helper.save()
        # for helper_category in helper_categories:
        #     helper.category.add(helper_category)

        # Create a user profile

        return True

    def post(self, request):
        """
        Post request handler
        """
        data = request.data
        serializer = HelperSerializer(data=data)
        username = data.get("username")
        user = User.objects.filter(username=username)
        if user:
            return Response({"notification": "user already exists"}, status=200)
        if serializer.is_valid():

            # If new helper registered successfully
            if self.register_call(data=data):
                return Response({"notification": "success"}, status=200)
            # If sent category is invalid
            else:
                return Response({"notification": "invalid_category"}, status=200)

        # If invalid data sent
        else:
            return Response({"notification": "failed"}, status=200)



