"""Extracts files from Egosoft's X4 Foundations cat files."""

import argparse
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "sourcedir", help="The directory where the cat files are located")
    parser.add_argument(
        "destdir", help="The directory where to extract any matching files")
    parser.add_argument(
        "-i",
        "--include",
        type=list,
        nargs="*",
        default=[],
        help="Specific files to extract. By default this is all cat files found in the directory.")
    parser.add_argument(
        "-t",
        "--types",
        type=str,
        default="xml, xsd, html, js, css, lua",
        help="A comma separated list of file extensions to extract. By default xml, xsd, html, js, css and lua are extracted.")
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging. By default only warnings and errors are logged.")
    return parser.parse_args()


def ex_cat(cat_file: Path, output: Path, extensions: list[str]) -> None:
    """
    Extracts files from a cat file.

    Args:
        cat_file (Path): The path to the cat file.
        output (Path): The directory where extracted files will be saved.
        extensions (list): List of file extensions to filter files for extraction.

    Raises:
        FileNotFoundError: If the cat file does not exist.
        OSError: If there is an error writing the extracted file.
        Exception: For any other unexpected errors during extraction.
    """
    logger.info(f"Processing {cat_file}...")
    if not cat_file.exists():
        raise FileNotFoundError(f"Cat file {cat_file} does not exist")

    dat_file = cat_file.with_suffix('.dat')
    if not dat_file.exists():
        logger.warning(f"Associated dat file {dat_file} does not exist, skipping extraction for {cat_file}")
        return

    with Path.open(cat_file) as c_file, Path.open(dat_file, 'rb') as d_file:
        for i, line in enumerate(c_file):
            logger.debug(f"Processing line: {line.strip()}")

            if i % 10000 == 0:
                logger.info(f"Processed {i} lines...")

            fields = line.strip().split(" ")

            filepath = Path(fields[0])
            size = int(fields[-3])
            file_parent = filepath.parent

            if filepath.suffix[1:] not in extensions:
                d_file.read(size)
                continue

            if not Path(output / file_parent).is_dir():
                Path(output / file_parent).mkdir(parents=True)

            try:
                outf = Path.open(output / filepath, "wb")
                outf.write(d_file.read(size))
                outf.close()
            except OSError:
                logger.warning(f"Error while writing file {output}/{filepath}: {OSError}")
            except Exception as e:
                logger.error(f"Unexpected error while writing file {output}/{filepath}: {e}")

    logger.debug(f"Files of types {', '.join(extensions)} extracted from {cat_file} to {output}")


def main(source_dir: Path, output: Path, extensions: list[str], include: list) -> None:
    """
    Main function to extract files from cat files.

    Args:
        source_dir (Path): The directory containing the cat files.
        output (Path): The directory where extracted files will be saved.
        extensions (list): List of file extensions to filter files for extraction.
        include (list): List of specific files to include in extraction.

    Raises:
        FileNotFoundError: If no cat files are found in the source directory.
    """
    # Find all .cat files that do NOT have '_sig' before the suffix
    all_files = [f for f in source_dir.glob("*.cat") if not f.stem.endswith("_sig")]

    if not all_files:
        raise FileNotFoundError(f"No cat files found in {source_dir}")

    if include:
        extract_files = [f for f in all_files if f.name in include]
    else:
        extract_files = all_files

    logger.info(f"{len(extract_files)} cat files found for extraction...")
    for file in extract_files:
        ex_cat(file, output, extensions)


if __name__ == "__main__":
    args = parse_arguments()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    if not Path(args.destdir).exists():
        Path.mkdir(args.destdir, parents=True)

    file_types = args.types.split(",")
    if not file_types:
        raise ValueError("No file types specified for extraction.")

    logger.info(f"Extracting files to {Path(args.destdir).resolve()}")
    logger.info(f"Extracting types: {', '.join(file_types)}")
    main(Path(args.sourcedir), Path(args.destdir), file_types, args.include)
