import os
import shutil
from pathlib import Path
from typing import Optional, Dict
from app.config import settings

class MarkdownService:
    @staticmethod
    def get_job_dir(job_id: str) -> Path:
        job_dir = settings.STORAGE_PATH / job_id
        os.makedirs(job_dir, exist_ok=True)
        return job_dir

    @classmethod
    def save_markdown(cls, job_id: str, filename: str, content: str) -> Path:
        job_dir = cls.get_job_dir(job_id)
        file_path = job_dir / filename
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return file_path

    @classmethod
    def save_markdown_version(cls, job_id: str, base_filename: str, content: str, version: int = 1) -> Path:
        """
        Saves versioned file (e.g. 03-draft-v2.md) and updates active base file (03-draft.md).
        """
        job_dir = cls.get_job_dir(job_id)
        cls.save_markdown(job_id, base_filename, content)
        if version > 1:
            parts = base_filename.rsplit(".", 1)
            v_filename = f"{parts[0]}-v{version}.{parts[1]}"
            v_path = job_dir / v_filename
            with open(v_path, "w", encoding="utf-8") as f:
                f.write(content)
            return v_path
        return job_dir / base_filename

    @classmethod
    def read_markdown(cls, job_id: str, filename: str) -> Optional[str]:
        job_dir = cls.get_job_dir(job_id)
        file_path = job_dir / filename
        if not file_path.exists():
            return None
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    @classmethod
    def get_all_job_files(cls, job_id: str) -> Dict[str, bool]:
        job_dir = cls.get_job_dir(job_id)
        expected_files = [
            "01-research.md",
            "02-content-brief.md",
            "03-draft.md",
            "04-quality-seo.md",
            "05-final.md",
        ]
        return {file_name: (job_dir / file_name).exists() for file_name in expected_files}

    @classmethod
    def delete_job_files(cls, job_id: str) -> bool:
        """
        Deletes all temporary markdown files and the job directory.
        MUST ONLY be called after successful publication verification.
        """
        job_dir = settings.STORAGE_PATH / job_id
        if job_dir.exists() and job_dir.is_dir():
            shutil.rmtree(job_dir)
            return True
        return False
