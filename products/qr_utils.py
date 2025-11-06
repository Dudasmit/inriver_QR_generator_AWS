# products/utils/qr_utils.py

import os
import qrcode
from PIL import Image
from urllib.request import urlopen
from django.conf import settings
from pyzbar.pyzbar import decode
import requests
from io import BytesIO


def extract_qr_data_from_image(name):
    #url =  f"https://esschertdesign-prod.s3.eu-west-1.amazonaws.com/qrcodes/{name}.png?mtime=0"
    url =  f"{os.getenv("AWS_URL")}{name}.png?mtime=0"
    
    if not check_url_exists(url):
        return None

    try:
        #print("Загрузка изображения из URL:", url)
        response = requests.get(url)
        img = Image.open(BytesIO(response.content))
        # Декодируем QR
        decoded_objects = decode(img)
    
        #image = Image.open(image_path)
        #decoded_objects = decode(image)
        if decoded_objects:
            qr_data = decoded_objects[0].data.decode("utf-8")
            #print(f"Декодированные данные из QR: {qr_data}")
            return qr_data
    except Exception as e:
        print(f"Ошибка при декодировании QR: {e}")
    return None

def check_url_exists(url):
    try:
        response = urlopen(url)
        return response.status == 200
    except:
        return False

def remove_transparency(im, bg_color=(255, 255, 255)):
    if im.mode in ('RGBA', 'LA'):
        background = Image.new('RGB', im.size, bg_color)
        background.paste(im, mask=im.split()[3])  # 3 is the alpha channel
        return background
    return im



def create_and_save_qr_code_eps(s3,url, item, GTIN, include_barcode, folder):
    data_url = "https://www.esschertdesign.com/qr/" + item
    
    bucket_name = os.getenv("BUCKET_NAME")#"esschertdesign-prod"
    print("Создание QR для: ", bucket_name)
    
    if not check_url_exists(data_url):
        print("Ссылка не существует: ", data_url)

    data = url + str(GTIN)
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    png_path = os.path.join(settings.MEDIA_ROOT, folder, f"{item}.png")
    try:
        img.save(png_path)
    except Exception:
        return False
    
    #try:
    s3.upload_file(png_path, bucket_name, os.path.join("qrcodes/", f"{item}.png"),ExtraArgs={'ACL': 'public-read'})
        #print('OK',os.path.join("qrcodes/", f"{item}.png"))
    #except:
    #    print("\033[1;31mQR code was not created\033[0m", png_path)

        #return False


    fig = Image.open(png_path)
    if fig.mode in ('RGBA', 'LA'):
        fig = remove_transparency(fig)
        fig = fig.convert('RGB')
    fig = remove_transparency(fig)
    fig = fig.convert('RGB')

    eps_path = os.path.join(settings.MEDIA_ROOT, folder, f"{item}.eps")
    try:
        fig.save(eps_path)
    except Exception:
        return False
    fig.close()
    
    try:
        s3.upload_file(eps_path, bucket_name, os.path.join("qrcodes/", f"{item}.eps"),ExtraArgs={'ACL': 'public-read'})
        #print('OK',os.path.join("qrcodes/", f"{item}.eps"))
    except:
        print("\033[1;31mQR code was not created\033[0m", eps_path)

        return False
    
    
    return True
