from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.shortcuts import redirect
from .models import Product
from .filters import ProductFilter
import qrcode
import tempfile
import shutil

import os
from django.conf import settings
from django.http import HttpResponse, FileResponse, Http404, JsonResponse
import requests
from PIL import Image
from io import BytesIO
import json
import zipfile
from django.core.paginator import Paginator
from datetime import date
from zipfile import ZipFile
from django.template.loader import render_to_string
from .qr_utils import create_and_save_qr_code_eps, extract_qr_data_from_image
from django.contrib.auth import authenticate, login,logout
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
import uuid
from .models import QRTaskStatus

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import boto3

TEMP_QR_DIR = os.path.join(tempfile.gettempdir(), 'qr_codes')
os.makedirs(TEMP_QR_DIR, exist_ok=True)







BUCKET_NAME = os.getenv("BUCKET_NAME")
S3_FOLDER = os.getenv("S3_FOLDER")

s3 = boto3.client("s3")

@csrf_exempt
@require_POST
def custom_logout(request):
    logout(request)
    return redirect('/') 



@login_required(login_url='login')
def product_list(request):
    if not request.user.is_authenticated:
        return redirect("/")

    # Основной queryset
    queryset = Product.objects.all().order_by('name')

    # Фильтр: только товары без QR-кодов
    show_without_qr = request.GET.get("without_qr") == "1"
    
    
    if show_without_qr:
        queryset = queryset.filter(qr_image_url__isnull= True)

    
    # Применение фильтров
    product_filter = ProductFilter(request.GET, queryset=queryset)

    # Пагинация
    paginator = Paginator(product_filter.qs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Проверка: есть ли QR-коды вообще
    
    
    has_qr_codes = Product.objects.exclude(qr_code_url__in=[None, '']).exists()
   
    
    

    # AJAX-запрос от infinite scroll
    #if request.headers.get('x-requested-with') == 'XMLHttpRequest':
    #    html = render_to_string('products/includes/product_rows.html', {'page_obj': page_obj})
    #    return JsonResponse({
    #        'html': html,
    #        'has_next': page_obj.has_next()
    #    })

    # Рендер полной страницы
    return render(request, 'products/product_list.html', {
        'filter': product_filter,
        'page_obj': page_obj,
        'has_qr_codes': has_qr_codes,
        'show_without_qr': show_without_qr,
    })

def redirect_by_barcode(request, barcode):
    product = get_object_or_404(Product, barcode=barcode[1:])
    return redirect(f"{os.getenv("REDERECT_URL")}{product.name}")

def delete_all_qr(request):
    qr_dir = os.path.join(settings.MEDIA_ROOT, 'qrcodes')  # или 'qr_codes', если используется такая папка

    if os.path.exists(qr_dir):
        shutil.rmtree(qr_dir)
        os.makedirs(qr_dir)  # Создаём заново пустую папку, если нужно
        messages.success(request, "All QR codes have been successfully removed.")
    else:
        messages.info(request, "No files were found for deletion.")
        
        
    response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=S3_FOLDER)

    if "Contents" not in response:
        messages.info(request, "No QR codes were found for deletion.")
        return

    # Формируем список ключей для удаления
    objects_to_delete = [
        {"Key": obj["Key"]}
        for obj in response["Contents"]
        if not obj["Key"].endswith("/")  # пропускаем "папку"
    ]

    if not objects_to_delete:
        messages.info(request, "No QR codes were found for deletion.")
        return

    # Удаляем все объекты
    s3.delete_objects(
        Bucket=BUCKET_NAME,
        Delete={"Objects": objects_to_delete}
    )
    Product.objects.filter(qr_code_url__isnull=False).update(qr_code_url=None)
    Product.objects.filter(qr_image_url__isnull=False).update(qr_image_url=None)
    
    return redirect('product_list')  # Возврат на главную




@csrf_exempt
def generate_qr_old(request):
    if request.method == 'POST':
        selected_ids = request.POST.getlist('products')
        
        select_all = request.POST.get("select_all") == "1"
        
        
        include_barcode = 'include_barcode' in request.POST
        domain = request.POST.get('domain')
        #print(select_all)

        if not selected_ids:
            return render(request, 'products/generate_qr.html', {'returntolist': True})
            
        if select_all:
            # Выбрать ВСЕ товары с учётом фильтра (не только текущую страницу)
            product_filter = ProductFilter(request.session.get("last_filter", {}), queryset=Product.objects.all())
            products = product_filter.qs
        else:
            products = Product.objects.filter(id__in=selected_ids)
            
        file_paths = []
        qr_root = os.path.join(settings.MEDIA_ROOT, 'qrcodes')
        os.makedirs(qr_root, exist_ok=True)
        
        count = 0  # ← счётчик  файлов
       
        
        

        for product in products:
            qr_text = f"{product.name}"
            #print("Generating QR for:", product)
            if include_barcode:
                qr_text += f"\n{product.barcode}"

            filename = f"{product.name.replace(' ', '_')}.png"
            
            
            
            if create_and_save_qr_code_eps(s3,f"https://{domain}/01/0", product.name, product.barcode, include_barcode, "qrcodes"):
                
                product, created = Product.objects.update_or_create(
                external_id=product.external_id,
                defaults={
                    'name': product.name,
                    'barcode': product.barcode,
                    'created_at': date.today(),
                    'group': 'inriver',
                    'show_on_site': True,
                    'qr_code_url': f"{os.getenv("AWS_URL")}{product.name}.png",
                    'qr_image_url': extract_qr_data_from_image(product.name),
                    

                    }
                )

                file_paths.append((product.id, filename))

  
        
        return redirect('product_list')

    return HttpResponse("Метод не поддерживается", status=405)


    
    product = get_object_or_404(Product, id=product_id)
    base_path = f'media/qrcodes/'
    
    png_path = os.path.join(base_path, f"{product.name}.png")
    eps_path = os.path.join(base_path, f"{product.name}.eps")

    if not os.path.exists(png_path) or not os.path.exists(eps_path):
        return HttpResponse("No QR codes found for this product.", status=404)

    buffer = BytesIO()
    with ZipFile(buffer, 'w') as zip_file:
        zip_file.write(png_path, arcname=f"{product.name}.png")
        zip_file.write(eps_path, arcname=f"{product.name}.eps")

    buffer.seek(0)
    response = FileResponse(buffer, as_attachment=True, filename=f"{product.name}_qr.zip")
    return response



def download_qr_zip(request, product_id):
    # 1️⃣ Получаем товар
    product = get_object_or_404(Product, id=product_id)

    # 2️⃣ Формируем пути
    png_key = f"{S3_FOLDER}{product.name}.png"
    eps_key = f"{S3_FOLDER}{product.name}.eps"

    # 3️⃣ Проверяем наличие файлов в S3
    try:
        s3.head_object(Bucket=BUCKET_NAME, Key=png_key)
        s3.head_object(Bucket=BUCKET_NAME, Key=eps_key)
    except s3.exceptions.ClientError:
        return HttpResponse("No QR codes found for this product.", status=404)

    # 4️⃣ Скачиваем файлы в память
    buffer = BytesIO()
    with ZipFile(buffer, 'w') as zip_file:
        for key, ext in [(png_key, "png"), (eps_key, "eps")]:
            file_stream = BytesIO()
            s3.download_fileobj(Bucket=BUCKET_NAME, Key=key, Fileobj=file_stream)
            file_stream.seek(0)
            zip_file.writestr(f"{product.name}.{ext}", file_stream.getvalue())

    # 5️⃣ Возвращаем ZIP как FileResponse
    buffer.seek(0)
    response = FileResponse(buffer, as_attachment=True, filename=f"{product.name}_qr.zip")
    return response



def download_all_qr(request):
    # Буфер для ZIP-файла
    zip_buffer = BytesIO()

    with ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        continuation_token = None
        total_files = 0

        # S3 возвращает максимум 1000 объектов за раз, поэтому используем пагинацию
        while True:
            list_kwargs = {
                "Bucket": BUCKET_NAME,
                "Prefix": S3_FOLDER,
                "ContinuationToken": continuation_token,
            } if continuation_token else {
                "Bucket": BUCKET_NAME,
                "Prefix": S3_FOLDER,
            }

            response = s3.list_objects_v2(**list_kwargs)
            contents = response.get("Contents", [])

            for obj in contents:
                key = obj["Key"]
                # Пропускаем "папочные" ключи (например qrcodes/)
                if key.endswith("/"):
                    continue

                # Загружаем файл в память
                file_buffer = BytesIO()
                s3.download_fileobj(BUCKET_NAME, key, file_buffer)
                file_buffer.seek(0)

                # Добавляем файл в ZIP
                arcname = key[len(S3_FOLDER):]  # имя без префикса
                zipf.writestr(arcname, file_buffer.read())
                total_files += 1

            # Проверяем, есть ли ещё страницы
            if response.get("IsTruncated"):
                continuation_token = response.get("NextContinuationToken")
            else:
                break

    # Если файлов нет — вернуть 404
    if total_files == 0:
        return HttpResponse("No QR codes found in S3 bucket.", status=404)

    # Подготавливаем ответ
    zip_buffer.seek(0)
    response = HttpResponse(
        zip_buffer.getvalue(),
        content_type="application/zip",
    )
    response["Content-Disposition"] = 'attachment; filename="qr_codes.zip"'
    return response


    
    zip_buffer = BytesIO()
    with ZipFile(zip_buffer, 'w') as zipf:
        for fname in os.listdir(os.path.join(settings.MEDIA_ROOT, 'qrcodes')):
            fpath = os.path.join(settings.MEDIA_ROOT, 'qrcodes', fname)
            zipf.write(fpath, arcname=fname)
    zip_buffer.seek(0)
    
    return HttpResponse(zip_buffer, content_type='application/zip', headers={
        'Content-Disposition': 'attachment; filename="qr_codes.zip"',
    })

def check_url_exists(url):
    try:
        response = requests.head(url, allow_redirects=True, timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False



def remove_transparency(im, bg_color=(255, 255, 255)):
    """
    """
    # Only process if image has transparency (http://stackoverflow.com/a/1963146)
    if im.mode in ('RGBA', 'LA') or (im.mode == 'P' and 'transparency' in im.info):

        # Need to convert to RGBA if LA format due to a bug in PIL (http://stackoverflow.com/a/1963146)
        alpha = im.convert('RGBA').split()[-1]

        # Create a new background image of our matt color.
        # Must be RGBA because paste requires both images have the same format
        # (http://stackoverflow.com/a/8720632  and  http://stackoverflow.com/a/9459208)
        bg = Image.new("RGBA", im.size, bg_color + (255,))
        bg.paste(im, mask=alpha)
        return bg
    else:
        return im





def get_inriver_token():
    token = os.getenv("IN_RIVER_API_KEY")
    if not token:
        raise ValueError("IN_RIVER_API_KEY is not set in environment variables.")
    return token 
    
    
    
def get_inriver_header():
        headers_inRiver = dict(Accept='application/json')
        headers_inRiver['Content-type'] = 'application/json'
        headers_inRiver['X-inRiver-APIKey'] = get_inriver_token()
        return headers_inRiver
    
def get_inriver_url():
        return 'https://api-prod1a-euw.productmarketingcloud.com'


def update_products_from_inriver(request):
    created_count = 0
    updated_count = 0
    skipped_count = 0
    json_request =  {
            "systemCriteria": [ ],
            "dataCriteria": [ {
                "fieldTypeId": "ItemIndicationWebshop",
                "value": "1",
                "operator": "Equal"
                }
                             ]
            }
    # Эмуляция запроса к Inriver — замените на настоящий API
    try:
        
        response = requests.post('{}/api/v1.0.0/query'.format(get_inriver_url()),
                                 headers= get_inriver_header(), data= json.dumps(json_request))
        
        response.raise_for_status()

        inriver_data = response.json()  # Ожидается список словарей с полями
    except Exception as e:
        print("Begin_",e)
        messages.error(request, f"Ошибка при подключении к Inriver: {e}")
        return redirect('product_list')


    for item in inriver_data['entityIds']:
        ext_id = item
        if Product.objects.filter(external_id=ext_id).exists():
            skipped_count += 1
            continue
        if not ext_id:
            continue
        resp_get_linkEntityId = requests.get('{}/api/v1.0.0/entities/{}/fieldvalues'.format(get_inriver_url(),int(ext_id)),headers= get_inriver_header())
        if resp_get_linkEntityId.text != '[]' and resp_get_linkEntityId.status_code == 200:
            json_data = resp_get_linkEntityId.json()
            product_name = next((item_["value"] for item_ in json_data if item_["fieldTypeId"] == "ItemCode"), None)
            
            product, created = Product.objects.update_or_create(
                external_id=ext_id,
                defaults={
                    'name': product_name,
                    'barcode': next((item["value"] for item in json_data if item["fieldTypeId"] == "ItemGTIN"), None),
                    'created_at': date.today(),
                    'group': 'inriver',
                    'show_on_site': True,
                    'product_url' : f"{os.getenv("REDERECT_URL")}{product_name}",
                    'product_image_url' : f"https://dhznjqezv3l9q.cloudfront.net/report_Image/normal/{product_name}_01.png"
                    }
                )
        if created:
            created_count += 1
        else:
            updated_count += 1

    messages.success(
        request,
        f"The update has been finalized: {created_count} added, {updated_count} updated, {skipped_count} missing (duplicates)."
    )
    return redirect('product_list')

def barcode_image_view(request, name):
    
    
    #qr_data = request.build_absolute_uri(f"/01/{barcode}")
    #img = qrcode.make(qr_data)
    buffer = BytesIO()
    
    path = f"qrcodes/{name}.png"
    full_path = os.path.join(settings.MEDIA_ROOT, path)
    if os.path.exists(full_path):
        fig = Image.open(full_path)
        fig.save(buffer, format="PNG")
        return HttpResponse(buffer.getvalue(), content_type="image/png")




