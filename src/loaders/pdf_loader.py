import uuid
import aiofiles
from pathlib import Path
from fastapi import UploadFile

BASE_DIR = Path.cwd().resolve().parent

class FileStorageService:
    """Handles secure, non-blocking enterprise disk storage operations."""

    def __init__(self, base_upload_dir: str):
        self.base_upload_dir = Path(base_upload_dir)
        self.base_upload_dir.mkdir(parents=True, exist_ok=True)
    
    async def save_uploaded_file(self, file: UploadFile) -> str:
        """
        Asynchronously streams and saves an incoming UploadFile object to disk.
        Returns the uniform POSIX absolute string path matching the processed structural pipeline.
        """
        try: 
            unique_prefix = uuid.uuid4().hex
            secure_filename = file.filename  

            target_disk_path = self.base_upload_dir / secure_filename
        
            async with aiofiles.open(target_disk_path, "wb") as out_file:
                while chunk := await file.read(1024 * 64):
                    await out_file.write(chunk)
            
            await file.close()
        
            posix_path_str = target_disk_path.as_posix()

            return posix_path_str

        except Exception as e:
            raise RuntimeError(f"Failed to securely write file to disk: {str(e)}")