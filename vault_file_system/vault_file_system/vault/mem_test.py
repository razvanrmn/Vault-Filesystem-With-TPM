import datetime
import logging
import os

from fs import copy
from fs.errors import DirectoryExists, DirectoryExpected, FileExists, FileExpected, ResourceNotFound
import fs

# Configurarea fisierului de logging
logging.basicConfig(filename='error_log.txt', level=logging.ERROR)


class MemoryFileManager:
    MAX_LENGTH = 1024  # Dimensiunea maxima a contentului sanitizat

    def __init__(self):
        # Am initializat un sistem de fisiere in memorie folosindu-ma de libraria fs
        self.memory_filestream = fs.open_fs('mem://')

    @staticmethod
    def sanitize_path(provided_path):
        # Sanitizez si validez pathul care vine ca parametru al metodei
        sanitized_input = provided_path.strip()
        normalized_path = os.path.normpath(sanitized_input)
        if not normalized_path or ".." in normalized_path.split(os.path.sep):
            raise ValueError("Invalid path")
        return normalized_path

    @staticmethod
    def log_error(error_message):
        # Adaug un timestamp pentru a tine evidenta mai bine cand s-a produs eroarea in timpul executiei
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp} - ERROR: {error_message}"
        logging.error(log_entry)

    @staticmethod
    def sanitize_log_message(message):
        # Sanitizez mesajul de eroare
        sanitized_message = message.replace("\n", " ").replace("\r", "")
        if not isinstance(sanitized_message, str):
            sanitized_message = str(sanitized_message)
        sanitized_message = ''.join(char for char in sanitized_message if char.isprintable())
        sanitized_message = sanitized_message[:MemoryFileManager.MAX_LENGTH]
        return sanitized_message

    @staticmethod
    def sanitize_file_content(content):
        # Sanitize content based on its type (str or bytes)
        if isinstance(content, bytes):
            sanitized_content = content
        else:
            # If it's a string, sanitize it
            sanitized_content = content.replace("\n", " ")

        # Trim content to the maximum length
        sanitized_content = sanitized_content[:MemoryFileManager.MAX_LENGTH]
        return sanitized_content

    def create_directory(self, path):
        # Creez un director in sistemul de fisiere din memorie
        try:
            sanitized_path = self.sanitize_path(path)
            self.memory_filestream.makedirs(sanitized_path)
        except (DirectoryExists, DirectoryExpected, ValueError) as exception:
            sanitized_error_message = self.sanitize_log_message(
                f"The path already exists or one of the ancestors in "
                f"the path is not a directory: {exception}"
            )
            self.log_error(sanitized_error_message)

    def create_file(self, path, content):
        # Creez un fisier in sistemul de fisiere din memorie
        try:
            sanitized_path = self.sanitize_path(path)
            sanitized_content = self.sanitize_file_content(content)

            mode = 'wb' if isinstance(sanitized_content, bytes) else 'w'

            # Log information about the file path and content
            print(f"Creating file: {sanitized_path}")
            print(f"Content: {sanitized_content}")
            print(f"Mode: {mode}")

            with self.memory_filestream.open(sanitized_path, mode) as file:
                file.write(sanitized_content)
            print(f"File created successfully.")
        except (FileExpected, FileExists, ResourceNotFound, ValueError) as exception:
            sanitized_error_message = self.sanitize_log_message(
                f"The path is not a file or file already exists or "
                f"path does not exist: {exception}"
            )
            self.log_error(sanitized_error_message)

    def read_file(self, path):
        # Citesc continutul fisierului aflat in sistemul de fisiere din memorie
        sanitized_path = self.sanitize_path(path)

        try:
            # Attempt to open the file in text mode
            with self.memory_filestream.open(sanitized_path, 'r') as text_file:
                return text_file.read()
        except UnicodeDecodeError:
            # If decoding as text raises an error, open the file in binary mode
            with self.memory_filestream.open(sanitized_path, 'rb') as binary_file:
                return binary_file.read()

    def list_directory_contents(self, path):
        # Afisez lista de directoare aflata in sistemul de fisiere din memorie
        sanitized_path = self.sanitize_path(path)
        return self.memory_filestream.listdir(sanitized_path)

    def copy_to_os(self, os_path):
        # Copiez tot sistemul de fisiere din memorie intr-o zona a sistemului de operare
        sanitized_path = self.sanitize_path(os_path)
        with fs.open_fs(sanitized_path) as os_fs:
            copy.copy_fs(self.memory_filestream, os_fs)

    def copy_from_os(self, os_path):
        # Copiez tot sistemul de fisiere dintr-o zona a sistemului de operare in memorie
        sanitized_path = self.sanitize_path(os_path)
        with fs.open_fs(sanitized_path) as os_fs:
            copy.copy_fs(os_fs, self.memory_filestream)

    def display_tree(self):
        # Afisez directory tree
        return self.memory_filestream.tree()

    def delete_file(self, path):
        # Sterg un fisier aflat in sistemul de fisiere din memorie
        sanitized_path = self.sanitize_path(path)
        try:
            self.memory_filestream.remove(sanitized_path)
            self.log_error(f"File '{sanitized_path}' deleted successfully.")
        except fs.errors.ResourceNotFound:
            self.log_error(f"File '{sanitized_path}' not found.")
        except Exception as e:
            self.log_error(str(e))

    def delete_directory(self, path):
        # Sterg un director aflat in sistemul de fisiere din memorie
        sanitized_path = self.sanitize_path(path)
        try:
            self.memory_filestream.removetree(sanitized_path)
            self.log_error(f"Directory '{sanitized_path}' deleted successfully.")
        except fs.errors.DirectoryExpected:
            self.log_error(f"'{sanitized_path}' is not a directory.")
        except fs.errors.ResourceNotFound:
            self.log_error(f"Directory '{sanitized_path}' not found.")
        except Exception as e:
            self.log_error(str(e))

    def traverse(self):
        root_path = 'mem://'
        try:
            contents = self.memory_filestream.listdir(root_path)
        except ResourceNotFound:
            self.log_error(f"Directory '{root_path}' not found.")
            return []

        result = [(root_path, contents)]

        for item in contents:
            item_path = os.path.join(root_path, item)
            if self.memory_filestream.isdir(item_path):
                # If the item is a directory, recursively traverse it
                result.extend(self.traverse_directory_recursive_helper(item_path))

        return result

    def traverse_directory_recursive_helper(self, path='mem://'):

        sanitized_path = self.sanitize_path(path)

        try:
            contents = self.memory_filestream.listdir(sanitized_path)
        except ResourceNotFound:
            self.log_error(f"Directory '{sanitized_path}' not found.")
            return []

        result = [(sanitized_path, contents)]

        for item in contents:
            item_path = os.path.join(sanitized_path, item)
            if self.memory_filestream.isdir(item_path):
                # If the item is a directory, recursively traverse it
                result.extend(self.traverse_directory_recursive_helper(item_path))

        return result

    def display_directory_tree(self, tree):
        for directory, contents in tree:
            print(f"Directory: {directory}")
            for item in contents:
                item_path = os.path.join(directory, item)
                if self.memory_filestream.isdir(item_path):
                    # If the item is a directory, recursively display its contents
                    subdirectory_contents = self.memory_filestream.listdir(item_path)
                    subdirectory_tree = [(item_path, subdirectory_contents)]
                    self.display_directory_tree(subdirectory_tree)
                else:
                    # If the item is a file, display it
                    print(f"  File: {item_path}")

    def clear_memory(self):
        self.memory_filestream = fs.open_fs('mem://')
        print("Memory cleared successfully.")