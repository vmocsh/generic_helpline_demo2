class HelperStatusOptions:
    """
    Status options available to Helper
    """
    ACTIVE = 1
    BLOCKED = 2
    STATUS_CHOICES = (
        (ACTIVE, 'Active'),
        (BLOCKED, 'Blocked'),
    )


class LoginStatus:
    """
        Login Status options of Helper
    """
    LOGGED_IN = 1
    LOGGED_OUT = 2
    PENDING = 3
    STATUS_CHOICES = (
        (LOGGED_IN, 'LOGGED_IN'),
        (LOGGED_OUT, 'LOGGED_OUT'),
        (PENDING, 'PENDING'),
    )


class HelperLevel:
    """
    Helper level : primary and secondary. Task allocated to primary helpers first
    """
    PRIMARY = 1
    SECONDARY = 2
    LEVEL_CHOICES = (
        (PRIMARY, 'PRIMARY'),
        (SECONDARY, 'SECONDARY'),
    )


class HelperType:
    """
    Helper type : direct and indirect. Task allocated to direct helpers first
    """
    DIRECT = 1
    INDIRECT = 2
    TYPE_CHOICES = (
        (DIRECT, 'DIRECT'),
        (INDIRECT, 'INDIRECT'),
    )
