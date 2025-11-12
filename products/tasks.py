from celery import shared_task
from .models import Product,QRTaskStatus
from datetime import date
import os
from .qr_utils import create_and_save_qr_code_eps, extract_qr_data_from_image
from django.conf import settings
import boto3
from .filters import ProductFilter

BUCKET_NAME = os.getenv("BUCKET_NAME")
S3_FOLDER = os.getenv("S3_FOLDER")

s3 = boto3.client("s3")

@shared_task(bind=True)
def generate_qr_for_products(self, product_ids=None, select_all=False, include_barcode=False, domain=None, filter_data=None):
    """
    Генерация QR-кодов для товаров.
    :param product_ids: список id выбранных товаров
    :param select_all: если True — обрабатываем все товары по фильтру
    :param include_barcode: включать штрихкод в QR
    :param domain: домен для ссылок
    :param filter_data: фильтр для select_all (dict)
    """
    
    if select_all:
        
        products = ProductFilter(filter_data or {}, queryset=Product.objects.all()).qs
    else:
        products = Product.objects.filter(id__in=product_ids or [])
     
     
    total = products.count()
    print(f"🚀 Generating shared_task", self.request.id)


    # 🔹 Создаём/обновляем запись статуса задачи
    task_status, _ = QRTaskStatus.objects.get_or_create(task_id=self.request.id)
    task_status.total = total
    task_status.processed = 0
    task_status.done = False
    task_status.save()
            
    print(f"🚀 Generating {total} QR codes...")
    
    
    for i, product in enumerate(products, start=1):
        try:
            qr_text = product.name
            if include_barcode:
                qr_text += f"\n{product.barcode}"
            print(f"🔧 Generating QR for product ID {product.id}, Name: {product.name}")

            # создаём QR-код через твою функцию
            result = create_and_save_qr_code_eps(
                s3,
                f"https://{domain}/01/0",
                product.name,
                product.barcode,
                include_barcode,
                S3_FOLDER
            )

            if not isinstance(result, dict):
                continue

            # обновляем или создаём запись товара с URL QR-кода
            Product.objects.update_or_create(
                external_id=product.external_id,
                defaults={
                    'name': product.name,
                    'barcode': product.barcode,
                    'created_at': date.today(),
                    'group': 'inriver',
                    'show_on_site': True,
                    'qr_code_url': f"{os.getenv('AWS_URL')}{product.name}.png",
                    'qr_image_url': extract_qr_data_from_image(product.name),
                }
            )
        except Exception as e:
            print(f"⚠️ Ошибка при обработке {product.id}: {e}")
            
        task_status.processed = i
        task_status.save(update_fields=["processed"])
        
    task_status.done = True
    task_status.save(update_fields=["done"])

