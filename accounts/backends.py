from django.contrib.auth import get_user_model


class PhoneOTPBackend:
    """
    Authenticates a user purely by phone number, assuming OTP verification
    (or the no-provider fallback) already happened in the login view. This
    backend never checks a password — BabyCal has no password-based login.
    """

    def authenticate(self, request, phone=None, **kwargs):
        if not phone:
            return None
        User = get_user_model()
        try:
            user = User.objects.get(phone=phone, is_active=True)
        except User.DoesNotExist:
            return None
        return user

    def get_user(self, user_id):
        User = get_user_model()
        try:
            return User.objects.get(pk=user_id, is_active=True)
        except User.DoesNotExist:
            return None
