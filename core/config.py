# core/config.py
import json
import os

from ui.constants import CONFIG_FILE, SESSIONS_DIR


class Config:
    """
    설정 파일을 관리하는 클래스.
    API 정보, 마지막 사용 라이브러리 등을 JSON 파일로 관리합니다.
    """

    def __init__(self):
        self._config_path = CONFIG_FILE
        self._config = self._load_config()

        if not os.path.exists(SESSIONS_DIR):
            os.makedirs(SESSIONS_DIR)

    def _load_config(self):
        """설정 파일(config.json)을 불러옵니다. 없으면 기본 구조를 생성합니다."""
        try:
            with open(self._config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # 파일이 없거나 내용이 잘못된 경우 기본값으로 시작
            return {"api_credentials": [], "last_used_api": None, "last_used_library": "Pyrogram"}

    def _save_config(self):
        """현재 설정을 config.json 파일에 저장합니다."""
        with open(self._config_path, "w", encoding="utf-8") as f:
            json.dump(self._config, f, indent=4, ensure_ascii=False)

    def get_api_credentials(self):
        """저장된 모든 API 자격 증명 목록을 반환합니다."""
        return self._config.get("api_credentials", [])

    def add_api_credential(self, nickname, api_id, api_hash):
        """새로운 API 자격 증명을 추가합니다."""
        credentials = self.get_api_credentials()
        # 닉네임 중복 확인
        if any(cred.get("name") == nickname for cred in credentials):
            return False

        new_cred = {"name": nickname, "api_id": api_id, "api_hash": api_hash}
        self._config["api_credentials"].append(new_cred)
        self._save_config()
        return True

    def remove_api_credential(self, nickname):
        """닉네임으로 API 자격 증명을 삭제합니다."""
        credentials = self.get_api_credentials()
        original_count = len(credentials)

        new_credentials = [cred for cred in credentials if cred.get("name") != nickname]

        if len(new_credentials) < original_count:
            self._config["api_credentials"] = new_credentials
            self._save_config()
            return True
        return False

    def get_last_used_library(self):
        """마지막으로 사용한 라이브러리 이름을 반환합니다."""
        return self._config.get("last_used_library", "Pyrogram")

    def get_last_used_api(self):
        """마지막으로 사용한 API 닉네임을 반환합니다."""
        return self._config.get("last_used_api")

    def save_last_used(self, api_nickname, library_name):
        """마지막으로 사용한 API와 라이브러리 설정을 저장합니다."""
        self._config["last_used_api"] = api_nickname
        self._config["last_used_library"] = library_name
        self._save_config()
