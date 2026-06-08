from typing import Dict

class DevModeManager:
    def __init__(self):
        self._dev_mode_users: Dict[str, bool] = {}

    def is_dev_mode(self, user_id: str) -> bool:
        return self._dev_mode_users.get(user_id, False)

    def toggle_dev_mode(self, user_id: str) -> bool:
        current = self.is_dev_mode(user_id)
        self._dev_mode_users[user_id] = not current
        return not current

    def get_dev_mode_prefix(self) -> str:
        return "[DEV MODE] "
