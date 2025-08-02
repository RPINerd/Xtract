"""Extracts files from Egosoft's X4 Foundations cat files."""

import argparse
import logging
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode="w",
    filename=f"xtract_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
)
logger = logging.getLogger(__name__)
console = Console()

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


def extract_cat(cat_file: Path, output: Path, extensions: list[str]) -> None:
    """
    Extracts files from a cat file.

    Args:
        cat_file (Path): The path to the cat file.
        output (Path): The base directory where extracted files will be saved.
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
        for i, line in enumerate(c_file, start=1):
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


def collect_files(source_dir: Path, include: list[str]) -> list[Path]:
    """
    Process a directory and return a list of cat files.

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
    return extract_files


def extraction_job(target: str, files: list[Path], output_dir: Path, extensions: list[str]) -> None:
    """
    Extract all files for a given target (base or expansion).

    Args:
        target (str): The name of the extraction target.
        files (list[Path]): List of cat files to extract.
        output_dir (Path): Directory to extract files into.
        extensions (list[str]): List of file extensions to extract.
    """
    with Progress(
        SpinnerColumn(),
        TextColumn(f"[progress.description]{EXPANSIONS.get(target, "Base Game"):{" "}<20} "),
        BarColumn(bar_width=None),
        TextColumn("[progress.percentage]{task.percentage:>3.1f}%  "),
        console=console,
    ) as progress:
        task_id = progress.add_task(f"{EXPANSIONS.get(target, "Base Game")}", total=len(files))
        for cat_file in files:
            try:
                extract_cat(cat_file, output_dir, extensions)
            except Exception as e:
                logger.error(f"Error extracting {cat_file}: {e}")
            progress.update(task_id, description=f"{cat_file.name}..", advance=1)


def main(
    foundation_dir: Path,
    target_dir: Path,
    expansions: bool,
    file_types: list[str],
    files_specified: list[str],
    mods: bool = False) -> None:
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
    extraction_targets: dict[str, list[Path]] = {}

    logger.info(f"Extracting core files from {foundation_dir}...")
    logger.debug(f"(Extracting types: {', '.join(file_types)})")
    extraction_targets["base"] = collect_files(foundation_dir, files_specified)

    if expansions:
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
            extraction_targets[expansion.name] = collect_files(expansion, files_specified)

    if mods:
        # TODO: Implement mod extraction logic
        logger.warning("Mod extraction is not implemented yet.")
        pass

    # Prepare extraction jobs for parallel execution
    with ThreadPoolExecutor() as executor:
        futures = []
        for target, files in extraction_targets.items():
            logger.debug(f"Target {target} has {len(files)} files to extract.")
            output_dir = target_dir if target == "base" else target_dir / target
            futures.append(
                executor.submit(
                    extraction_job,
                    target,
                    files,
                    output_dir,
                    file_types,
                )
            )
        # Wait for all jobs to complete
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                logger.error(f"Extraction job failed: {e}")


if __name__ == "__main__":
    args = parse_arguments()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    foundation_dir = Path(args.sourcedir).resolve()
    if not foundation_dir.exists():
        logger.error(f"Source directory {foundation_dir} does not exist!")
        sys.exit(1)

    file_types: list[str] = args.types.split(",")
    if not file_types:
        logger.error("File type flag provided without any extensions!")
        sys.exit(1)

    target_dir = Path(args.destdir).resolve()
    if not target_dir.exists():
        logger.debug(f"Creating target directory {target_dir}...")
        Path.mkdir(target_dir, parents=True)

    files_specified: list[str] = []
    for file in args.include:
        if file.endswith(".cat"):
            files_specified.append(file)
        else:
            logger.warning(f"File {file} does not appear to be a *.cat file, ignoring it.")
    if not files_specified:
        logger.info("No specific files provided for extraction, extracting all cat files found.")
        files_specified = []

    main(foundation_dir, target_dir, args.expansions, file_types, files_specified)
