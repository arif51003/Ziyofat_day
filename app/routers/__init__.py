from .auth import router as login_router
from .waiter import router as waiter_router
from .user import router as user_router
from .cashier import router as cashier_router
from .kitchen import router as kitchen_router

__all__ = [ 
           login_router, 
           waiter_router, 
           user_router,
           cashier_router,
           kitchen_router]
