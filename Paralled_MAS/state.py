
from typing import TypedDict, List, Dict, Any
from streamlit.runtime.uploaded_file_manager import UploadedFile

class PipelineState(TypedDict, total=False):
    uploaded_files: List[UploadedFile]
    parsed_data: Dict[str, Any]
    checklist_result: Any
    validation_result: Any
    union_job_check: Any
    po_check: str