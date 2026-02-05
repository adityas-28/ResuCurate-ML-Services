import fitz  # PyMuPDF
from docx import Document
import io
import re

# ---------- PDF TEXT EXTRACTION ----------
def extract_textpdf(file_bytes):
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    blocks = []

    for page in doc:
        for b in page.get_text("blocks"):
            text = b[4]
            text = re.sub(r"[^\x00-\x7F]+", " ", text)
            text = re.sub(r"\s+", " ", text).strip()
            if text:
                blocks.append(text)

    doc.close()
    return "\n".join(blocks)


def extract_links_from_pdf(file_bytes):
    """Extract URLs from PDF link annotations (clickable hyperlinks).
    get_text() only returns plain text; actual URLs are stored in link annotations.
    """
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    urls = []
    for page in doc:
        for link in page.get_links():
            uri = link.get("uri")
            if not uri or not isinstance(uri, str):
                continue
            uri = uri.strip()
            if not uri or uri.startswith(("mailto:", "tel:", "#")):
                continue
            if uri.startswith(("http://", "https://")):
                urls.append(uri)
            elif "linkedin.com" in uri or "github.com" in uri:
                urls.append(uri if "://" in uri else "https://" + uri)
    doc.close()
    return list(set(urls))

# ---------- DOCX TEXT EXTRACTION ----------
def extract_textdocs(file_bytes):
    doc = Document(io.BytesIO(file_bytes))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())

# ---------- LINK EXTRACTION ----------
URL_REGEX = r"(https?://[^\s]+|linkedin\.com/\S+|github\.com/\S+)"

def extract_links(text):
    raw_links = re.findall(URL_REGEX, text)
    return list(set(
        link if link.startswith("http") else "https://" + link
        for link in raw_links
    ))

def classify_links(links):
    classified = {
        "github": [],
        "linkedin": [],
        "portfolio": [],
        "other": []
    }

    for link in links:
        l = link.lower()
        if "github.com" in l:
            classified["github"].append(link)
        elif "linkedin.com" in l:
            classified["linkedin"].append(link)
        elif any(x in l for x in ["portfolio", "vercel", "netlify", "github.io"]):
            classified["portfolio"].append(link)
        else:
            classified["other"].append(link)

    return classified

# ---------- MAIN ----------
if __name__ == "__main__":
    with open("resume.pdf", "rb") as f:
        file_bytes = f.read()

    text = extract_textpdf(file_bytes)

    # Save extracted text
    with open("demo.txt", "w", encoding="utf-8") as f:
        f.write(text)

    # Extract links: from PDF annotations (clickable URLs) + from plain text
    links_from_pdf = extract_links_from_pdf(file_bytes)
    links_from_text = extract_links(text)
    links = list(set(links_from_pdf + links_from_text))
    classified_links = classify_links(links)

    # Save links
    with open("links.txt", "w", encoding="utf-8") as f:
        for k, v in classified_links.items():
            f.write(f"{k.upper()}:\n")
            for link in v:
                f.write(f"  {link}\n")
            f.write("\n")

    print("Extracted links:", classified_links)
