import asyncio
import json
import os

import indy.wallet as indy_wallet

from tpm_controller import TPMController
from utils import json_to_dict


class IndyAgent(object):


    def __init__(self, config) -> None:
        self._config = config
        self._tpm_controller = None
        self._wallet_handle = None

    def _controller_from_config(self, config):
        
        json_policy = json_to_dict(config["policy_path"])
        # Convert json policy to string
        json_policy = json.dumps(json_policy)

        return TPMController(json_policy, config["policy_path_tss"],
                               config["secret_path_tss"],
                               config["aik_path_tss"],
                               config["aik_attributes"],
                               config["fapi"]["profile_name"], 
                               config["fapi"]["profile_dir"],
                               config["fapi"]["user_dir"], 
                               config["fapi"]["system_dir"], 
                               config["fapi"]["log_dir"])
    
    async def setup(self, secret=None):
        # Run only once
        # TODO: add did
        # TODO: add ak

        if not secret:
            key_config = {
                "seed": "secret seed"
            }

            key_config = json.dumps(key_config)

            secret = await indy_wallet.generate_wallet_key(key_config)

        self._tpm_controller = self._controller_from_config(self._config["tss"])

        self._tpm_controller.setup(secret)

        wallet_config = json.dumps(config["indy"]["wallet"])

        wallet_credentials = {
            "key": secret
        }

        await indy_wallet.create_wallet(wallet_config, wallet_credentials)

        # Try to open the wallet
        self._wallet_handle = await indy_wallet.open_wallet(wallet_config, wallet_credentials)

        await indy_wallet.close_wallet(self._wallet_handle)

        await self.close()

    async def start(self) -> bool:

        self._tpm_controller = self._controller_from_config(config["tss"])

        if not self._tpm_controller:
            print("TPM controller not created.")
            return False
        
        print("TPM Controller created")

        secret = self._tpm_controller.unseal()

        if not secret:
            print("Could not unseal wallet secret")
            return False
        
        wallet_config = json.dumps(config["indy"]["wallet"])

        wallet_credentials = {
            "key": secret
        }

        wallet_credentials = json.dumps(wallet_credentials)

        self._wallet_handle = await indy_wallet.open_wallet(wallet_config, wallet_credentials)

        if not self._wallet_handle:
            print("Could not open wallet")
            return False
        
        print("Wallet opened")

        return True
    
    async def close(self) -> None:

        if self._wallet_handle:
            await indy_wallet.close_wallet(self._wallet_handle)
            print("Wallet closed")

        if self._tpm_controller:
            self._tpm_controller.close()
            print("TPM Controller closed")
    
        
if __name__ == "__main__":

    config = json_to_dict("../config.json")
    loop = asyncio.get_event_loop()

    indy_agent = IndyAgent(config)

    loop.run_until_complete(indy_agent.start())

    loop.run_until_complete(indy_agent.close())
