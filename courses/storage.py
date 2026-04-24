import cloudinary.utils
from cloudinary_storage.storage import MediaCloudinaryStorage, RawMediaCloudinaryStorage

class AuthenticatedMediaCloudinaryStorage(MediaCloudinaryStorage):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = 'authenticated'

class AuthenticatedRawMediaCloudinaryStorage(RawMediaCloudinaryStorage):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = 'authenticated'

from cloudinary.exceptions import NotFound
import cloudinary.api

def get_signed_url(public_id, resource_type=None):
    """
    Generates a signed URL for an authenticated Cloudinary resource.
    Automatically fetches resource type and handles legacy 'upload' types.
    """
    resource = None
    
    # Query Cloudinary directly to know exactly how it was stored
    try:
        resource = cloudinary.api.resource(public_id, resource_type='raw')
    except NotFound:
        try:
            resource = cloudinary.api.resource(public_id, resource_type='image')
        except NotFound:
            try:
                resource = cloudinary.api.resource(public_id, resource_type='video')
            except NotFound:
                pass

    if resource:
        r_type = resource.get('resource_type', 'raw')
        delivery_type = resource.get('type', 'upload')
        
        # Public ('upload') files do not require signing
        if delivery_type == 'upload':
            return resource.get('secure_url')
            
        # Build signed URL for authenticated files
        url, _ = cloudinary.utils.cloudinary_url(
            public_id,
            resource_type=r_type,
            type='authenticated',
            format=resource.get('format'),
            sign_url=True
        )
        return url

    # Fallback to local guessing if Cloudinary API check didn't find the resource
    if not resource_type:

        ext = public_id.split('.')[-1].lower() if '.' in public_id else ''
        if ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'tiff']:
            resource_type = 'image'
        elif ext in ['mp4', 'mov', 'avi', 'mkv', 'webm']:
            resource_type = 'video'
        else:
            resource_type = 'raw'

    # Ensure format extension is included if required by Cloudinary for signed RAW URLs
    if resource_type == 'raw' and '.' not in public_id:
        # Depending on storage, sometimes the public_id includes the extension for raw files
        pass

    url, options = cloudinary.utils.cloudinary_url(
        public_id,
        resource_type=resource_type,
        type='authenticated',
        sign_url=True,
    )
    return url
