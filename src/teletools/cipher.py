from dataclasses import dataclass
from pathlib import Path

import gnupg


@dataclass
class FileCipher:
    @staticmethod
    def _encrypt_file(public_key_file: Path, input_file: Path, output_folder: Path):
        gpg = gnupg.GPG()
        results = gpg.import_keys_file(public_key_file)
        if results.count == 0:
            raise ValueError(f"Key file provided is not valid: {public_key_file}.")

        output_file = output_folder / (input_file.name + ".gpg")

        with open(input_file, "rb") as f:
            status = gpg.encrypt_file(
                f,
                recipients=results.fingerprints,
                output=output_file,
                always_trust=True,
            )
            if status.ok:
                print(f"File {input_file} sucessfully encrypted to {output_file}")

    @staticmethod
    def _encrypt_folder(public_key_file: Path, input_folder: Path, output_folder: Path):
        input_files = [file for file in input_folder.glob("*.*") if file.is_file()]
        if len(input_files) == 0:
            print(f"There is no file to encrypt in folder {input_folder}.")
            return

        for input_file in input_files:
            FileCipher._encrypt_file(public_key_file, input_file, output_folder)

    @staticmethod
    def encrypt(public_key_file, input_file_or_folder, output_folder=None):
        public_key_file = Path(public_key_file).expanduser()
        if not public_key_file.exists():
            raise FileNotFoundError(f"Public key file {public_key_file} not found.")

        input_file_or_folder = Path(input_file_or_folder).expanduser()
        if not input_file_or_folder.exists():
            raise FileNotFoundError(
                f"Input file or folder {input_file_or_folder} not found."
            )

        output_folder = FileCipher._create_output_folder(
            input_file_or_folder, output_folder
        )

        if input_file_or_folder.is_file():
            FileCipher._encrypt_file(
                public_key_file, input_file_or_folder, output_folder
            )
        elif input_file_or_folder.is_dir():
            FileCipher._encrypt_folder(
                public_key_file, input_file_or_folder, output_folder
            )
        else:
            raise OSError(
                f"Unexpected error reading input file or folder {input_file_or_folder}."
            )

    @staticmethod
    def _decrypt_file(private_key_file: Path, input_file: Path, output_folder: Path):
        gpg = gnupg.GPG()
        results = gpg.import_keys_file(private_key_file)
        if results.count == 0:
            raise ValueError(f"Key file provided is not valid: {private_key_file}.")

        output_file = output_folder / (input_file.name + ".gpg")

        with open(input_file, "rb") as f:
            status = gpg.decrypt_file(
                f,
                passphrase=None,
                output=output_file,
            )
            if status.ok:
                print(f"File {input_file} sucessfully decrypted to {output_file}")

    @staticmethod
    def _decrypt_folder(private_key_file: Path, input_folder: Path, output_folder):
        input_files = [file for file in input_folder.glob("*.gpg") if file.is_file()]
        if len(input_files) == 0:
            print(f"There is no file to decrypt in folder {input_folder}.")
            return

        for input_file in input_files:
            FileCipher._decrypt_file(private_key_file, input_file, output_folder)

    @staticmethod
    def decrypt(private_key_file, input_file_or_folder, output_folder=None):
        private_key_file = Path(private_key_file).expanduser()
        if not private_key_file.exists():
            raise FileNotFoundError(f"Public key file {private_key_file} not found.")

        input_file_or_folder = Path(input_file_or_folder).expanduser()
        if not input_file_or_folder.exists():
            raise FileNotFoundError(
                f"Input file or folder {input_file_or_folder} not found."
            )

        output_folder = FileCipher._create_output_folder(
            input_file_or_folder, output_folder
        )

        if input_file_or_folder.is_file():
            FileCipher._decrypt_file(
                private_key_file, input_file_or_folder, output_folder
            )
        elif input_file_or_folder.is_dir():
            FileCipher._decrypt_folder(
                private_key_file, input_file_or_folder, output_folder
            )
        else:
            raise OSError(
                f"Unexpected error reading input file or folder {input_file_or_folder}."
            )

    @staticmethod
    def _create_output_folder(input_file_or_folder, output_folder):
        try:
            if output_folder is None:
                if input_file_or_folder.is_file():
                    output_folder = input_file_or_folder.parent
                elif input_file_or_folder.is_dir():
                    output_folder = input_file_or_folder
            else:
                output_folder = Path(output_folder).expanduser()
            output_folder.mkdir(exist_ok=True)
            return output_folder
        except Exception as e:
            raise OSError(f"Error {e} creating output folder {output_folder}")
