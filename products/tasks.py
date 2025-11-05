from background_task import background
from .models import Product, QRTaskStatus
import os
from django.conf import settings
from .qr_utils import create_and_save_qr_code_eps

@background(schedule=1)
def generate_qr_background_task(product_ids, domain, include_barcode, task_id):
    try:
        task = QRTaskStatus.objects.get(task_id=task_id)
        task.total = len(product_ids)
        task.save()

        for i, product_id in enumerate(product_ids):
            product = Product.objects.get(id=product_id)
            create_and_save_qr_code_eps(
                url=f"https://{domain}/01/",
                item=product.name,
                GTIN=product.barcode,
                include_barcode=include_barcode,
                folder="qrcodes"
            )
            task.processed = i + 1
            task.save()

        task.done = True
        task.save()
    except Exception as e:
        print("Error in background task:", e)


@background(schedule=1)
def generate_qr_background_task_(product_id, domain, task_id):
    try:
            
            
        task = QRTaskStatus.objects.get(task_id=task_id)

        product = Product.objects.get(id=product_id)
        path = f"qrcodes/{product.name}.png"
        full_path = os.path.join(settings.MEDIA_ROOT, path)
        if os.path.exists(full_path):
            task.processed = task.processed + 1
            task.save()
        else:
            create_and_save_qr_code_eps(
                url=f"https://{domain}/01/",
                item=product.name,
                GTIN=product.barcode,
                include_barcode=True,  # Assuming include_barcode is always True here
                folder="qrcodes"
            )
            task.processed = task.processed + 1
            task.save()

        task.done = task.processed >= task.total
        task.save()
    except Exception as e:
        print("Error in background task:", e)
