from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery

from sqlalchemy.ext.asyncio import AsyncSession
import logging

from ...infrastructure.database.repositories import circuit_repository


logger = logging.getLogger(__name__)


class IsCircuitOwner(BaseFilter):
    async def __call__(
            self, 
            callback: CallbackQuery, 
            session: AsyncSession, 
    ):
        try:
            circuit_id = int(callback.data.split(':')[1])
            
            is_owner = await circuit_repository.user_is_owner(
                session=session, 
                tg_id=callback.from_user.id, 
                circuit_id=circuit_id, 
            )
            # print('IsOwner -', is_owner, circuit_id)
        except Exception as e:
            logger.error('Error in filter IsCircuitOwner: %s', e)
            is_owner = False

        return {'circuit_id': circuit_id} if is_owner else False 


        
            