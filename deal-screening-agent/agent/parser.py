"""
Raw text extraction from a pitch deck PDF via PyMuPDF (fitz).

Real pitch decks are frequently exported as flattened/rasterized slides (a
PDF export from Keynote/Google Slides/Canva, or a scanned deck) with NO text
layer at all -- PyMuPDF's native extraction returns an empty string for every
page in that case, which used to silently flow into the LLM as "no content",
producing a bogus all-zeros screening memo instead of an error.

Fix: per page, if the native text layer is suspiciously short, render that
page to an image and run Tesseract OCR (via pytesseract) on it instead. OCR
requires the Tesseract binary to be installed on the host machine -- if it
isn't, we fail soft (that page just stays empty) rather than crashing, and
the caller can warn the user based on the returned `used_ocr` / total length.
"""
import io

import fitz  # PyMuPDF

OCR_MIN_CHARS = 20  # below this, a page is treated as having no real text layer
OCR_DPI = 200

_ocr_available: bool | None = None  # None = untested, True/False after first attempt


def _try_ocr_page(page) -> str:
    global _ocr_available
    if _ocr_available is False:
        return ""
    try:
        import pytesseract
        from PIL import Image

        pix = page.get_pixmap(dpi=OCR_DPI)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        text = pytesseract.image_to_string(img)
        _ocr_available = True
        return text
    except Exception:
        # pytesseract/Pillow not installed, or Tesseract binary not found on
        # PATH -- treat OCR as unavailable for the rest of this process
        # rather than raising, so text-based PDFs still work fine.
        _ocr_available = False
        return ""


def _extract_pages(doc) -> tuple[list[str], bool]:
    pages = []
    used_ocr = False
    for page in doc:
        text = page.get_text()
        if len(text.strip()) < OCR_MIN_CHARS:
            ocr_text = _try_ocr_page(page)
            if len(ocr_text.strip()) > len(text.strip()):
                text = ocr_text
                used_ocr = True
        pages.append(text)
    return pages, used_ocr


def extract_text(pdf_path: str) -> tuple[str, bool]:
    """Returns (full_text, used_ocr)."""
    doc = fitz.open(pdf_path)
    pages, used_ocr = _extract_pages(doc)
    doc.close()
    return "\n\n--- page break ---\n\n".join(pages), used_ocr


def extract_text_from_bytes(pdf_bytes: bytes) -> tuple[str, bool]:
    """Returns (full_text, used_ocr)."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages, used_ocr = _extract_pages(doc)
    doc.close()
    return "\n\n--- page break ---\n\n".join(pages), used_ocr
