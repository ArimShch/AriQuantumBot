from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery
from typing import Union, Dict, Any


class IsAdmin(BaseFilter):
    async def __call__(
        self, 
        event: Union[Message, CallbackQuery], 
        admin_ids: list[int], 
    ) -> Union[bool, Dict[str, Any]]:
        user_id = event.from_user.id
        # print('Admin ids', admin_ids)
        return user_id in admin_ids
    