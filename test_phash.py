from PIL import Image
import imagehash

path = '/mnt/smb/OneDrive/Pictures/!Фотосессии/Алина Титова (@ApelsiN04KA)/_DSC4017.jpg'
img = Image.open(path)
# Преобразуем в RGB, если изображение в другом формате
if img.mode != 'RGB':
    img = img.convert('RGB')
# Вычисляем phash
phash = imagehash.phash(img)
print(f"Вычисленный хеш: {str(phash)}")
print(f"Хеш из базы: 94c98e3f64f46919") 