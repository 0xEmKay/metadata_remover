import argparse
import shutil
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

IMAGE_EXTS = [".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp", ".bmp"]
PDF_EXTS = [".pdf"]
OOXML_EXTS = [".docx", ".xlsx", ".pptx"]

ALL_EXTS = IMAGE_EXTS + PDF_EXTS + OOXML_EXTS

# images

def image(src, dst, strip_icc):
    try:
        from PIL import Image, ImageOps
    except ImportError:
        raise Exception("pillow is needed for images: pip install pillow")

    with Image.open(src) as original:
        original.load()
        fmt = original.format or "PNG"
        icc = original.info.get("icc_profile")
        # apply the rotation stored in EXIF, otherwise phone photos end up sideways
        im = ImageOps.exif_transpose(original)

        new = Image.frombytes(im.mode, im.size, im.tobytes())
        if im.mode == "P":
            new.putpalette(im.getpalette())

        options = {}
        if icc and not strip_icc:
            options["icc_profile"] = icc
        if fmt == "JPEG":
            options["quality"] = 95

        new.save(dst, format=fmt, **options)


# pdf 

def pdf(src, dst):
    try:
        import pikepdf
    except ImportError:
        raise Exception("pikepdf is needed for PDFs: pip install pikepdf")

    with pikepdf.open(src) as doc:
        with doc.open_metadata(set_pikepdf_as_editor=False) as xmp:
            xmp.clear()

        info = doc.trailer.get("/Info")
        if info is not None:
            for key in list(info.keys()):
                del info[key]

        doc.save(dst)


# office files (docx, xlsx, pptx) 
DC = "{http://purl.org/dc/elements/1.1/}"
DCTERMS = "{http://purl.org/dc/terms/}"
CP = "{http://schemas.openxmlformats.org/package/2006/metadata/core-properties}"
EP = "{http://schemas.openxmlformats.org/officeDocument/2006/extended-properties}"

CORE_TAGS = [DC + "creator", DC + "description", DCTERMS + "created", DCTERMS + "modified",
             CP + "lastModifiedBy", CP + "revision", CP + "keywords", CP + "category",
             CP + "contentStatus"]
APP_TAGS = [EP + "Company", EP + "Manager"]


def blank(xml_bytes, tags):
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return xml_bytes

    for tag in tags:
        for element in root.iter(tag):
            element.text = ""
            element.attrib.clear()

    return ET.tostring(root, encoding="UTF-8", xml_declaration=True)


def office(src, dst):
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
        for entry in zin.infolist():
            data = zin.read(entry.filename)

            if entry.filename == "docProps/core.xml":
                data = blank(data, CORE_TAGS)
            elif entry.filename == "docProps/app.xml":
                data = blank(data, APP_TAGS)
            elif entry.filename == "docProps/custom.xml":
                continue 

            zout.writestr(entry, data)


def clean(src, dst, strip_icc):
    ext = src.suffix.lower()

    if ext in IMAGE_EXTS:
        image(src, dst, strip_icc)
    elif ext in PDF_EXTS:
        pdf(src, dst)
    elif ext in OOXML_EXTS:
        office(src, dst)
    else:
        raise Exception("unsupported file type: " + (ext or "no extension"))


def find_files(inputs, recursive):
    files = []
    for name in inputs:
        path = Path(name)
        if path.is_dir():
            pattern = "**/*" if recursive else "*"
            for item in sorted(path.glob(pattern)):
                if item.is_file() and item.suffix.lower() in ALL_EXTS:
                    files.append(item)
        elif path.is_file():
            files.append(path)
        else:
            print("not found:", path, file=sys.stderr)
    return files


# main 

def main():
    parser = argparse.ArgumentParser(description="Remove metadata from files.")
    parser.add_argument("inputs", nargs="+", help="files or folders")
    parser.add_argument("-o", "--output-dir", type=Path, help="folder for the cleaned copies")
    parser.add_argument("--in-place", action="store_true", help="overwrite the original files")
    parser.add_argument("--recursive", action="store_true", help="also go into subfolders")
    parser.add_argument("--suffix", default="_clean", help="added to output names")
    parser.add_argument("--strip-icc", action="store_true", help="also remove image color profiles")
    args = parser.parse_args()

    if not args.in_place and not args.output_dir:
        parser.error("use -o/--output-dir or --in-place")

    files = find_files(args.inputs, args.recursive)
    if not files:
        print("No supported files found.", file=sys.stderr)
        sys.exit(1)

    had_error = False

    for file in files:
        try:
            if args.in_place:
                temp = file.with_name(file.stem + ".temp" + file.suffix)
                clean(file, temp, args.strip_icc)
                shutil.move(str(temp), str(file))
                print("cleaned:", file)
            else:
                args.output_dir.mkdir(parents=True, exist_ok=True)
                out = args.output_dir / (file.stem + args.suffix + file.suffix)
                clean(file, out, args.strip_icc)
                print("cleaned:", file, "->", out)
        except Exception as e:
            had_error = True
            print("ERROR", file, "-", e, file=sys.stderr)

    if had_error:
        sys.exit(1)


if __name__ == "__main__":
    main()
