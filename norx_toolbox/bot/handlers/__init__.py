from typing import TYPE_CHECKING

from .auto_download import router as auto_download_router
from .convert import router as convert_router
from .crop import router as crop_router
from .download import router as download_router
from .share import router as share_router
from .shorten import router as shorten_router
from .trim import router as trim_router

if TYPE_CHECKING:
    from typing import List

    from aiogram import Router

routers: "List[Router]" = [
    download_router,
    trim_router,
    convert_router,
    crop_router,
    auto_download_router,
    share_router,
    shorten_router,
]
