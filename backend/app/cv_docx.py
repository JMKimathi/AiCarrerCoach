"""Turn the CV's simple Markdown into a Word document without extra dependencies.

A .docx file is a zip of XML parts. This writes the smallest valid set: one
column, real text, standard headings and plain bullets, which is what applicant
tracking systems read most reliably. Understood Markdown:

  # Name            large bold line
  ## Heading        bold capitals with a rule underneath
  **Bold line**     a bold paragraph (text after the closing ** stays regular)
  - item            bullet
  anything else     normal paragraph
"""

import io
import zipfile
from xml.sax.saxutils import escape

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

_CONTENT_TYPES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
    '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
    '</Types>'
)
_ROOT_RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
    '</Relationships>'
)
_DOCUMENT_RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
    '</Relationships>'
)
_STYLES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    f'<w:styles xmlns:w="{_W}"><w:docDefaults>'
    '<w:rPrDefault><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:cs="Calibri"/>'
    '<w:sz w:val="22"/><w:szCs w:val="22"/><w:lang w:val="en-GB"/></w:rPr></w:rPrDefault>'
    '<w:pPrDefault><w:pPr><w:spacing w:after="60" w:line="264" w:lineRule="auto"/></w:pPr></w:pPrDefault>'
    '</w:docDefaults></w:styles>'
)


def _run(text: str, bold: bool = False, size: int | None = None) -> str:
    properties = ("<w:b/>" if bold else "") + (f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>' if size else "")
    return (f"<w:r>{'<w:rPr>' + properties + '</w:rPr>' if properties else ''}"
            f'<w:t xml:space="preserve">{escape(text)}</w:t></w:r>')


def _paragraph(runs: str, properties: str = "") -> str:
    return f"<w:p>{'<w:pPr>' + properties + '</w:pPr>' if properties else ''}{runs}</w:p>"


def _line(raw: str) -> str:
    line = raw.rstrip()
    if line.startswith("## "):
        rule = '<w:pBdr><w:bottom w:val="single" w:sz="6" w:space="1" w:color="808080"/></w:pBdr>'
        return _paragraph(_run(line[3:].upper(), bold=True, size=24), rule + '<w:spacing w:before="200" w:after="80"/>')
    if line.startswith("# "):
        return _paragraph(_run(line[2:], bold=True, size=36), '<w:spacing w:after="40"/>')
    if line.startswith("- "):
        return _paragraph(_run("• " + line[2:].replace("**", "")), '<w:ind w:left="360" w:hanging="200"/>')
    if line.startswith("**") and "**" in line[2:]:
        bold_text, _, rest = line[2:].partition("**")
        return _paragraph(_run(bold_text, bold=True) + (_run(rest) if rest else ""), '<w:spacing w:before="80"/>')
    return _paragraph(_run(line.replace("**", "")))


def markdown_to_docx(markdown: str) -> bytes:
    body = "".join(_line(line) for line in markdown.splitlines() if line.strip())
    document = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:document xmlns:w="{_W}"><w:body>{body}'
        '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/>'
        '<w:pgMar w:top="1134" w:right="1134" w:bottom="1134" w:left="1134" w:header="708" w:footer="708" w:gutter="0"/>'
        '</w:sectPr></w:body></w:document>'
    )
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", _CONTENT_TYPES)
        archive.writestr("_rels/.rels", _ROOT_RELS)
        archive.writestr("word/document.xml", document)
        archive.writestr("word/styles.xml", _STYLES)
        archive.writestr("word/_rels/document.xml.rels", _DOCUMENT_RELS)
    return buffer.getvalue()
