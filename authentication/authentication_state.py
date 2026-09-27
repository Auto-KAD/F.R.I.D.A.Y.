from enum import Enum


class AuthenticationState(Enum):

    LOCKED = "LOCKED"

    AUTHENTICATING = "AUTHENTICATING"

    AUTHENTICATED = "AUTHENTICATED"

    DENIED = "DENIED"