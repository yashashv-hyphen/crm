from typing import TypeVar
from sqlalchemy import Select, func
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


async def paginate(session: AsyncSession, query: Select, page: int, size: int = 50):
    count_query = query.with_only_columns(func.count()).order_by(None)
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0

    offset = (page - 1) * size
    result = await session.execute(query.offset(offset).limit(size))
    items = result.scalars().all()

    return items, total
