# metadata_remover

A small command line tool that strips metadata (EXIF/GPS, author names, tags) from files before you share them. It runs fully offline and nothing is collected or stored.

## Supported files

| Type | Extensions | Needs |
|------|-----------|-------|
| Images | jpg, jpeg, png, tif, tiff, webp, bmp | `pillow` |
| PDF | pdf | `pikepdf` |
| Office | docx, xlsx, pptx | N/A |

Libraries are only needed for the file types you actually use.

## Install

```
git https://gitlab.com/KavinduTharushan/metadata_remover.git
cd metadata_remover
pip install -r requirements.txt
```

Requires Python 3.8 or newer.

## Usage

Write cleaned copies to a folder (originals untouched):

```
python metadata_remover.py -o clean/ photo.jpg report.docx
```

Overwrite the originals:

```
python metadata_remover.py --in-place photo.jpg
```

Clean a whole folder, including subfolders:

```
python metadata_remover.py --recursive -o clean/ ~/Pictures/trip
```

## Options

| Option | Description |
|--------|-------------|
| `-o, --output-dir DIR` | Write cleaned copies to DIR |
| `--in-place` | Overwrite the originals |
| `--recursive` | Go into folders |
| `--suffix TEXT` | Added to output names (default `_clean`) |
| `--strip-icc` | Also remove ICC color profiles from images |

## Notes

- FYI images are rebuilt from pixel data, so gifs keep only the first frame.
- Office files have author, dates, company and custom properties blanked. Document content, comments and embedded images are not touched.
- On Windows, use `py` instead of `python`.

## License

MIT

