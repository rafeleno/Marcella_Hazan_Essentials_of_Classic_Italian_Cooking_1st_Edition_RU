import zipfile
import os

EPUB_NAME = "test_range.epub"

# HTML контент с проблемой
HTML_CONTENT = """<?xml version='1.0' encoding='utf-8'?>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>Test Range</title>
    <style>body { font-family: sans-serif; }</style>
</head>
<body>
    <p>For 6 servings or more if served as an appetizer</p>
    
    <p>8 to 10 fresh zucchini</p>
    <p>1 tablespoon butter</p>
    <p>1 tablespoon vegetable oil</p>
    <p>1 tablespoon onion chopped fine</p>
    <p>¼ pound boiled unsmoked ham, chopped fine</p>
    <p>Salt</p>
    <p>Black pepper, ground fresh from the mill</p>
    <p>Béchamel Sauce, prepared as directed, using 1 cup milk, 2 tablespoons butter, 1½ tablespoons flour, and ⅛ teaspoon salt</p>
    <p>¼ cup freshly grated parmigiano-reggiano cheese</p>
    <p>Whole nutmeg</p>
    <p>1 egg</p>
    <p>An oven-to-table baking dish</p>
    <p>Butter for smearing and dotting the baking dish</p>
    <p>Unflavored bread crumbs, lightly toasted</p>
</body>
</html>
"""

# OPF контент
OPF_CONTENT = """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="BookId" version="2.0">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
        <dc:title>Test Range</dc:title>
        <dc:language>en</dc:language>
        <dc:identifier id="BookId" opf:scheme="UUID">urn:uuid:12345</dc:identifier>
    </metadata>
    <manifest>
        <item id="content" href="content.xhtml" media-type="application/xhtml+xml"/>
        <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
    </manifest>
    <spine toc="ncx">
        <itemref idref="content"/>
    </spine>
</package>
"""

# NCX контент
NCX_CONTENT = """<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
    <head><meta name="dtb:uid" content="urn:uuid:12345"/></head>
    <docTitle><text>Test Range</text></docTitle>
    <navMap>
        <navPoint id="navPoint-1" playOrder="1">
            <navLabel><text>Content</text></navLabel>
            <content src="content.xhtml"/>
        </navPoint>
    </navMap>
</ncx>
"""

# CONTAINER
CONTAINER = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
    <rootfiles>
        <rootfile full-path="content.opf" media-type="application/oebps-package+xml"/>
    </rootfiles>
</container>
"""

def create_epub():
    print(f"📦 Создаю {EPUB_NAME}...")
    if os.path.exists(EPUB_NAME):
        os.remove(EPUB_NAME)
        
    with zipfile.ZipFile(EPUB_NAME, 'w', zipfile.ZIP_DEFLATED) as epub:
        epub.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        epub.writestr("META-INF/container.xml", CONTAINER)
        epub.writestr("content.opf", OPF_CONTENT)
        epub.writestr("toc.ncx", NCX_CONTENT)
        epub.writestr("content.xhtml", HTML_CONTENT)
        
    print("✅ Тестовый EPUB готов.")

if __name__ == "__main__":
    create_epub()
