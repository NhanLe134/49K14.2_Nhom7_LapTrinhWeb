import requests
from django.conf import settings

class SupabaseRESTClient:
    def __init__(self):
        self.base_url = settings.SUPABASE_URL
        self.api_key = settings.SUPABASE_KEY
        self.headers = {
            "apikey": self.api_key,
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    # ==============================
    # Storage methods
    # ==============================
    def upload_file(self, bucket_name, file_path, file_data, content_type="image/jpeg"):
        """
        Uploads a file to Supabase Storage bucket.
        """
        url = f"{self.base_url}/storage/v1/object/{bucket_name}/{file_path}"
        
        headers = self.headers.copy()
        headers["Content-Type"] = content_type
        
        response = requests.post(url, headers=headers, data=file_data)
        
        if response.status_code == 200 or response.status_code == 201:
            return {
                "success": True,
                "url": self.get_public_url(bucket_name, file_path)
            }
        else:
            return {
                "success": False,
                "error": response.json()
            }

    def get_public_url(self, bucket_name, file_path):
        """
        Returns the public URL for a file in Supabase Storage.
        """
        return f"{self.base_url}/storage/v1/object/public/{bucket_name}/{file_path}"

# Instance ready to be imported by other modules
supabase_client = SupabaseRESTClient()
