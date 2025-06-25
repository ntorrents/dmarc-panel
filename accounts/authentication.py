from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import get_user_model

User = get_user_model()

class CookieJWTAuthentication(JWTAuthentication):
    """
    Custom JWT authentication that reads tokens from HttpOnly cookies
    """
    def authenticate(self, request):
        # First try to get token from cookie
        raw_token = request.COOKIES.get('access_token')
        
        if raw_token is None:
            # Fallback to header authentication for API clients
            header = self.get_header(request)
            if header is None:
                return None
            raw_token = self.get_raw_token(header)
        
        if raw_token is None:
            return None

        try:
            validated_token = self.get_validated_token(raw_token)
            user = self.get_user(validated_token)
            
            # Check if user is still active
            if not user.activo:
                return None
                
            return (user, validated_token)
        except TokenError:
            return None

    def get_user(self, validated_token):
        """
        Override to use UUID instead of integer user ID
        """
        try:
            user_id = validated_token['user_id']
        except KeyError:
            raise InvalidToken('Token contained no recognizable user identification')

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise InvalidToken('User not found')

        if not user.is_active:
            raise InvalidToken('User is inactive')

        return user