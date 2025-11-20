"""ABR Database Loader CLI Tool.

Command-line interface for importing Brazilian telecom data from
ABR Telecom into a PostgreSQL database.

This CLI provides two main commands:

1. load-portability: Import phone number portability data from PIP reports
2. load-numbering-plan: Import numbering plan data from NSAPN public files (STFC, SMP, SME, CNG, SUP)

Features:
- Import single files or entire directories
- Automatic file type detection (for numbering plan)
- Configure target database table and schema
- Control data loading behavior (truncate vs append)
- Monitor import progress with detailed logging
- Optimized chunked processing for large files

Usage Examples:
    # Import portability data
    abr_loader load-portability /path/to/pip_report.csv.gz

    # Import numbering plan data (ZIP files)
    abr_loader load-numbering-plan /path/to/nsapn_files/

    # Import to custom table and schema
    abr_loader load-portability /path/to/data/ custom_table custom_schema

    # Import without truncating existing data
    abr_loader load-portability /path/to/data/ --no-truncate-table
    abr_loader load-numbering-plan /path/to/data/ entrada --no-truncate-table

Requirements:
    - PostgreSQL database connection configured in _database_config.py
    - For portability: CSV files in ABR PIP format (*.csv.gz)
    - For numbering plan: ZIP files from ABR NSAPN portal (*.zip)
    - Required Python packages: typer, pandas, psycopg2

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
    table_name: Annotated[
        str,
        typer.Argument(
            help="Database table name for data storage. "
            "Table will be created automatically if it doesn't exist.",
            metavar="TABLE_NAME",
        ),
    ] = "abr_portabilidade",
    schema: Annotated[
        str,
        typer.Argument(
            help="Database schema name for table organization. "
            "Schema must exist in the target database.",
            metavar="SCHEMA_NAME",
        ),
    ] = "entrada",
    truncate_table: Annotated[
        bool,
        typer.Option(
            "--truncate-table/--no-truncate-table",
            help="Truncate table before import. "
            "When enabled, existing data will be deleted before import. "
            "Use --no-truncate-table to append to existing data.",
        ),
    ] = True,
    rebuild_database: Annotated[
        bool,
        typer.Option(
            "--rebuild-database/--no-rebuild-database",
            help="Rebuild database entire portability database. "
            "When enabled, existing data will be deleted before import. "
            "Use --no-rebuild-database to append to existing data.",
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
        table_name: Target database table (created if doesn't exist)
        schema: Target database schema (must already exist)
        truncate_table: Whether to clear existing data before import
        rebuild_database: Whether to rebuild the entire database before import

    Returns:
        None: Results are logged to console and log file

    Raises:
        typer.Exit: On file not found, database connection errors, or import failures

    Examples:
        Import single file with default settings:
        $ abr_loader load-portability data.csv.gz

        Import directory to custom table:
        $ abr_loader load-portability /data/ my_table my_schema

        Append data without truncating:
        $ abr_loader load-portability /data/ --no-truncate-table
    """

    # Execute the import process
    load_pip_reports(
        input_path=input_path,
        table_name=table_name,
        schema=schema,
        truncate_table=truncate_table,
        rebuild_database=rebuild_database,
    )


@app.command(name="load-nsapn")
def load_nsapn(
    input_path: Annotated[
        str,
        typer.Argument(
            help="Path to input file or directory. "
            "If directory provided, all *.csv.gz files will be processed recursively. "
            "Supports single files or batch processing.",
            metavar="INPUT_PATH",
        ),
    ],
    schema: Annotated[
        str,
        typer.Argument(
            help="Database schema name for table organization. "
            "Schema must exist in the target database.",
            metavar="SCHEMA_NAME",
        ),
    ] = "entrada",
    truncate_table: Annotated[
        bool,
        typer.Option(
            "--truncate-table/--no-truncate-table",
            help="Truncate table before import. "
            "When enabled, existing data will be deleted before import. "
            "Use --no-truncate-table to append to existing data.",
        ),
    ] = True,
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
        schema: Target database schema (must already exist)
        truncate_table: Whether to clear existing data before import

    Returns:
        None: Results are logged to console and log file

    Raises:
        typer.Exit: On file not found, database connection errors, or import failures

    Examples:
        Import single ZIP file with default settings:
        $ abr_loader load-numbering-plan STFC_202401.zip

        Import directory of ZIP files to custom schema:
        $ abr_loader load-numbering-plan /data/nsapn/ custom_schema

        Append data without truncating:
        $ abr_loader load-numbering-plan /data/nsapn/ --no-truncate-table
    """
    load_nsapn_files(
        input_path=input_path, schema=schema, truncate_table=truncate_table
    )


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
