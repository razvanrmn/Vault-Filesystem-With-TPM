import os
import subprocess
from pprint import pprint

from tpm2_pytss import *
from utils import json_to_dict
from mem_test import MemoryFileManager


class TPMController:
    def __init__(self, profile_name, profile_dir, user_dir, system_dir, log_dir) -> None:
        self._config = FAPIConfig(temp_dirs=False, profile_name=profile_name,
                                  profile_dir=profile_dir, user_dir=user_dir,
                                  system_dir=system_dir, log_dir=log_dir,
                                  ek_cert_less="yes")
        self._ctx = FAPI()
        # self._ctx.provision()
        self._memory_file_manager = MemoryFileManager()

    def get_memory_file_manager(self):
        return self._memory_file_manager

    def test_quote(self, path, pcrs, quote_type=None, qualifying_data=None):
        quote_info = self._ctx.quote(path, pcrs=pcrs, quote_type=quote_type, qualifying_data=qualifying_data)
        return quote_info

    def tpm_encrypt(self, key, thing):
        self._ctx.encrypt(key, thing)

    def close(self, do_delete=False) -> None:
        if do_delete:
            self._ctx.delete("/")

        if self._ctx:
            self._ctx.close()

        if self._config:
            self._config.close()

    def setup(self):
        key_path_encrypt_decrypt = "/P_RSA2048SHA256/HS/ed_key"
        key_path_sign = "/P_RSA2048SHA256/HS/SRK/sign_key"

        self._memory_file_manager.create_directory("main")
        self._memory_file_manager.display_tree()

        if not os.path.exists(
                "/home/razvan/Desktop/TPM/vault_file_system/fapi-config/keystore/P_RSA2048SHA256/HS/ed_key") and not os.path.exists(
            "/home/razvan/Desktop/TPM/vault_file_system/fapi-config/keystore/P_RSA2048SHA256/HS/SRK"
            "/sign_key"):
            print("Keys generated successfully")
            self._ctx.create_key(key_path_encrypt_decrypt, type_="decrypt")
            self._ctx.create_key(key_path_sign, type_="sign, restricted, 0x81000005")
        else:
            print("Existent keys")

        try:
            self._ctx.pcr_extend(23, "aaa")
            (values, _) = self._ctx.pcr_read(23)
            print("Values before reseting: \n")
            pprint(values)
            os.system("sudo tpm2_pcrreset 23")
            print("TPM PCR index 23 reset successfully.\n")
            (values, _) = self._ctx.pcr_read(23)
            pprint(values)
            print()

        except subprocess.CalledProcessError as e:
            print(f"Error resetting TPM PCR: {e}")

    def test_encrypt_decrypt(self):
        ed_key = "/P_RSA2048SHA256/HS/ed_key"
        plaintext = b"Hello World!"
        ciphertext = self._ctx.encrypt(ed_key, plaintext)
        assert isinstance(ciphertext, bytes)
        print("Encrypted Text:", ciphertext)
        decrypted = self._ctx.decrypt(ed_key, ciphertext)
        assert decrypted == plaintext
        print("Decrypted Text:", decrypted)

    def test_phase_one(self):
        self._memory_file_manager.create_file("main/init.txt", self._ctx.get_random(20))
        self._memory_file_manager.display_tree()

        nv_path = f"/nv/Owner/nv_data"
        nv_check_path = "/home/razvan/Desktop/TPM/vault_file_system/fapi-config/keystore/nv/Owner/nv_data"
        nv_size = 10
        nv_type = "counter"

        if not os.path.exists(nv_check_path):
            self._ctx.create_nv(nv_path, nv_size, nv_type)
        else:
            print(f"The path {nv_path} already exists. Skipping creation.")
            # self._ctx.nv_increment(nv_path)
            pprint(self._ctx.nv_read(nv_path))

    def test_phase_two(self):
        plaintext = self._memory_file_manager.read_file("main/init.txt")
        print("File content before encryption: ", plaintext)
        ciphertext = self._ctx.encrypt("/P_RSA2048SHA256/HS/ed_key", plaintext)
        assert isinstance(ciphertext, bytes)
        print("Encrypted Text:", ciphertext)
        decrypted = self._ctx.decrypt("/P_RSA2048SHA256/HS/ed_key", ciphertext)
        assert decrypted == plaintext
        print("Decrypted Text:", decrypted)


if __name__ == '__main__':
    config = json_to_dict("../config.json")
    controller = TPMController(
        config["fapi"]["profile_name"],
        config["fapi"]["profile_dir"],
        config["fapi"]["user_dir"],
        config["fapi"]["system_dir"],
        config["fapi"]["log_dir"]
    )

    controller.setup()
    # controller.test_encrypt_decrypt()
    controller.test_phase_one()
    controller.test_phase_two()
    # controller._memory_file_manager.create_file("test/aaa.txt", controller._ctx.get_random(20))
    # controller._memory_file_manager.display_tree()
    # content = controller._memory_file_manager.read_file("test/aaa.txt")
    # print("Content of file: ", content)
    controller.close()
