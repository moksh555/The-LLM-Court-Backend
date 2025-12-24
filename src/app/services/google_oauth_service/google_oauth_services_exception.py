class Google_OAuth_Error(Exception):
    """Base Google Auth Error"""

class StateMismatchError(Google_OAuth_Error):
    """States from callback and cookie does not match: Google Oauth Service"""

class NoCookieStateError(Google_OAuth_Error):
    """The state was not saved in Cookie suring login!"""

class MissingSUBError(Google_OAuth_Error):
    """Invalid Google token: missing sub."""

class EmailNotVerfiedError(Google_OAuth_Error):
    """Google email not verified."""



# class MissingSUBError(Google_OAuth_Error):
