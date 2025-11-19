"""Cipher CLI Module.

Command-line interface for file encryption and decryption operations using
RSA public/private key pairs. This module provides a user-friendly interface
to encrypt and decrypt files or entire folders.

The module supports:
- File and folder encryption with RSA public keys
- File and folder decryption with RSA private keys
- Automatic error handling and user-friendly messages
- Batch processing of multiple files in folders

Typical usage:
    # Encrypt a file
    python cipher_cli.py encrypt public_key.pem input.txt output_folder/
    
    # Decrypt a file
    python cipher_cli.py decrypt private_key.pem encrypted.bin output_folder/
    
    # Encrypt all files in a folder
    python cipher_cli.py encrypt public_key.pem input_folder/ output_folder/
"""

import sys
from typing import Annotated

import typer

from teletools.cipher import decrypt_file_or_folder, encrypt_file_or_folder

# Initialize Typer app with enhanced configuration
app = typer.Typer(
    name="cipher",
    help="File encryption and decryption CLI tool using RSA keys.",
    add_completion=False,
)


@app.command(name="encrypt")
def encrypt(
    public_key_file: Annotated[
        str,
        typer.Argument(
            help="Path to the public key file used for encryption. Must be a valid file containing the public key in the appropriate format.",
            metavar="PUBLIC_KEY_FILE",
        ),
    ],
    input_file_or_folder: Annotated[
        str,
        typer.Argument(
            help="Path to the input file or folder to be encrypted. If a folder is provided, all files within it will be encrypted (non-recursively).",
            metavar="INPUT_PATH",
        ),
    ],
    output_folder: Annotated[
        str,
        typer.Argument(
            help="Path to the output folder where encrypted content will be saved. If not specified, encrypted files will be saved in the same location as the input.",
            metavar="OUTPUT_FOLDER",
        ),
    ] = None,
) -> None:
    """Encrypt files using RSA public key.
    
    This command encrypts one or more files using the specified RSA public key.
    The encryption process uses hybrid encryption combining RSA and AES for
    efficient handling of large files.
    
    Args:
        public_key_file: Path to the RSA public key file (PEM format)
        input_file_or_folder: Path to file or folder to encrypt
        output_folder: Destination folder for encrypted files (optional)
        
    Returns:
        None: Results are displayed to console
        
    Raises:
        typer.Exit: On encryption failure or invalid inputs
        
    Examples:
        # Encrypt a single file
        $ python cipher_cli.py encrypt public.pem data.txt encrypted/
        
        # Encrypt all files in a folder
        $ python cipher_cli.py encrypt public.pem data_folder/ encrypted/
        
        # Encrypt to same location
        $ python cipher_cli.py encrypt public.pem data.txt
    """
    try:
        encrypt_file_or_folder(public_key_file, input_file_or_folder, output_folder)
        typer.echo("✅ Encryption completed successfully!")
    except FileNotFoundError as e:
        typer.echo(f"❌ File Error: {e}", err=True)
        raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"❌ Encryption Failed: {e}", err=True)
        raise typer.Exit(code=1)


@app.command(name="decrypt")
def decrypt(
    private_key_file: Annotated[
        str,
        typer.Argument(
            help="Path to the private key file used for decryption. Must be a valid file containing the private key in the appropriate format.",
            metavar="PRIVATE_KEY_FILE",
        ),
    ],
    input_file_or_folder: Annotated[
        str,
        typer.Argument(
            help="Path to the input file or folder to be decrypted. If a folder is provided, all files within it will be decrypted (non-recursively).",
            metavar="INPUT_PATH",
        ),
    ],
    output_folder: Annotated[
        str,
        typer.Argument(
            help="Path to the output folder where decrypted content will be saved. If not specified, decrypted files will be saved in the same location as the input.",
            metavar="OUTPUT_FOLDER",
        ),
    ] = None,
) -> None:
    """Decrypt files using RSA private key.
    
    This command decrypts one or more files that were encrypted using the
    corresponding RSA public key. The decryption process reverses the hybrid
    encryption (RSA + AES) used during encryption.
    
    Args:
        private_key_file: Path to the RSA private key file (PEM format)
        input_file_or_folder: Path to encrypted file or folder
        output_folder: Destination folder for decrypted files (optional)
        
    Returns:
        None: Results are displayed to console
        
    Raises:
        typer.Exit: On decryption failure or invalid inputs
        
    Examples:
        # Decrypt a single file
        $ python cipher_cli.py decrypt private.pem encrypted.bin decrypted/
        
        # Decrypt all files in a folder
        $ python cipher_cli.py decrypt private.pem encrypted_folder/ decrypted/
        
        # Decrypt to same location
        $ python cipher_cli.py decrypt private.pem encrypted.bin
    """
    try:
        decrypt_file_or_folder(private_key_file, input_file_or_folder, output_folder)
        typer.echo("✅ Decryption completed successfully!")
    except FileNotFoundError as e:
        typer.echo(f"❌ File Error: {e}", err=True)
        raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"❌ Decryption Failed: {e}", err=True)
        raise typer.Exit(code=1)


def main() -> None:
    """Main entry point for the cipher CLI application.
    
    Handles global error catching and provides user-friendly error messages
    for common issues like missing dependencies, invalid keys, or file access
    problems. Ensures proper exit codes for different error scenarios.
    
    Exit Codes:
        0: Success
        1: General error (file not found, invalid key, encryption/decryption failure)
        130: User interruption (Ctrl+C)
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
            "pip install cryptography"
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