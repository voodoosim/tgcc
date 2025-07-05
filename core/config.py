import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class Config:
    """Telegram API 자격 증명 관리"""

    def __init__(self, config_file: Optional[Path] = None):
        self.config_file = config_file or Path("data/config.json")
        self._config = self._load_config()

    def _load_config(self) -> Dict[str, List[Dict[str, str]]]:
        """config.json 로드, 없으면 기본값 생성"""
        try:
            self.config_file.parent.mkdir(exist_ok=True)
            if self.config_file.exists():
                with open(self.config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            config: Dict[str, List[Dict[str, str]]] = {"api_credentials": []}
            self._save_config(config)
            return config
        except json.JSONDecodeError as e:
            logging.error("Failed to decode config file: %s", e)
            return {"api_credentials": []}
        except PermissionError as e:
            logging.error("Permission denied accessing config file: %s", e)
            return {"api_credentials": []}

    def _save_config(self, config: Optional[Dict[str, List[Dict[str, str]]]] = None) -> bool:
        """config.json 저장"""
        try:
            if config is None:
                config = self._config
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except PermissionError as e:
            logging.error("Permission denied saving config file: %s", e)
            return False

    def reload_config(self):
        """설정 파일을 다시 로드"""
        self._config = self._load_config()
        return self._config

    def get_api_credentials(self) -> List[Dict[str, str]]:
        """API 자격 증명 목록 반환"""
        # 항상 최신 데이터를 반환하도록 리로드
        self.reload_config()
        return self._config.get("api_credentials", [])

    def add_api_credential(self, name: str, api_id: str, api_hash: str) -> bool:
        """새 API 자격 증명 추가"""
        try:
            api_id_int = int(api_id)

            # 중복 체크
            for cred in self._config["api_credentials"]:
                if cred["name"] == name:
                    logging.warning("Credential name already exists: %s", name)
                    return False

            # 새 자격증명 추가
            self._config["api_credentials"].append({"name": name, "api_id": str(api_id_int), "api_hash": api_hash})

            # 저장
            success = self._save_config(self._config)
            if success:
                # 저장 후 다시 로드하여 동기화
                self.reload_config()
            return success

        except ValueError as e:
            logging.error("Invalid API ID format: %s", e)
            return False
        except PermissionError as e:
            logging.error("Permission error adding API credential: %s", e)
            return False
