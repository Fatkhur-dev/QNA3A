import aiohttp
import pyuseragents
from web3utils import *


class Qna3:
    def __init__(self, key, proxy: str = None):
        self.credit = None
        self.token = None
        self.account = Web3Utils(key=key, is_async=True)
        self.account.define_new_provider('https://opbnb.publicnode.com')
        self.proxy = proxy
        if self.proxy is not None:
            self.proxy_ip = self.proxy.split('@')[1]
        else:
            self.proxy_ip = 'No Proxy'

        headers = {
            'authority': 'api.qna3.ai',
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-US,en;q=0.9,ru-RU;q=0.8,ru;q=0.7',
            'content-type': 'application/json',
            'origin': 'https://qna3.ai',
            'sec-ch-ua-platform': '"Windows"',
            'user-agent': pyuseragents.random(),
            'x-lang': 'english',
        }
        self.session = aiohttp.ClientSession(headers=headers)

    async def get_token(self):
        try:
            msg = "AI + DYOR = Ultimate Answer to Unlock Web3 Universe"
            json_data = {
                'wallet_address': self.account.address,
                'signature': self.account.get_signed_code(msg),
            }

            params = {
                'via': 'wallet',
            }

            url = "https://api.qna3.ai/api/v2/auth/login"
            response = await self.session.post(url, json=json_data, params=params)
            response_data = await response.json()
            self.token = response_data['data']['accessToken']
            self.session.headers.update({'Authorization': f'Bearer {self.token}'})
        except Exception as ex:
            print(f"Error in get_token(): {ex}")

    async def get_info(self):
        if self.token is None:
            await self.get_token()
        url = 'https://api.qna3.ai/user/credit'
        try:
            response = await self.session.get(url)
            response_data = await response.json()
            self.credit = response_data['data']
        except Exception as ex:
            print(f"Error in get_info(): {ex}")

    async def make_transaction(self):
        contract_address = '0xB342e7D33b806544609370271A8D074313B7bc30'
        data = '0xe95a644f0000000000000000000000000000000000000000000000000000000000000001'
        gas_estimate = await self.account.w3.eth.estimate_gas({
            'to': contract_address,
            'data': data
        })
        transaction = {
            'chainId': 204,
            'to': contract_address,
            'gas': gas_estimate,
            'gasPrice': await self.account.w3.eth.gas_price,
            'nonce': await self.account.w3.eth.get_transaction_count(self.account.address),
            'data': data

        }
        try:
            signed_transaction = self.account.w3.eth.account.sign_transaction(transaction, self.account.key)
            transaction_hash = await self.account.w3.eth.send_raw_transaction(signed_transaction.rawTransaction)
            transaction_receipt = await self.account.w3.eth.wait_for_transaction_receipt(transaction_hash)
            if transaction_receipt:
                return transaction_hash.hex()
        except Exception as ex:
            print(f"Error in make_transaction(): {ex}")

    async def verify_transaction(self):
        if self.token is None:
            await self.get_token()

        tx_hash = await self.make_transaction()

        url = 'https://api.qna3.ai/api/v2/my/check-in'
        json_data = {"hash": f"{tx_hash}",
                     "via": 'opbnb'}

        response = await self.session.post(url, json=json_data)
        return await response.text()

    async def close_session(self):
        if self.session and not self.session.closed:
            await self.session.close()
