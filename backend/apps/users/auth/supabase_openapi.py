from drf_spectacular.extensions import OpenApiAuthenticationExtension
from apps.users.auth.supabase import SupabaseJWTAuthentication

class SupabaseAuthenticationScheme(OpenApiAuthenticationExtension):
    target_class = 'apps.users.auth.supabase.SupabaseJWTAuthentication'
    name = 'bearerAuth'

    def get_security_definition(self, auto_schema):
        return {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'JWT',
        }
