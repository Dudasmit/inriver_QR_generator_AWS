from django.urls import path

from .views import product_list, generate_qr, generate_qr_background, download_all_qr, update_products_from_inriver, download_qr_zip, delete_all_qr
from django.contrib.auth import views as auth_views

from .api_views import generate_qr_api, MyEndpoint
from .views import redirect_by_barcode, barcode_image_view, qr_progress_status, qr_progress_view, custom_logout,generate_qr_old
from django.views.generic import TemplateView

urlpatterns = [
    
    path('', auth_views.LoginView.as_view(template_name="registration/login.html")),
    
    path('logout/', custom_logout, name='custom_logout'),
    path('accounts/profile/', product_list, name='product_list'),
    path('generate_qr/', generate_qr_old, name='generate_qr'),
    
    path('qr-progress/<str:task_id>/', qr_progress_view, name='qr_progress'),
    
    path('api/qr-progress/<str:task_id>/', qr_progress_status),
    
    path('download_qr/<int:product_id>/', download_qr_zip, name='download_qr'),
    path('download_all/', download_all_qr, name='download_all_qr'),
    path('update-from-inriver/', update_products_from_inriver, name='update_from_inriver'),
    path('delete_all_qr/', delete_all_qr, name='delete_all_qr'),
    
    path("barcode-image/<str:name>.png", barcode_image_view, name="barcode_image"),

    
    
    
    path('01/<str:barcode>/', redirect_by_barcode, name='redirect_by_barcode'),
    
    path('api/generate-qr/', generate_qr_api, name='generate_qr_api'),
    path('api/hello/', MyEndpoint.as_view(), name='hello-api'),
]

