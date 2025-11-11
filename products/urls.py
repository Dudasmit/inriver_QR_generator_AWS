from django.urls import path

from .views import product_list,  download_all_qr, update_products_from_inriver, download_qr_zip, delete_all_qr
from django.contrib.auth import views as auth_views

from .api_views import generate_qr_api, MyEndpoint, get_all_generated_qr_codes
from .views import redirect_by_barcode, custom_logout, generate_qr,generate_qr_view

urlpatterns = [
    
    path('', auth_views.LoginView.as_view(template_name="registration/login.html")),
    
    path('logout/', custom_logout, name='custom_logout'),
    path('accounts/profile/', product_list, name='product_list'),
    path('generate_qr/', generate_qr_view, name='generate_qr'),
    
    
    
    path('download_qr/<int:product_id>/', download_qr_zip, name='download_qr'),
    path('download_all/', download_all_qr, name='download_all_qr'),
    path('update-from-inriver/', update_products_from_inriver, name='update_from_inriver'),
    path('delete_all_qr/', delete_all_qr, name='delete_all_qr'),
    

    
    
    
    path('01/<str:barcode>/', redirect_by_barcode, name='redirect_by_barcode'),
    
    path('api/generate-qr/', generate_qr_api, name='generate_qr_api'),
    path('api/get_all_generated_qr_codes/', get_all_generated_qr_codes, name='get_all_generated_qr_codes'),

    
    path('api/hello/', MyEndpoint.as_view(), name='hello-api'),
    
    
]

