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


class CallRequestStatusOptions:
    """
    Status options available to Call Requests
    """
    CREATED = 1
    BLOCKED = 2
    MERGED = 3
    INVALID_HELPLINE = 0
    STATUS_CHOICES = (
        (CREATED, 'Created'),
        (BLOCKED, 'Blocked'),
        (MERGED, 'Merged'),
    )


class TaskStatusOptions:
    """
    Status options available to Tasks
    """
    PENDING = 1
    COMPLETED = 2
    REJECTED = 3
    STATUS_CHOICES = (
        (PENDING, 'Pending'),
        (COMPLETED, 'Completed'),
        (REJECTED, 'Rejected'),
    )


class TaskType:

    DIRECT = 1
    INDIRECT = 2
    TYPE_CHOICES = (
        (DIRECT, 'DIRECT'),
        (INDIRECT, 'INDIRECT'),
    )
