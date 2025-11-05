from rest_framework import permissions
from rest_framework.authentication import TokenAuthentication
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


schema_view = get_schema_view(
   
   
   openapi.Info(
      title="Product QR API",
      default_version='v1',
      description="API для генерации QR-кодов товаров",
      contact=openapi.Contact(email="support@example.com"),
   ),
   public=True,
   permission_classes=[permissions.AllowAny],
   authentication_classes=(TokenAuthentication,),

   #url='https://inriverqr-63c10a36ae10.herokuapp.com/',
)