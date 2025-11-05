# api_views.py
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from .serializers import GenerateQRInputSerializer
from .models import Product
from .filters import ProductFilter
from .views import create_and_save_qr_code_eps
import os
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
import base64
from drf_yasg import openapi

token_param = openapi.Parameter(
    name='Authorization',
    in_=openapi.IN_HEADER,
    description='Token {your_token}',
    type=openapi.TYPE_STRING
)




class MyEndpoint(APIView):
    def get(self, request):
        return Response({"message": "Привет из API!"})


    


@swagger_auto_schema(
    manual_parameters=[token_param],
    method='post',
    request_body=GenerateQRInputSerializer,
    operation_description="Генерация QR-кодов для выбранных продуктов",
    responses={200: "Успешно", 400: "Ошибка запроса"}
)
@api_view(['POST'])
@authentication_classes([TokenAuthentication])
def generate_qr_api(request):
    serializer = GenerateQRInputSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)

    data = serializer.validated_data
    product_ids = data.get("product_ids", [])
    select_all = data.get("select_all", False)
    include_barcode = data.get("include_barcode", False)
    domain = data.get("domain")

    if not product_ids and not select_all:
        return Response({"error": "No products selected"}, status=400)

    if select_all:
        session_filter = request.session.get("last_filter", {})
        product_filter = ProductFilter(session_filter, queryset=Product.objects.all())
        products = product_filter.qs
    else:
        products = Product.objects.filter(name__in=product_ids)

    folder = "qrcodes"
    os.makedirs(os.path.join(settings.MEDIA_ROOT, folder), exist_ok=True)

    success_count = 0
    generated_files = []

    for product in products:
        url = f"https://{domain}/01/"
        success = create_and_save_qr_code_eps(url, product.name, product.barcode, include_barcode, folder)

        if success:
            success_count += 1
            filename = f"{product.name.replace(' ', '_')}.png"
            file_path = os.path.join(settings.MEDIA_ROOT, folder, filename)

            # Чтение PNG-файла и кодирование в base64
            try:
                with open(file_path, "rb") as image_file:
                    encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                    generated_files.append({
                        "product": product.name,
                        "filename": filename,
                        "image_base64": encoded_string
                    })
            except Exception as e:
                generated_files.append({
                    "product": product.name,
                    "filename": filename,
                    "error": f"Не удалось прочитать PNG-файл: {str(e)}"
                })

    return Response({
        "success": True,
        "generated": success_count,
        "files": generated_files
    })


