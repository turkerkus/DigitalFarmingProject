import json
import requests


class FarmbotTokenManager:
    def __init__(self, login, farmbot_name):
        self.__raw_token = None
        self.__login = login
        self._farmbot_name = farmbot_name
        self.path_to_token_folder = "./farmbot_api/tokens/"

    def get_raw_token(self, dumps=False):
        """
        Returns the token for the farmbot.
        :param dumps:
        :return: token
        """
        if self.__raw_token is None:
            self.__raw_token = self._download_or_load_token()

        if dumps:
            return json.dumps(self.__raw_token)
        else:
            return self.__raw_token

    def get_username(self):
        if self.__raw_token is None:
            self.__raw_token = self._download_or_load_token()

        return self.__raw_token["token"]["unencoded"]["bot"]

    def get_token(self):
        if self.__raw_token is None:
            self.__raw_token = self._download_or_load_token()

        return self.__raw_token["token"]["encoded"]

    def get_host(self):
        if self.__raw_token is None:
            self.__raw_token = self._download_or_load_token()

        return self.__raw_token["token"]["unencoded"]["mqtt"]

    def set_token(self, token):
        """
        You can set the token manually.
        :param token:
        """
        if token is None:
            raise AttributeError("token cannot be None.")

        self.__raw_token = token

    def _download_or_load_token(self) -> dict:
        token = None
        try:  # try to load token from files
            token = self._load_token()
        except FileNotFoundError:  # if file not found download token from farmbot
            token = self._download_token()

            if token is None:  # if token still None something went wrong
                raise AttributeError("Token not found in file and also cannot be downloaded")
            else:  # else save the token for later
                self._save_token(token)
        finally:
            return token

    def _save_token(self, token):
        filename_token_file = self.path_to_token_folder + self._farmbot_name + ".json"
        with open(filename_token_file, 'w') as file:
            file.write(json.dumps(token))

    def _load_token(self):
        filename_token_file = self.path_to_token_folder + self._farmbot_name + ".json"
        with open(filename_token_file, 'r') as file:
            return json.load(file)

    def _download_token(self):
        server = self.__login["server"]
        email = self.__login["email"]
        password = self.__login["password"]

        headers = {'content-type': 'application/json'}
        user = {'user': {'email': email, 'password': password}}
        response = requests.post(f'{server}/api/tokens', headers=headers, json=user)
        return response.json()
