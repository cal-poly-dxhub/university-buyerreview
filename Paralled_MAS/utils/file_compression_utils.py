import subprocess
import os
import tempfile
import io
from PIL import Image
from PyPDF2 import PdfReader, PdfWriter

MAX_CHUNK_SIZE_MB = 4.5
MAX_PDF_PAGES = 50


def get_file_size_mb(file) -> float:
    pos = file.tell()
    file.seek(0, 2)
    size = file.tell() / (1024 * 1024)
    file.seek(pos)
    return size


def trim_pdf(file: io.BytesIO, max_pages=MAX_PDF_PAGES) -> io.BytesIO:
    file.seek(0)
    reader = PdfReader(file)
    total_pages = len(reader.pages)

    if total_pages <= max_pages:
        file.seek(0)
        return file  # No trimming needed

    writer = PdfWriter()
    for i in range(max_pages):
        writer.add_page(reader.pages[i])

    trimmed_pdf = io.BytesIO()
    writer.write(trimmed_pdf)
    trimmed_pdf.seek(0)
    return trimmed_pdf


def compress_pdf(file: io.BytesIO, quality: str = "screen") -> io.BytesIO:
    file.seek(0)
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.pdf")
        output_path = os.path.join(tmpdir, "output_compressed.pdf")

        with open(input_path, "wb") as f:
            f.write(file.read())

        try:
            subprocess.run([
                "gs",
                "-sDEVICE=pdfwrite",
                "-dCompatibilityLevel=1.4",
                f"-dPDFSETTINGS=/{quality}",
                "-dNOPAUSE",
                "-dQUIET",
                "-dBATCH",
                f"-sOutputFile={output_path}",
                input_path
            ], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Ghostscript compression failed: {e}")
            file.seek(0)
            return file  # Return original if compression fails

        with open(output_path, "rb") as f:
            compressed = io.BytesIO(f.read())

    compressed.seek(0)
    return compressed


def compress_image(file, target_quality=85, resize_factor=0.5) -> io.BytesIO:
    file.seek(0)
    img = Image.open(file)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    new_size = (int(img.width * resize_factor),
                int(img.height * resize_factor))
    img = img.resize(new_size, Image.Resampling.LANCZOS)

    output = io.BytesIO()
    img.save(output, format="JPEG", quality=target_quality, optimize=True)
    output.seek(0)
    return output


def compress_file_if_needed(file, filename: str) -> io.BytesIO:
    file.seek(0)
    size_mb = get_file_size_mb(file)
    ext = filename.lower().split(".")[-1]

    if ext == "pdf":
        # First, trim the PDF if needed
        file = trim_pdf(file, max_pages=MAX_PDF_PAGES)

    # Check if size still exceeds limit after trimming (or if no trimming was needed)
    size_mb = get_file_size_mb(file)
    if size_mb <= MAX_CHUNK_SIZE_MB:
        file.seek(0)
        return file

    # Apply compression based on file type
    if ext == "pdf":
        return compress_pdf(file)
    if ext in {"jpg", "jpeg", "png"}:
        return compress_image(file)

    file.seek(0)
    return file
