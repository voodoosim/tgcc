# core/security.py
"""보안 관련 유틸리티"""
import base64
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class ConfigEncryption:
    """설정 파일 암호화/복호화 클래스"""

    def __init__(self, key_file: Optional[Path] = None):
        """
        Args:
            key_file: 암호화 키 파일 경로
        """
        self.key_file = key_file or Path("data/.key")
        self.key_file.parent.mkdir(exist_ok=True)
        self._fernet = self._get_or_create_fernet()

    def _get_or_create_fernet(self) -> Fernet:
        """암호화 키 가져오기 또는 생성"""
        if self.key_file.exists():
            # 기존 키 로드
            with open(self.key_file, "rb") as f:
                key = f.read()
        else:
            # 새 키 생성
            key = Fernet.generate_key()
            with open(self.key_file, "wb") as f:
                f.write(key)
            # 키 파일 권한 설정 (읽기 전용)
            os.chmod(self.key_file, 0o600)

        return Fernet(key)

    def _derive_key_from_password(self, password: str, salt: bytes) -> bytes:
        """비밀번호로부터 암호화 키 유도"""
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000, backend=default_backend())
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key

    def encrypt_data(self, data: Dict[str, Any]) -> bytes:
        """데이터 암호화"""
        json_data = json.dumps(data, ensure_ascii=False)
        encrypted = self._fernet.encrypt(json_data.encode())
        return encrypted

    def decrypt_data(self, encrypted_data: bytes) -> Dict[str, Any]:
        """데이터 복호화"""
        decrypted = self._fernet.decrypt(encrypted_data)
        return json.loads(decrypted.decode())

    def encrypt_file(self, file_path: Path, output_path: Optional[Path] = None):
        """파일 암호화"""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        output_path = output_path or file_path.with_suffix(".enc")

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        encrypted = self.encrypt_data(data)

        with open(output_path, "wb") as f:
            f.write(encrypted)

    def decrypt_file(self, encrypted_path: Path) -> Dict[str, Any]:
        """파일 복호화"""
        if not encrypted_path.exists():
            raise FileNotFoundError(f"Encrypted file not found: {encrypted_path}")

        with open(encrypted_path, "rb") as f:
            encrypted_data = f.read()

        return self.decrypt_data(encrypted_data)

    def secure_delete(self, file_path: Path):
        """파일 안전 삭제 (덮어쓰기)"""
        if not file_path.exists():
            return

        file_size = file_path.stat().st_size

        with open(file_path, "ba+", buffering=0) as f:
            # 랜덤 데이터로 3번 덮어쓰기
            for _ in range(3):
                f.seek(0)
                f.write(os.urandom(file_size))

        # 파일 삭제
        file_path.unlink()


class SecureConfig:
    """암호화된 설정 관리"""

    def __init__(self, config_file: Optional[Path] = None):
        self.config_file = config_file or Path("data/config.enc")
        self.plain_config_file = Path("data/config.json")
        self.encryption = ConfigEncryption()
        self._migrate_if_needed()

    def _migrate_if_needed(self):
        """평문 설정을 암호화된 설정으로 마이그레이션"""
        if self.plain_config_file.exists() and not self.config_file.exists():
            # 평문 설정 암호화
            self.encryption.encrypt_file(self.plain_config_file, self.config_file)
            # 평문 파일 안전 삭제
            self.encryption.secure_delete(self.plain_config_file)

    def load_config(self) -> Dict[str, Any]:
        """암호화된 설정 로드"""
        if self.config_file.exists():
            return self.encryption.decrypt_file(self.config_file)
        return {"api_credentials": []}

    def save_config(self, config: Dict[str, Any]):
        """설정 암호화하여 저장"""
        encrypted = self.encryption.encrypt_data(config)
        with open(self.config_file, "wb") as f:
            f.write(encrypted)

    def add_api_credential(self, name: str, api_id: str, api_hash: str) -> bool:
        """API 자격증명 추가"""
        config = self.load_config()

        # 중복 체크
        for cred in config["api_credentials"]:
            if cred["name"] == name:
                return False

        # API ID 해시 (일부만 보이도록)
        api_id_hash = hashlib.sha256(api_id.encode()).hexdigest()[:8]

        config["api_credentials"].append(
            {"name": name, "api_id": api_id, "api_hash": api_hash, "id_hash": api_id_hash}  # 디버깅용
        )

        self.save_config(config)
        return True

    def get_api_credentials(self) -> list:
        """API 자격증명 목록 반환"""
        config = self.load_config()
        return config.get("api_credentials", [])
