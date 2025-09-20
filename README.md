# Xtract: Egosoft X4 Foundations Cat File Extractor

Xtract is a Python script for extracting files from Egosoft's X4 Foundations `.cat` archives. It allows you to selectively extract files by type or by specific file name, making it easier to work with modding or data analysis for X4 Foundations.

## Features

- Extracts files from `.cat`/`.dat` pairs in a given directory
- Supports filtering by file extension (e.g., xml, html, js, css, lua)
- Optionally extract only specific files
- Verbose logging for debugging

## Requirements

- Python 3.8+
- Rich 14.1+

## Usage

```bash
python xtract.py <source_directory> <destination_directory> [options]
```

### Arguments

- `<source_directory>`: Directory containing `.cat` files (and their corresponding `.dat` files)
- `<destination_directory>`: Directory where extracted files will be saved

### Options

- `-i`, `--include`: List of specific `.cat` files to extract (default: all found)
- `-t`, `--types`: Comma-separated list of file extensions to extract (default: xml, xsd, html, js, css, lua)
- `-e`, `--expansions`: Auto-detect and extract official expansions
- `-v`, `--verbose`: Enable verbose logging for debugging

### Examples

Extract all XML, HTML, and JS files from a Steam install:

```bash
python xtract.py /home/username/.local/share/steam/steamapps/common/X4\ Foundations /output -t xml,html,js
```

Extract only *.xml files from cat file 01 and 02:

```bash
python xtract.py /path/to/cats /output -i 01.cat 02.cat -t xml
```

## Logging

By default, only warnings and errors are logged. Use `-v` or `--verbose` for detailed debug output.

## Notes

- The script expects `.cat` and corresponding `.dat` files to be present in the source directory.
- Only files with the specified extensions will be extracted.
- The script creates output directories as needed.

## Contributing

Pull requests and issues are welcome! Please ensure code follows PEP8/ruff formatting and is well-documented.

## License

This project is licensed under the GNU General Public License v3.0. See the [LICENSE](LICENSE) file for details.
