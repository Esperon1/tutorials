import requests
import uuid
import time
import logging
from odoo.exceptions import UserError

BASE_URL = "https://rksv.fiskaly.com/api/v1"


class FiskalyAPI:
    def __init__(self, api_key, api_secret, fon_participant_id, fon_user_id, fon_user_pin, legal_entity_id):
        self.api_key = api_key  # Fiskaly stuff > API Key, Api Secret
        self.api_secret = api_secret  # Uniquely generated secret for the API Key right after establishing api key.
        self.fon_participant_id = fon_participant_id  # FinanzOnline stuff >
        self.fon_user_id = fon_user_id  # ...
        self.fon_user_pin = fon_user_pin  # ...
        self.access_token = None
        self.legal_entity_id = legal_entity_id  # vat_id, taxID, gln
        self.scu_id = str(uuid.uuid4())  # UUIDv4 required for SCU creation.
        self.cash_register_id = str(uuid.uuid4())  # UUIDv4 required for Cash Register creation.
        self.receipt_id = str(uuid.uuid4())  # UUIDv4 required for Receipt creation.

    def _authenticate(self, url, payload):
        """Helper method to authenticate with a given URL and payload."""
        try:
            response = requests.post(url=url, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            print(f'HTTP errror occured: {e}')
            raise
        except Exception as err:
            print(f'Other error occured {err}')
            raise

    def _make_request(self, method, url, headers=None, json=None, params=None):
        """Helper method to make an HTTP request and handle responses."""
        response = requests.request(method=method, url=url, headers=headers, json=json, params=params)
        if response.status_code in (200, 201):
            return response.json()
        else:
            raise UserError(f"Request failed: {response.text}")

    # <Authentication methods>
    def l10n_at_authenticate_fiskaly(self):
        url = f"{BASE_URL}/auth"
        payload = {
            "api_key": self.api_key,
            "api_secret": self.api_secret
        }
        retry_count = 3
        for attempt in range(retry_count):
            try:
                response_data = self._make_request("POST", url, json=payload)
                self.access_token = response_data["access_token"]
                print("Authenticated successfully.")
                return True
            except requests.exceptions.HTTPError as http_err:
                if http_err.response.status_code in [500, 502, 503, 504]:
                    print(f"Server error during authentication, attempt {attempt + 1}/{retry_count}")
                    time.sleep(5)
                else:
                    print(f"HTTP error during authentication: {http_err}")
                    break
            except Exception as e:
                raise UserError(
                    f"Error is most likely due to INTERNET CONNECTION. See the error below: \n\nError during authentication: {e}. ")
        else:
            raise UserError("Failed to authenticate after several attempts.")

    def l10n_at_authenticate_FON(self):
        """Authenticate with FON."""
        if not self.access_token:
            self.l10n_at_authenticate_fiskaly()

        url = f"{BASE_URL}/fon/auth"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        payload = {
            'fon_participant_id': self.fon_participant_id,
            'fon_user_id': self.fon_user_id,
            'fon_user_pin': self.fon_user_pin,
        }
        try:
            response_data = self._make_request("PUT", url, headers=headers, json=payload)
            if response_data.get('authentication_status') == 'AUTHENTICATED':
                print("FON authentication successful.")
                return response_data['authentication_status']
            else:
                print(f"FON authentication failed: {response_data.get('message', 'Unknown error')}")
                return response_data.get('authentication_status', 'failed')
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred during FON authentication: {http_err}")
        except requests.exceptions.ConnectionError as conn_err:
            print(f"Connection error occurred during FON authentication: {conn_err}")
        except requests.exceptions.Timeout as timeout_err:
            print(f"Timeout error occurred during FON authentication: {timeout_err}")
        except requests.exceptions.RequestException as req_err:
            print(f"An error occurred during FON authentication: {req_err}")
        except Exception as e:
            print(f"An unexpected error occurred during FON authentication: {e}")
        return 'failed'

    # </Authentication methods>

    # <SCU methods>
    def l10n_at_check_scu_state(self, scu_id):
        """Check the status of a Signature Creation Unit (SCU)."""
        if not self.access_token:
            self.l10n_at_authenticate_fiskaly()

        url = f"{BASE_URL}/signature-creation-unit/{scu_id}"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        response_data = self._make_request("GET", url, headers=headers)
        print("SCU status checked successfully.")
        return response_data

    def l10n_at_create_scu(self, scu_id):
        """Create a Signature Creation Unit (SCU) with the Fiskaly API."""
        if not self.access_token:
            self.l10n_at_authenticate_fiskaly()

        url = f"{BASE_URL}/signature-creation-unit/{scu_id}"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        payload = {
            'signature_creation_unit_id': scu_id,
            'legal_entity_id': self.legal_entity_id['legal_entity_id'],
            'metadata': {
            }
        }
        scu = self._make_request("PUT", url, headers=headers, json=payload)
        print("SCU created successfully.")
        return scu

    def l10n_at_retrieve_scu(self, scu_id):
        if not self.access_token:
            self.l10n_at_authenticate_fiskaly()

        url = f"{BASE_URL}/signature-creation-unit/{scu_id}"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        response_data = self._make_request(method='GET', url=url, headers=headers)
        print("SCU retrieved successfully.")
        return response_data

    def l10n_at_update_scu(self, scu_id):
        if not self.access_token:
            self.l10n_at_authenticate_fiskaly()

        url = f"{BASE_URL}/signature-creation-unit/{scu_id}"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        payloads = {
            'signature_creation_unit_id': scu_id,
            'state': 'INITIALIZED',
        }

        max_retries = 3
        backoff_factor = 2

        for attempt in range(max_retries):
            try:
                response_data = self._make_request(method='PATCH', url=url, headers=headers, json=payloads)
                print("SCU updated successfully.")
                return response_data
            except requests.exceptions.RequestException as req_err:
                print(f"Request error during SCU update: {req_err}")
                if attempt < max_retries - 1:
                    sleep_time = backoff_factor ** attempt
                    print(f"Retrying in {sleep_time} seconds...")
                    time.sleep(sleep_time)
                else:
                    raise

    def l10n_at_list_all_scu(self):
        if not self.access_token:
            self.l10n_at_authenticate_fiskaly()

        url = f"{BASE_URL}/signature-creation-unit"
        headers = {"Authorization": f"Bearer {self.access_token}"}

        response_data = self._make_request("GET", url, headers=headers)
        print("SCUs listed successfully.")
        return response_data

    def l10n_at_retrieve_metadata_scu(self, scu_id):
        if not self.access_token:
            self.l10n_at_authenticate_fiskaly()

        url = f"{BASE_URL}/signature-creation-unit/{scu_id}/metadata"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        response_data = self._make_request("GET", url, headers=headers)
        print("SCU metadata retrieved successfully.")
        return response_data

    def l10n_at_update_metadata_scu(self, scu_id):
        if not self.access_token:
            self.l10n_at_authenticate_fiskaly()

        url = f"{BASE_URL}/signature-creation-unit/{scu_id}/metadata"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        payloads = {
            'signature_creation_unit_id': scu_id,
        }
        response_data = self._make_request("PATCH", url, headers=headers, json=payloads)
        print("SCU metadata updated successfully.")
        return response_data

    # </SCU methods>

    # <Cash Register methods>
    def l10n_at_check_cash_register_status(self):
        if not self.access_token:
            self.l10n_at_authenticate_fiskaly()

        url = f"{BASE_URL}/cash-register/{self.cash_register_id}"
        headers = {"Authorization": f"Bearer {self.access_token}"}

        response_data = self._make_request("GET", url, headers=headers)
        print(f"Cash Register status: {response_data['state']}")
        return response_data

    def l10n_at_update_cash_register_state(self, cash_register_id, state):
        """Update the state of a Cash Register."""
        if not self.access_token:
            self.l10n_at_authenticate_fiskaly()

        url = f"{BASE_URL}/cash-register/{cash_register_id}"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        payload = {'state': state}

        response_data = self._make_request("PATCH", url, headers=headers, json=payload)
        print(f"Cash register {cash_register_id} state updated to {state}.")
        return response_data

    def l10n_at_create_cash_register(self, cash_register_id):
        if not self.access_token:
            self.l10n_at_authenticate_fiskaly()

        url = f"{BASE_URL}/cash-register/{cash_register_id}"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        payloads = {
            'cash_register_id': cash_register_id,
            'metadata': {
            }
        }
        response_data = self._make_request("PUT", url, headers=headers, json=payloads)
        print("Cash register created successfully.")
        return response_data

    def l10n_at_retrieve_cash_register(self, cash_register_id):
        if not self.access_token:
            self.l10n_at_authenticate_fiskaly()

        url = f"{BASE_URL}/cash-register/{cash_register_id}"
        headers = {"Authorization": f"Bearer {self.access_token}"}

        response_data = self._make_request("GET", url, headers=headers)
        print("Cash register retrieved successfully.")
        return response_data

    def l10n_at_register_cash_register(self):
        if not self.access_token:
            self.l10n_at_authenticate_fiskaly()

        url = f"{BASE_URL}/cash-register/{self.cash_register_id}"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        payloads = {
            'cash_register_id': self.cash_register_id,
            'state': 'REGISTERED',
        }
        response_data = self._make_request("PATCH", url, headers=headers, json=payloads)
        print("Cash register registered successfully.")
        return response_data

    def l10n_at_initialize_cash_register(self, cash_register_id):
        if not self.access_token:
            self.l10n_at_authenticate_fiskaly()

        url = f"{BASE_URL}/cash-register/{cash_register_id}"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        payloads = {
            'cash_register_id': cash_register_id,
            'state': 'INITIALIZED',
        }
        response_data = self._make_request("PATCH", url, headers=headers, json=payloads)
        print("Cash register updated successfully.")
        return response_data

    def l10n_at_list_cash_register(self):
        if not self.access_token:
            self.l10n_at_authenticate_fiskaly()

        url = f"{BASE_URL}/cash-register"
        headers = {"Authorization": f"Bearer {self.access_token}"}

        response_data = self._make_request("GET", url, headers=headers)
        print("Cash registers listed successfully.")
        return response_data

    def l10n_at_update_cash_register(self, cash_register_id, state):
        if not self.access_token:
            self.l10n_at_authenticate_fiskaly()

        url = f"{BASE_URL}/cash-register/{cash_register_id}"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        payloads = {
            'cash_register_id': cash_register_id,
            'state': state,
        }
        response_data = self._make_request("PATCH", url, headers=headers, json=payloads)
        print("Cash register updated successfully.")
        return response_data

    def l10n_at_retrieve_metadata_cash_register(self, cash_register_id):
        if not self.access_token:
            self.l10n_at_authenticate_fiskaly()

        url = f"{BASE_URL}/cash-register/{cash_register_id}/metadata"
        headers = {"Authorization": f"Bearer {self.access_token}"}

        response_data = self._make_request("GET", url, headers=headers)
        print("Cash register metadata retrieved successfully.")
        return response_data

    def l10n_at_update_metadata_cash_register(self, cash_register_id):
        if not self.access_token:
            self.l10n_at_authenticate_fiskaly()

        url = f"{BASE_URL}/cash-register/{cash_register_id}/metadata"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        payloads = {
            'cash_register_id': cash_register_id}
        response_data = self._make_request("PATCH", url, headers=headers, json=payloads)
        print("Cash register metadata updated successfully.")
        return response_data

    # </Cash Register methods>

    # < Receipt methods >

    def l10n_at_validate_receipt(self, cash_register_id, receipt_id):
        # Before we can sign a receipt, we need to validate it with the FON.
        if not self.access_token:
            self.l10n_at_authenticate_fiskaly()

        url = f"{BASE_URL}/cash-register/{cash_register_id}/receipt/{receipt_id}/validation"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        payloads = {
            'cash_register_id': cash_register_id,
            'receipt_id': receipt_id,
        }
        response_data = self._make_request("POST", url, headers=headers, json=payloads)
        print("Receipt validated successfully.")
        return response_data

    def l10n_at_sign_receipt(self, cash_register_id, receipt_id):
        if not self.access_token:
            self.l10n_at_authenticate_fiskaly()

        payloads = {
            'cash_register_id': cash_register_id,
            'receipt_id': receipt_id,
            "receipt_type": "NORMAL",
            "schema": {
                "standard_v1": {
                    "amounts_per_vat_rate": [
                        {
                            "vat_rate": "STANDARD",
                            "amount": "1.00"
                        },
                        {
                            "vat_rate": "REDUCED_1",
                            "amount": "1.00"
                        },
                        {
                            "vat_rate": "REDUCED_2",
                            "amount": "1.00"
                        },
                        {
                            "vat_rate": "SPECIAL",
                            "amount": "1.00"
                        },
                        {
                            "vat_rate": "ZERO",
                            "amount": "1.00"
                        }
                    ],
                    "line_items": [
                        {
                            "quantity": 1,
                            "text": "ARTIKELTEXT1",
                            "price_per_unit": "1.00"
                        },
                        {
                            "quantity": 1,
                            "text": "ARTIKELTEXT2",
                            "price_per_unit": "1.00"
                        },
                        {
                            "quantity": 1,
                            "text": "ARTIKELTEXT3",
                            "price_per_unit": "1.00"
                        },
                        {
                            "quantity": 1,
                            "text": "ARTIKELTEXT4",
                            "price_per_unit": "1.00"
                        },
                        {
                            "quantity": 1,
                            "text": "ARTIKELTEXT5",
                            "price_per_unit": "1.00"
                        }
                    ]
                }
            },
            "metadata": {
                "my_property_1": "ABCD",
                "my_property_2": "EFGH"
            }
        }

        url = f"{BASE_URL}/cash-register/{cash_register_id}/receipt/{receipt_id}"
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }

        response_data = self._make_request("PUT", url, headers=headers, json=payloads)
        print("Receipt signed successfully.")
        return response_data

    def l10n_at_retrieve_receipt(self, cash_register_id, receipt_id):
        if not self.access_token:
            self.l10n_at_authenticate_fiskaly()

        url = f"{BASE_URL}/cash-register/{cash_register_id}/receipt/{receipt_id}"
        headers = {"Authorization": f"Bearer {self.access_token}"}

        response_data = self._make_request("GET", url, headers=headers)
        print("Receipt retrieved successfully.")
        return response_data

    def l10n_at_list_all_receipts(self, cash_register_id):
        if not self.access_token:
            self.l10n_at_authenticate_fiskaly()

        url = f"{BASE_URL}/cash-register/{cash_register_id}/receipt"
        headers = {"Authorization": f"Bearer {self.access_token}"}

        responce_data = self._make_request("GET", url, headers=headers)
        print("All receipts listed successfully.")
        return responce_data

    def l10n_at_list_receipt_cash_register(self, cash_register_id):
        if not self.access_token:
            self.l10n_at_authenticate_fiskaly()

        url = f"{BASE_URL}/cash-register/{cash_register_id}/receipt"
        headers = {
            'Authorization': f'Bearer {self.access_token}'}

        response_data = self._make_request("GET", url, headers=headers)
        print("Receipts of cash registers listed successfully.")
        return response_data

    def l10n_at_retrieve_metadata_receipt(self, cash_register_id, receipt_id):
        if not self.access_token:
            self.l10n_at_authenticate_fiskaly()

        url = f"{BASE_URL}/cash-register/{self.cash_register_id}/receipt/{self.receipt_id}/metadata"
        headers = {"Authorization": f"Bearer {self.access_token}"}

        response_data = self._make_request("GET", url, headers=headers)
        print("Receipt metadata retrieved successfully.")
        return response_data

    def l10n_at_update_metadata_receipt(self, cash_register_id, receipt_id):
        if not self.access_token:
            self.l10n_at_authenticate_fiskaly()

        url = f"{BASE_URL}/cash-register/{cash_register_id}/receipt/{receipt_id}/metadata"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        payloads = {
            'cash_register_id': cash_register_id,
            'receipt_id': receipt_id,
        }
        response_data = self._make_request("PATCH", url, headers=headers, json=payloads)
        print("Receipt metadata updated successfully.")
        return response_data

    # </ Receipt methods >

    # <Data Exports>

    def l10n_at_export_data(self, cash_register_id, params=None):
        if not self.access_token:
            self.l10n_at_authenticate_fiskaly()

        url = f"{BASE_URL}/cash-register/{cash_register_id}/export"
        headers = {"Authorization": f"Bearer {self.access_token}"}

        response_data = self._make_request("GET", url, headers=headers, params=params)
        print("Data exported successfully.")
        return response_data

    # </Data Exports>

    # < Clean ups>
    def l10n_at_decommission_cash_register(self, cash_register_id):
        """Decommission a Cash Register."""
        if not self.access_token:
            self.l10n_at_authenticate_fiskaly()

        url = f"{BASE_URL}/cash-register/{cash_register_id}"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        payload = {'state': 'DECOMMISSIONED'}

        response_data = self._make_request("PATCH", url, headers=headers, json=payload)
        print(f"Cash register {self.cash_register_id} decommissioned successfully.")
        return response_data

    def l10n_at_decommission_scu(self, scu_id):
        if not self.access_token:
            self.l10n_at_authenticate_fiskaly()

        url = f"{BASE_URL}/signature-creation-unit/{scu_id}"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        payload = {'state': 'DECOMMISSIONED'}

        response_data = self._make_request("PATCH", url, headers=headers, json=payload)
        print(f"SCU {scu_id} decommissioned successfully.")
        return response_data

    # </ Clean ups>

    # < Outage checks >

    def l10n_at_transition_to_outage(self, cr_id):
        if not self.access_token:
            self.l10n_at_authenticate_fiskaly()

        url = f"{BASE_URL}/cash-register/{cr_id}"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        payload = {'state': 'OUTAGE'}

        response_data = self._make_request("PATCH", url, headers=headers, json=payload)
        print(f"Cash register {cr_id} transitioned to OUTAGE successfully.")
        return response_data

    def l10n_at_transition_to_initiallised(self, cr_id):
        if not self.access_token:
            self.l10n_at_authenticate_fiskaly()

        url = f"{BASE_URL}/cash-register/{cr_id}"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        payload = {'state': 'INITIALIZED'}

        response_data = self._make_request("PATCH", url, headers=headers, json=payload)
        print(f"Cash register {cr_id} transitioned to INITIALISED successfully.")
        return response_data

    def l10n_at_transition_to_defective_cash_register(self, cr_id):
        if not self.access_token:
            self.l10n_at_authenticate_fiskaly()

        url = f"{BASE_URL}/cash-register/{cr_id}"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        payload = {'state': 'DEFECTIVE'}

        response_data = self._make_request("PATCH", url, headers=headers, json=payload)
        print(f"Cash register {cr_id} transitioned to DEFECTIVE successfully.")
        return response_data

