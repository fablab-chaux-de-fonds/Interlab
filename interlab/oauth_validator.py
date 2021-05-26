from oauth2_provider.oauth2_validators import OAuth2Validator

class CustomOAuth2Validator(OAuth2Validator):

    def get_additional_claims(self, request):
        return {
            'sub': request.user.username,
            'mail': request.user.email,
            'name': ' '.join([request.user.first_name, request.user.last_name]),
            'given_name': request.user.first_name,
            'last_name': request.user.last_name,
            'groups': [g.name for g in request.user.groups.all()],
            'is_admin': request.user.is_staff
        }
