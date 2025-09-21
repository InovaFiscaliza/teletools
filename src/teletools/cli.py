from typing import Annotated

import typer
from cipher import FileCipher

app = typer.Typer()


@app.command()
def encrypt(
    public_key_file: Annotated[
        str,
        typer.Argument(
            help="Path to the public key file used for encryption. Must be a valid file containing the public key in the appropriate format."
        ),
    ],
    input_file_or_folder: Annotated[
        str,
        typer.Argument(
            help="Path to the input file or folder to be encrypted. If a folder is provided, all files within it will be encrypted (non-recursively)."
        ),
    ],
    output_folder: Annotated[
        str,
        typer.Argument(
            help="Path to the output folder where encrypted content will be saved. If not specified encrypted files will be saved in the same location as the input."
        ),
    ] = None,
):
    FileCipher.encrypt(public_key_file, input_file_or_folder, output_folder)


@app.command()
def decrypt(
    private_key_file: Annotated[
        str,
        typer.Argument(
            help="Path to the private key file used for decryption. Must be a valid file containing the private key in the appropriate format."
        ),
    ],
    input_file_or_folder: Annotated[
        str,
        typer.Argument(
            help="Path to the input file or folder to be decrypted. If a folder is provided, all files within it will be decrypted (non-recursively)."
        ),
    ],
    output_folder: Annotated[
        str,
        typer.Argument(
            help="Path to the output folder where decrypted content will be saved. If not specified decrypted files will be saved in the same location as the input."
        ),
    ] = None,
):
    FileCipher.decrypt(private_key_file, input_file_or_folder, output_folder)


if __name__ == "__main__":
    app()
