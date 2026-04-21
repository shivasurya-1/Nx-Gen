import cloudinary.utils
from cloudinary_storage.storage import MediaCloudinaryStorage, RawMediaCloudinaryStorage

class AuthenticatedMediaCloudinaryStorage(MediaCloudinaryStorage):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = 'authenticated'

class AuthenticatedRawMediaCloudinaryStorage(MediaCloudinaryStorage):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = 'authenticated'

def get_signed_url(public_id, resource_type=None):
    """
    Generates a signed URL for an authenticated Cloudinary resource.
    Automatically detects resource_type from extension if not provided.
    """
    if not resource_type:
        ext = public_id.split('.')[-1].lower() if '.' in public_id else ''
        if ext in ['jpg', 'jpeg', 'png', 'gif', 'pdf', 'bmp', 'webp', 'tiff']:
            resource_type = 'image'
        elif ext in ['mp4', 'mov', 'avi', 'mkv', 'webm']:
            resource_type = 'video'
        else:
            resource_type = 'raw'

    url, options = cloudinary.utils.cloudinary_url(
        public_id,
        resource_type=resource_type,
        type='authenticated',
        sign_url=True,
    )
    return url
