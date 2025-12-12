"""ABR Database Loader CLI Tool.

Command-line interface for importing Brazilian telecom data from
ABR Telecom into a PostgreSQL database.

This CLI provides three main commands:

1. load-pip: Import phone number portability data from PIP reports
2. load-nsapn: Import numbering plan data from NSAPN public files (STFC, SMP, SME, CNG, SUP)
3. test-connection: Test PostgreSQL database connectivity and configuration

Features:
- Import single files or entire directories
- Automatic file type detection (for numbering plan)
- Control data loading behavior (truncate vs append)
- Monitor import progress with detailed logging
- Optimized chunked processing for large files

Usage Examples:
    # Import portability data
    abr_loader load-pip /path/to/pip_report.csv.gz

    # Import numbering plan data (ZIP files)
    abr_loader load-nsapn /path/to/nsapn_files/

    # Import with rebuild database option
    abr_loader load-pip /path/to/data/ --rebuild-database

    # Import without truncating existing data
    abr_loader load-pip /path/to/data/ --no-truncate-table

    # Test database connection
    abr_loader test-connection

Requirements:
    - PostgreSQL database connection configured via .env file
    - Required environment variables: DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
    - Optional: DB_SCHEMA (defaults to 'cdr')
    - For portability: CSV files in ABR PIP format (*.csv.gz)
    - For numbering plan: ZIP files from ABR NSAPN portal (*.zip)
    - Required Python packages: typer, pandas, psycopg2, python-dotenv

Data Sources:
    - Portability: ABR Telecom PIP system reports (restricted access)
    - Numbering Plan: https://easi.abrtelecom.com.br/nsapn/#/public/files/download/
"""

import sys
from typing import Annotated

import typer

from ._abr_numeracao import load_nsapn_files
from ._abr_portabilidade import load_pip_reports
from ._database_config import validate_connection

# Initialize Typer app with enhanced configuration
app = typer.Typer(
    name="abr-loader",
    help="ABR Database Loader - Import Brazilian telecom portability and numbering plan data.",
    add_completion=False,
)


@app.command(name="load-pip")
def load_pip(
    input_path: Annotated[
        str,
        typer.Argument(
            help="Path to input file or directory. "
            "If directory provided, all *.csv.gz files will be processed recursively. "
            "Supports single files or batch processing.",
            metavar="INPUT_PATH",
        ),
    ],
    drop_table: Annotated[
        bool,
        typer.Option(
            "--drop-table/--no-drop-table",
            help="Drop table after import. "
            "When enabled, imported data will be deleted after import. "
            "Use --no-drop-table to keep it after import.",
        ),
    ] = False,
    rebuild_database: Annotated[
        bool,
        typer.Option(
            "--rebuild-database/--no-rebuild-database",
            help="Rebuild entire portability database. "
            "When enabled, existing data will be deleted before import. "
            "Use --no-rebuild-database to append to existing data.",
        ),
    ] = False,
    rebuild_indexes: Annotated[
        bool,
        typer.Option(
            "--rebuild-indexes/--no-rebuild-indexes",
            help="Rebuild portability database indexes."
            "When enabled, existing indexes will be deleted before import and rebuilt. "
            "Use --no-rebuild-indexes to keep existing indexes.",
        ),
    ] = False,
) -> None:
    """Import ABR portability data into PostgreSQL database.

    This command processes Brazilian phone number portability reports from
    ABR Telecom's PIP system. The input files should be in CSV format
    (*.csv.gz) with specific column structure defined by ABR standards.

    The import process includes:
    - Automatic table creation with optimized schema
    - Chunked processing for memory efficiency
    - Bulk insertions using PostgreSQL COPY FROM
    - Comprehensive progress tracking and error handling
    - Data type optimization and validation

    Args:
        input_path: Path to CSV file or directory containing CSV files
        drop_table: Whether to drop staging table after import (default: False)
        rebuild_database: Whether to rebuild the entire portability database before import
        rebuild_indexes: Whether to rebuild portability database indexes

    Returns:
        None: Results are logged to console and log file

    Raises:
        typer.Exit: On file not found, database connection errors, or import failures

    Examples:
        Import single file with default settings:
        $ abr_loader load-pip data.csv.gz

        Import directory with rebuild database:
        $ abr_loader load-pip /data/ --rebuild-database

        Drop staging table after import:
        $ abr_loader load-pip /data/ --drop-table
    """

    # Execute the import process
    load_pip_reports(
        input_path=input_path,
        drop_table=drop_table,
        rebuild_database=rebuild_database,
        rebuild_indexes=rebuild_indexes,
    )


@app.command(name="load-nsapn")
def load_nsapn(
    input_path: Annotated[
        str,
        typer.Argument(
            help="Path to input file or directory. "
            "If directory provided, all *.zip files will be processed recursively. "
            "Supports single files or batch processing.",
            metavar="INPUT_PATH",
        ),
    ],
    drop_table: Annotated[
        bool,
        typer.Option(
            "--drop-table/--no-drop-table",
            help="Drop table after import. "
            "When enabled, imported data will be deleted after import. "
            "Use --no-drop-table to keep it after import.",
        ),
    ] = False,
) -> None:
    """Import ABR numbering plan data into PostgreSQL database.

    This command processes Brazilian numbering plan public files from ABR Telecom's
    NSAPN system. The input files should be ZIP archives (*.zip) downloaded
    from the official ABR portal containing CSV files with numbering data.

    Supported file types (auto-detected by filename prefix):
    - STFC: Fixed telephony service numbering (complete data)
    - SMP/SME: Mobile service numbering (subset of columns)
    - CNG: Non-geographic codes (0800, 0300, etc.)
    - SUP: Public utility service numbering
    - STFC-FATB: Fixed telephony outside basic tariff area

    Data sources:
        https://easi.abrtelecom.com.br/nsapn/#/public/files/download/

    The import process includes:
    - Automatic file type detection based on filename
    - Automatic table creation with optimized schema
    - ZIP file extraction and processing
    - Chunked processing for memory efficiency
    - Bulk insertions using PostgreSQL COPY FROM
    - Comprehensive progress tracking and error handling
    - Data type optimization and validation

    Args:
        input_path: Path to ZIP file or directory containing ZIP files
        drop_table: Whether to drop existing data after import

    Returns:
        None: Results are logged to console and log file

    Raises:
        typer.Exit: On file not found, database connection errors, or import failures

    Examples:
        Import single ZIP file:
        $ abr_loader load-nsapn STFC_202401.zip

        Import directory of ZIP files:
        $ abr_loader load-nsapn /data/nsapn/

        Append data without truncating:
        $ abr_loader load-nsapn /data/nsapn/ --no-drop-table
    """
    load_nsapn_files(input_path=input_path, drop_table=drop_table)


@app.command(name="test-connection")
def test_connection() -> None:
    """Test database connection and validate configuration.

    This command verifies that the database connection is properly configured
    and can be established successfully. It checks:
    - Environment variables are properly set (.env file)
    - Database server is reachable
    - Credentials are valid
    - Connection can be established

    The test performs a simple query to verify full connectivity.

    Returns:
        None: Outputs connection status to console

    Raises:
        typer.Exit: On connection failure with detailed error message

    Examples:
        Test database connection:
        $ abr_loader test-connection

        Use before running imports to verify setup:
        $ abr_loader test-connection && abr_loader load-pip data.csv.gz
    """
    typer.echo("🔍 Testing database connection...")
    typer.echo("")

    try:
        if validate_connection():
            typer.echo("✅ Database connection successful!")
            typer.echo("✓ Configuration is valid")
            typer.echo("✓ Server is reachable")
            typer.echo("✓ Credentials are correct")
            typer.echo("")
            typer.echo("💡 You can now proceed with data import operations.")
        else:
            typer.echo("❌ Database connection failed!", err=True)
            typer.echo("", err=True)
            typer.echo("🔧 Troubleshooting steps:", err=True)
            typer.echo("  1. Check if .env file exists and is properly configured", err=True)
            typer.echo("  2. Verify database server is running", err=True)
            typer.echo("  3. Confirm credentials are correct", err=True)
            typer.echo("  4. Check network connectivity to database server", err=True)
            typer.echo("", err=True)
            typer.echo("📖 See .env.example for configuration template", err=True)
            raise typer.Exit(code=1)

    except ValueError as e:
        typer.echo(f"❌ Configuration Error: {e}", err=True)
        typer.echo("", err=True)
        typer.echo("💡 Hint: Create .env file from .env.example template", err=True)
        typer.echo("   cp .env.example .env", err=True)
        typer.echo("   # Edit .env with your database credentials", err=True)
        raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"❌ Connection Error: {e}", err=True)
        raise typer.Exit(code=1)


def main() -> None:
    """Main entry point for the CLI application.

    Handles global error catching and provides user-friendly error messages
    for common issues like missing dependencies or database connection problems.
    """
    try:
        app()
    except KeyboardInterrupt:
        typer.echo("\n⚠️  Operation cancelled by user.")
        sys.exit(130)  # Standard exit code for SIGINT
    except ImportError as e:
        typer.echo(
            f"❌ Import Error: Missing required dependency: {e}",
            err=True,
        )
        typer.echo("💡 Hint: Install missing packages with: uv sync")
        sys.exit(1)
    except Exception as e:
        typer.echo(
            f"❌ Unexpected Error: {e}",
            err=True,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
