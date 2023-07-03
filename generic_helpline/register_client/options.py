"""
Helper class to manage status options of models
"""


class ClientStatusOptions:
    """
    Status options available to Client
    """
    ACTIVE = 1
    BLOCKED = 2
    STATUS_CHOICES = (
        (ACTIVE, 'Active'),
        (BLOCKED, 'Blocked'),
    )