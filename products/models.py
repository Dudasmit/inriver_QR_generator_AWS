from django.db import models
from urllib.parse import quote
import os
from django.conf import settings
from .qr_utils import extract_qr_data_from_image, check_url_exists 


class Product(models.Model):
    
    name = models.CharField(max_length=255)
    barcode = models.CharField(max_length=50)
    created_at = models.DateField()
    group = models.CharField(max_length=100)
    show_on_site = models.BooleanField(default=False)
    external_id = models.CharField(max_length=100, unique=True)
    qr_image_url = models.URLField(blank=True, null=True)
    qr_code_url = models.URLField(blank=True, null=True)
    product_url = models.URLField(blank=True, null=True)
    product_image_url = models.URLField(blank=True, null=True)
    
    
    '''
    @property
    def product_url(self):
        return f"https://www.esschertdesign.com/qr/{self.name}"
    
    @property
    def product_image_url(self):
        return f"https://dhznjqezv3l9q.cloudfront.net/report_Image/normal/{quote(self.name)}_01.png"
    
    @property
    def product_barcode_image_url(self):
        return f"https://esschertdesign-prod.s3.eu-west-1.amazonaws.com/qrcodes/{quote(self.name)}.png"

    
    @property
    def barcode_png_url(self):
        
        if check_url_exists(f"https://esschertdesign-prod.s3.eu-west-1.amazonaws.com/qrcodes/{self.name}.png"):
            return f"https://esschertdesign-prod.s3.eu-west-1.amazonaws.com/qrcodes/{self.name}.png"
        
        return None

    @property
    def qr_code_link(self):
      
        return extract_qr_data_from_image(self.name)
    '''




    def __str__(self):
        return self.name

class QRTaskStatus(models.Model):
    task_id = models.CharField(max_length=100, unique=True)
    total = models.PositiveIntegerField(default=0)
    processed = models.PositiveIntegerField(default=0)
    done = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    
