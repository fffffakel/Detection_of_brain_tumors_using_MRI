import os
from django.conf import settings

print("MEDIA_ROOT:", settings.MEDIA_ROOT)
print("Файлы в MEDIA_ROOT:", os.listdir(settings.MEDIA_ROOT))