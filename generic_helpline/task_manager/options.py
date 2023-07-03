"""
Helper class to manage options of models in task manager app
"""


class ActionTypeOptions:
    """
    Type options available to Action
    """
    PRIMARY = 1
    SPECIALIST = 2
    SPECIALIST_CONFIRM = 3
    FEEDBACK = 4

    ACTION_CHOICES = (
        (PRIMARY, 'Primary'),
        (SPECIALIST, 'Specialist'),
        (SPECIALIST_CONFIRM, 'Specialist Confirm'),
        (FEEDBACK, 'Feedback'),
    )

    def get_action_type(self, choice):
        """
        Returns string for choice
        """
        return ActionTypeOptions.ACTION_CHOICES[int(choice)-1][1]


class ActionStatusOptions:
    """
    Status options available to Action
    """

    ASSIGN_PENDING = 1
    ASSIGNED = 2
    ASSIGN_TIMEOUT = 3
    REJECTED = 4
    COMPLETE_TIMEOUT = 5
    COMPLETED = 6

    STATUS_CHOICES = (
        (ASSIGN_PENDING, 'Assign Pending'),
        (ASSIGNED, 'Assigned'),
        (ASSIGN_TIMEOUT, 'Assigned Timeout'),
        (REJECTED, 'Rejected'),
        (COMPLETE_TIMEOUT, 'Complete Timeout'),
        (COMPLETED, 'Completed'),
    )


class AssignStatusOptions:
    """
    Status options available to Assign
    """

    PENDING = 1
    ACCEPTED = 2
    REJECTED = 3
    TIMEOUT = 4
    CLOSED = 5
    COMPLETED = 6
    REALLOCATED = 7
    FOLLOW_UP_ACCEPTED = 8
    FOLLOW_UP_COMPLETED = 9

    STATUS_CHOICES = (
        (PENDING, 'Pending'),
        (ACCEPTED, 'Accepted'),
        (REJECTED, 'Rejected'),
        (TIMEOUT, 'Timeout'),
        (CLOSED, 'Closed'),
        (COMPLETED, 'Completed'),
        (REALLOCATED, 'Reallocated'),
        (FOLLOW_UP_ACCEPTED, 'FAccepted'),
        (FOLLOW_UP_COMPLETED, 'FCompleted')
    )

    def get_status(self, choice):
        """
        Returns string for choice
        """
        return AssignStatusOptions.STATUS_CHOICES[int(choice)-1][1]
