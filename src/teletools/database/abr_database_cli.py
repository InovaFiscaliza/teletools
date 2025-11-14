"""ABR Database CLI Tool.

Command-line interface for importing Brazilian telecom portability data from
ABR (Agência Brasileira de Telecomunicações) PIP system reports into a
PostgreSQL database.

This CLI provides functionality to:
- Import single CSV files or entire directories of portability reports
- Configure target database table and schema
- Control data loading behavior (truncate vs append)
- Monitor import progress with detailed logging

Usage Examples:
    # Import single file
    python abr_database_cli.py load-portability /path/to/file.csv.gz
    
    # Import all files from directory
    python abr_database_cli.py load-portability /path/to/directory/
    
    # Import to custom table and schema
    python abr_database_cli.py load-portability /path/to/data/ custom_table custom_schema
    
    # Import without truncating existing data
    python abr_database_cli.py load-portability /path/to/data/ --no-truncate-table

Requirements:
    - PostgreSQL database connection configured in _database_config.py
    - CSV files in ABR PIP format (*.csv.gz)
    - Required Python packages: typer, pandas, psycopg2
"""

from typing import Annotated
import sys
from pathlib import Path

import typer
from typer import Exit

from _abr_portabilidade import load_pip_reports

# Initialize Typer app with enhanced configuration
app = typer.Typer(
    name="abr-database",
    help="ABR Database CLI Tool for importing Brazilian telecom portability data.",
    add_completion=False,
)


@app.command(name="load-portability")
def load_portabilidade(
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
        
    Returns:
        None: Results are logged to console and log file
        
    Raises:
        typer.Exit: On file not found, database connection errors, or import failures
        
    Examples:
        Import single file with default settings:
        $ python abr_database_cli.py load-portability data.csv.gz
        
        Import directory to custom table:
        $ python abr_database_cli.py load-portability /data/ my_table my_schema
        
        Append data without truncating:
        $ python abr_database_cli.py load-portability /data/ --no-truncate-table
    """
    # Validate input path exists
    input_file_path = Path(input_path)
    if not input_file_path.exists():
        typer.echo(
            f"❌ Error: Input path '{input_path}' does not exist.",
            err=True,
        )
        raise Exit(code=1)
    
    # Display import configuration
    typer.echo("🚀 Starting ABR Portability Data Import")
    typer.echo(f"📁 Input: {input_path}")
    typer.echo(f"🗄️  Target: {schema}.{table_name}")
    typer.echo(f"🔄 Truncate: {'Yes' if truncate_table else 'No'}")
    typer.echo("" + "─" * 50)
    
    try:
        # Execute the import process
        results = load_pip_reports(
            input_path=input_path,
            table_name=table_name, 
            schema=schema,
            truncate_table=truncate_table
        )
        
        # Display results summary
        if results:
            successful_imports = sum(
                1 for result in results.values() 
                if result.get("status") == "success"
            )
            total_files = len(results)
            
            typer.echo("" + "─" * 50)
            typer.echo("✅ Import completed successfully!")
            typer.echo(f"📊 Files processed: {successful_imports}/{total_files}")
            
            if successful_imports < total_files:
                typer.echo(
                    f"⚠️  Warning: "
                    f"{total_files - successful_imports} files failed to import."
                )
        else:
            typer.echo("ℹ️  Info: No files were processed.")
            
    except FileNotFoundError as e:
        typer.echo(
            f"❌ File Error: {e}",
            err=True,
        )
        raise Exit(code=1)
        
    except Exception as e:
        typer.echo(
            f"❌ Import Failed: {e}",
            err=True,
        )
        raise Exit(code=1)


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
        typer.echo(
            "💡 Hint: Install missing packages with: "
            "pip install -r requirements.txt"
        )
        sys.exit(1)
    except Exception as e:
        typer.echo(
            f"❌ Unexpected Error: {e}",
            err=True,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()