from rest_framework_simplejwt.tokens import Token
from rest_framework_simplejwt.settings import api_settings
import uuid

class CustomRefreshToken(Token):
    """
    Custom refresh token class that completely avoids database operations
    to prevent UUID vs bigint type mismatch
    """
    token_type = 'refresh'
    lifetime = api_settings.REFRESH_TOKEN_LIFETIME
    no_copy_claims = (
        api_settings.TOKEN_TYPE_CLAIM,
        'exp',
        # Both of these claims are included even though they may be the same.  This
        # is purely for backwards compatibility.
        'jti', 'refresh_jti',
    )
    access_token_class = None

    @property
    def access_token(self):
        """
        Returns an access token created from this refresh token.  Internally
        uses the AccessToken class in the `access_token_class` attribute.
        """
        if self.access_token_class is None:
            from rest_framework_simplejwt.tokens import AccessToken
            self.access_token_class = AccessToken

        access = self.access_token_class()
        access.set_exp(from_time=self.current_time)

        # Use this refresh token's JTI as the access token's JTI too
        access[api_settings.JTI_CLAIM] = self[api_settings.JTI_CLAIM]

        # Copy all claims (including user ID) from refresh token to access token
        no_copy = self.no_copy_claims
        for claim, value in self.payload.items():
            if claim in no_copy:
                continue
            access[claim] = value

        return access

    @classmethod
    def for_user(cls, user):
        """
        Returns a refresh token for the given user without storing it in the database
        """
        token = cls()

        # Set token JTI and type
        token[api_settings.JTI_CLAIM] = uuid.uuid4().hex

        # Set user ID claim
        user_id = getattr(user, api_settings.USER_ID_FIELD)
        token[api_settings.USER_ID_CLAIM] = str(user_id)

        # Set token expiration
        token.set_exp()

        return token
