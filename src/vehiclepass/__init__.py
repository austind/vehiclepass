import httpx
from dotenv import load_dotenv
import os
from vehiclepass import constants, errors
import logging
load_dotenv()

FORDPASS_USERNAME = os.getenv("FORDPASS_USERNAME", "")
FORDPASS_PASSWORD = os.getenv("FORDPASS_PASSWORD", "")
FORDPASS_VIN = os.getenv("FORDPASS_VIN", "")

logger = logging.getLogger(__name__)

class VehiclePass:
    def __init__(self, username: str = FORDPASS_USERNAME, password: str = FORDPASS_PASSWORD, vin: str = FORDPASS_VIN):
        if not username or not password:
            raise ValueError("FordPass username (email address) and password are required")
        self.username = username
        self.password = password
        self.vin = vin
        self.fordpass_token = None
        self.autonomic_token = None
        self.session = httpx.Client()

    def login(self):
        self._get_fordpass_token()
        self._get_autonomic_token()
        self.session.headers.update({
            'User-Agent': constants.FORDPASS_USER_AGENT,
            'Authorization': f'Bearer {self.autonomic_token}',
            'Accept': '*/*',
            'Accept-Language': 'en-US',
            'Accept-Encoding': 'gzip, deflate, br',
            'Content-Type': 'application/json',
            'Application-Id': constants.FORDPASS_APPLICATION_ID,
        })

    def _get_fordpass_token(self) -> None:
        headers = {
            'Accept': '*/*',
            'Accept-Language': 'en-US',
            'Accept-Encoding': 'gzip, deflate, br',
            'User-Agent': constants.LOGIN_USER_AGENT,
        }
        data = {
            'username': self.username,
            'password': self.password,
        }
        response = self.session.post('https://us-central1-ford-connected-car.cloudfunctions.net/api/auth', headers=headers, data=data)
        response.raise_for_status()
        self.fordpass_token = response.json()['access_token']
        logger.info(f"Obtained FordPass token")

    def _get_autonomic_token(self) -> None:
        url = 'https://accounts.autonomic.ai/v1/auth/oidc/token'
        headers = {
            'User-Agent': constants.LOGIN_USER_AGENT,
        }
        data = {
            'subject_token': self.fordpass_token,
            'subject_issuer': 'fordpass',
            'client_id': 'fordpass-prod',
            'grant_type': 'urn:ietf:params:oauth:grant-type:token-exchange',
            "subject_token_type": "urn:ietf:params:oauth:token-type:jwt",
        }
        response = self.session.post(url, headers=headers, data=data)
        response.raise_for_status()
        self.autonomic_token = response.json()['access_token']
        logger.info(f"Obtained Autonomic token")

    def status(self) -> dict:
        url = f"https://api.autonomic.ai/v1beta/telemetry/sources/fordpass/vehicles/{self.vin}"
        response = self.session.get(url)
        logger.debug(f"Received status request response: {response.status_code}")
        response.raise_for_status()
        return response.json()

    def _send_command(self, command: str) -> dict:
        url = f"https://api.autonomic.ai/v1beta/command/vehicles/{self.vin}/commands"
        json = {
            "type": command,
            "wakeUp": True,
        }
        response = self.session.post(url, json=json)
        response.raise_for_status()
        return response.json()

    def lock(self) -> None:
        self._send_command('lock')

    def unlock(self) -> None:
        self._send_command('unLock')
        
    def is_locked(self) -> bool:
        try:
            status = self.status()
            if not isinstance(status, dict) or 'metrics' not in status:
                raise errors.VehiclePassStatusError("Invalid status response format")
            
            door_lock_status = status['metrics'].get('doorLockStatus')
            if not door_lock_status:
                raise errors.VehiclePassStatusError("No door lock status found in metrics")
                
            all_doors_status = next((x for x in door_lock_status if x.get('vehicleDoor') == 'ALL_DOORS'), None)
            if not all_doors_status or 'value' not in all_doors_status:
                raise errors.VehiclePassStatusError("Door lock status not found in status response")
                
            return all_doors_status['value'] == 'LOCKED'
            
        except Exception as e:
            if isinstance(e, errors.VehiclePassStatusError):
                raise
            raise errors.VehiclePassStatusError(f"Error checking lock status: {str(e)}")
    
    def is_unlocked(self) -> bool:
        return not self.is_locked()
