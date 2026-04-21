import os
import django
import cloudinary.utils

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

public_id = 'media/assignments/cashora_aof5eb.pdf'

for r_type in ['raw', 'image', 'video']:
    url, _ = cloudinary.utils.cloudinary_url(
        public_id,
        resource_type=r_type,
        type='authenticated',
        sign_url=True
    )
    print(f"{r_type}: {url}")
