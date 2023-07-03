"""
Script for register helper test cases
"""
import json

from django.test import TestCase
from django.utils.six import BytesIO
from rest_framework.parsers import JSONParser

from registercall.models import HelperCategory


class RegisterHelperTest(TestCase):
    """
    Register helper test class
    """

    register_helper_url = "/RegisterHelper/"

    def setUp(self):
        """
        Setup for register helper
        """

        HelperCategory.objects.create(name="General")
        HelperCategory.objects.create(name="Education")
        HelperCategory.objects.create(name="Health")

    def register_helper(self, first_name, last_name, category,
                        helper_number, gcm_canonical_id):
        """
        Creates register requests
        """
        content_type = "application/json"

        response = self.client.post(
            self.register_helper_url,
            json.dumps({
                'first_name': first_name,
                'last_name': last_name,
                'helper_number': helper_number,
                'gcm_canonical_id': gcm_canonical_id,
                'category': category,
            }),
            content_type=content_type,
        )
        return response

    def test_create_helper(self):
        """
        Valid helper creation
        """
        response = self.register_helper(
            first_name="Prashanth",
            last_name="P",
            helper_number="+919444870256",
            gcm_canonical_id="ABC",
            category="General,Health",
        )
        stream = BytesIO(response.content)
        data = JSONParser().parse(stream)
        self.assertEqual(data.get("notification"), "new_helper_registered")
        self.assertEqual(response.status_code, 200)

    def test_missing_data(self):
        """
        invalid helper creation
        """
        response = self.register_helper(
            first_name="Prashanth",
            last_name="P",
            helper_number=None,
            gcm_canonical_id="ABC",
            category="General,Health",
        )
        stream = BytesIO(response.content)
        data = JSONParser().parse(stream)
        self.assertEqual(data.get("notification"), "bad_request")

    def test_invalid_category(self):
        """
        invalid helper category
        """
        response = self.register_helper(
            first_name="Prashanth",
            last_name="P",
            helper_number="+919444870256",
            gcm_canonical_id="ABC",
            category="General,InvalidCategory",
        )
        stream = BytesIO(response.content)
        data = JSONParser().parse(stream)
        self.assertEqual(data.get("notification"), "invalid_category")
