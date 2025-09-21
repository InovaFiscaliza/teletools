from dataclasses import dataclass
from pathlib import Path

import gnupg

GPG_FILE_PATTERN = "*.gpg"


@dataclass
class FileCipher:
    @staticmethod
    def _encrypt_file(public_key_file: Path, input_file: Path, output_folder: Path):
        """
        Encrypts a file using a public key and saves the encrypted file to the specified output folder.

        Args:
            public_key_file (Path): Path to the public key file used for encryption.
            input_file (Path): Path to the file to be encrypted.
            output_folder (Path): Path to the folder where the encrypted file will be saved.

        Raises:
            ValueError: If the provided public key file is not valid or contains no keys.

        Side Effects:
            Creates an encrypted file in the output folder with the same name as the input file, appended with '.gpg'.
            Prints a success message if the file is encrypted successfully.
        """
        gpg = gnupg.GPG()
        try:
            results = gpg.import_keys_file(public_key_file)
            assert results.count > 0
        except Exception as e:
            raise FileNotFoundError(
                f"Error {e} reading public key file: {public_key_file}."
            )

        output_file = output_folder / (input_file.name + ".gpg")

        with open(input_file, "rb") as f:
            status = gpg.encrypt_file(
                f,
                recipients=results.fingerprints,
                output=output_file,
                always_trust=True,
            )
            if status.ok:
                print(f"File {input_file} successfully encrypted to {output_file}")

    @staticmethod
    def _encrypt_folder(public_key_file: Path, input_folder: Path, output_folder: Path):
        """
        Encrypts all files in the specified input folder using the provided public key file and saves the encrypted files to the output folder.

        Args:
            public_key_file (Path): Path to the public key file used for encryption.
            input_folder (Path): Path to the folder containing files to be encrypted.
            output_folder (Path): Path to the folder where encrypted files will be saved.

        Returns:
            None

        Prints:
            A message if there are no files to encrypt in the input folder.
        """
        input_files = [file for file in input_folder.glob("*.*") if file.is_file()]
        if len(input_files) == 0:
            print(f"There is no file to encrypt in folder {input_folder}.")
            return

        for input_file in input_files:
            FileCipher._encrypt_file(public_key_file, input_file, output_folder)

    @staticmethod
    def encrypt(public_key_file, input_file_or_folder, output_folder=None):
        """
        Encrypts a file or all files in a folder using the provided public key.

        Args:
            public_key_file (str or Path): Path to the public key file.
            input_file_or_folder (str or Path): Path to the file or folder to encrypt.
            output_folder (str or Path, optional): Path to the output folder. If None, uses the input's parent or itself.

        Raises:
            FileNotFoundError: If the public key file or input file/folder does not exist.
            OSError: If there is an error reading the input or creating the output folder. This may be raised from _create_output_folder and is not caught here.

        Side Effects:
            Creates the output folder if it does not exist.
        """
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
                f"Input path '{input_file_or_folder}' is neither a file nor a directory."
            )

    @staticmethod
    def _decrypt_file(private_key_file: Path, input_file: Path, output_folder: Path):
        """
        Decrypts an encrypted file using a private key and saves the decrypted output to a specified folder.

        Args:
            private_key_file (Path): Path to the private key file used for decryption.
            input_file (Path): Path to the encrypted input file.
            output_folder (Path): Path to the folder where the decrypted file will be saved.

        Raises:
            ValueError: If the provided private key file is not valid or cannot be imported.

        Prints:
            Success message indicating the input file was successfully decrypted and the location of the output file.
        """
        gpg = gnupg.GPG()
        try:
            results = gpg.import_keys_file(private_key_file)
            assert results.count > 0
        except Exception as e:
            raise FileNotFoundError(
                f"Error {e} reading public key file: {private_key_file}."
            )

        output_file = output_folder / input_file.stem

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
        """
        Decrypts all '.gpg' files in the specified input folder using the provided private key file,
        and writes the decrypted files to the output folder.

        Args:
            private_key_file (Path): Path to the private key file.
            input_folder (Path): Path to the folder containing '.gpg' files to decrypt.
            output_folder (Path): Path to the folder where decrypted files will be saved.

        Prints a message if no files are found to decrypt.
        """
        input_files = [
            file for file in input_folder.glob(GPG_FILE_PATTERN) if file.is_file()
        ]
        if len(input_files) == 0:
            print(f"There is no file to decrypt in folder {input_folder}.")
            return

        for input_file in input_files:
            FileCipher._decrypt_file(private_key_file, input_file, output_folder)

    @staticmethod
    def decrypt(private_key_file, input_file_or_folder, output_folder=None):
        """
        Decrypts a file or all files in a folder using the provided private key.

        Args:
            private_key_file (str or Path): Path to the private key file.
            input_file_or_folder (str or Path): Path to the file or folder to decrypt.
            output_folder (str or Path, optional): Path to the output folder. If None, uses the input's parent or itself.

        Raises:
            FileNotFoundError: If the private key file or input file/folder does not exist.
            OSError: If there is an error reading the input or creating the output folder. This may be raised from _create_output_folder and is not caught here.
        """
        private_key_file = Path(private_key_file).expanduser()
        if not private_key_file.exists():
            raise FileNotFoundError(f"Private key file {private_key_file} not found.")

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
        """
        Creates and returns the output folder based on the provided input file or folder and output folder path.

        If `output_folder` is None:
            - If `input_file_or_folder` is a file, uses its parent directory as the output folder.
            - If `input_file_or_folder` is a directory, uses it as the output folder.
        Otherwise:
            - Expands the user path in `output_folder` and uses it.

        Ensures the output folder exists by creating it if necessary.

        Args:
            input_file_or_folder (Path): The input file or folder as a Path object.
            output_folder (str or Path or None): The desired output folder path, or None to infer from input.

        Returns:
            Path: The Path object of the output folder.

        Raises:
            OSError: If there is an error creating the output folder.
        """
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
