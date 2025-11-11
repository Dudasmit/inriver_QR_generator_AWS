from celery import shared_task
from .models import Product
from datetime import date
import os
from .qr_utils import create_and_save_qr_code_eps, extract_qr_data_from_image
from django.conf import settings
import boto3

BUCKET_NAME = os.getenv("BUCKET_NAME")
S3_FOLDER = os.getenv("S3_FOLDER")

s3 = boto3.client("s3")

@shared_task
def generate_qr_for_products(product_ids=None, select_all=False, include_barcode=False, domain=None, filter_data=None):
    """
    Генерация QR-кодов для товаров.
    :param product_ids: список id выбранных товаров
    :param select_all: если True — обрабатываем все товары по фильтру
    :param include_barcode: включать штрихкод в QR
    :param domain: домен для ссылок
    :param filter_data: фильтр для select_all (dict)
    """
    
    if select_all:
        # фильтруем все товары по сохранённому фильтру
        from .filters import ProductFilter
        products = ProductFilter(filter_data or {}, queryset=Product.objects.all()).qs
    else:
        products = Product.objects.filter(id__in=product_ids or [])
    print("Generating QR codes...")

    for product in products:
        qr_text = product.name
        if include_barcode:
            qr_text += f"\n{product.barcode}"
        print(f"Generating QR for product ID {product.id}, Name: {product.name}")

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
