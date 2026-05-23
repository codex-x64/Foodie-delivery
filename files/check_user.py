from database import get_user_by_username
user = get_user_by_username('admin')
print(f'User: {user}')
print(f'is_locked: {user["is_locked"]}')
print(f'failed_attempts: {user["failed_attempts"]}')
