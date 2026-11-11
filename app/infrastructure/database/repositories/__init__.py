from .user_repos import UserRepository
from .base_repos import BaseRepository
from .circuit_repos import CircuitRepository
from .activity_repos import ActivityRepository
from .admin_user_repos import UserStatRepository

user_repository = UserRepository()
base_repository = BaseRepository()
circuit_repository = CircuitRepository()
activity_repository = ActivityRepository()
user_stat_repository = UserStatRepository()

__all__ = [
    "UserRepository",
    "BaseRepository",
    'CircuitRepository',
    'ActivityRepository',
    'UserStatRepository'
    "user_repository",
    "base_repository",
    'circuit_repository', 
    'activity_repository', 
]