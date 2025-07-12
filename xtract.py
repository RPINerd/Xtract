"""Extracts files from Egosoft's X4 Foundations cat files."""

import argparse
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

EXPANSIONS = {
    "ego_dlc_boron": "Kingdoms End",
    "ego_dlc_pirate": "Tides of Avarice",
    "ego_dlc_split": "Split Vendetta",
    "ego_dlc_terran": "Cradle of Humanity",
    "ego_dlc_timelines": "Timelines",
    "ego_dlc_ventures": "Ventures",
    "ego_dlc_mini_01": "Hyperion",
    "ego_dlc_mini_02": "...",
    "ego_dlc_mini_03": "...",
}


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "sourcedir", help="The directory where the cat files are located")
    parser.add_argument(
        "destdir", help="The directory where to extract any matching files")
    parser.add_argument(
        "-e",
        "--expansions",
        action="store_true",
        help="Auto detect any game expansions and extract all files with those extensions."
    )
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
            # logger.debug(f"Processing line: {line.strip()}")

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


def process_directory(source_dir: Path, output: Path, extensions: list[str], include: list[str]) -> None:
    """
    Process a directory of cat files.

    Args:
        source_dir (Path): The directory containing the cat files.
        output (Path): The directory where extracted files will be saved.
        extensions (list): List of file extensions to filter files for extraction.
        include (list[str]): List of specific files to include in extraction.

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


def main(args: argparse.Namespace) -> None:
    """
    Main function to orchestrate the extraction of files from cat files.

    Args:
        source_dir (Path): The directory containing the cat files.
        output (Path): The directory where extracted files will be saved.
        extensions (list): List of file extensions to filter files for extraction.
        include (list[str]): List of specific files to include in extraction.

    Raises:
        ValueError: If no file types are specified for extraction.
        FileNotFoundError: If the source directory does not exist.
        FileNotFoundError: If no cat files are found in the source directory.
    """
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    target_dir = Path(args.destdir).resolve()
    if not target_dir.exists():
        Path.mkdir(target_dir, parents=True)

    file_types = args.types.split(",")
    if not file_types:
        raise ValueError("No file types specified for extraction!")

    foundation_dir = Path(args.sourcedir).resolve()
    if not foundation_dir.exists():
        raise FileNotFoundError(f"Source directory {foundation_dir} does not exist!")

    logger.info(f"Extracting core files from {foundation_dir}...")
    logger.debug(f"(Extracting types: {', '.join(file_types)})")
    process_directory(foundation_dir, target_dir, file_types, args.include)

    if args.expansions:
        logger.info("Checking for expansions...")
        # Find all expansion folders in foundation_dir/extensions that start with 'ego_dlc_'
        extensions_dir = foundation_dir / "extensions"
        if extensions_dir.exists() and extensions_dir.is_dir():
            official_expansions: list[Path] = [
            d for d in extensions_dir.iterdir()
            if d.is_dir() and d.name.startswith("ego_dlc_")
            ]
            logger.debug(f"Expansions detected: {[d.name for d in official_expansions]}")
        else:
            official_expansions = []
            logger.warning(f"No expansions directory found at {extensions_dir}!")
            return

        for expansion in official_expansions:
            logger.info(f"Extracting files from expansion {EXPANSIONS[expansion.name]}...")
            expansion_target_dir = target_dir / expansion.name
            if not expansion_target_dir.exists():
                Path.mkdir(expansion_target_dir, parents=True)
            process_directory(expansion, expansion_target_dir, file_types, [])


if __name__ == "__main__":
    args = parse_arguments()
    main(args)
