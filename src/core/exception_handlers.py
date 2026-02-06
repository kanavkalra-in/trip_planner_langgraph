"""Global exception handlers for FastAPI application."""

from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from langgraph.errors import GraphInterrupt, GraphBubbleUp

from gen_ai_core_lib.config.logging_config import logger


class ExceptionHandlerRegistry:
    """Registry for global exception handlers."""
    
    @staticmethod
    async def graph_interrupt_handler(request: Request, exc: GraphInterrupt) -> JSONResponse:
        """
        Handle GraphInterrupt exceptions.
        
        These should be caught by the graph's stream() method, but if they reach here,
        something went wrong with interrupt handling. We re-raise to let it propagate
        as this indicates a bug in interrupt handling.
        
        Args:
            request: FastAPI request object
            exc: GraphInterrupt exception
            
        Returns:
            JSONResponse (though this shouldn't normally be reached)
        """
        logger.error(
            f"GraphInterrupt reached application level - this shouldn't happen. "
            f"Request: {request.method} {request.url.path}"
        )
        # Re-raise to let it propagate - this indicates a bug in interrupt handling
        raise exc
    
    @staticmethod
    async def graph_bubble_up_handler(request: Request, exc: GraphBubbleUp) -> JSONResponse:
        """
        Handle GraphBubbleUp exceptions (parent class of GraphInterrupt).
        
        These should be caught by the graph's stream() method.
        
        Args:
            request: FastAPI request object
            exc: GraphBubbleUp exception
            
        Returns:
            JSONResponse (though this shouldn't normally be reached)
        """
        logger.error(
            f"GraphBubbleUp reached application level - this shouldn't happen. "
            f"Request: {request.method} {request.url.path}"
        )
        # Re-raise to let it propagate
        raise exc
    
    @staticmethod
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        """
        Handle HTTP exceptions - return them as-is.
        
        Args:
            request: FastAPI request object
            exc: HTTPException
            
        Returns:
            JSONResponse with error details
        """
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )
    
    @staticmethod
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """
        Global exception handler for all unhandled exceptions.
        
        This catches any exception that wasn't handled by specific handlers above.
        It logs the error and returns a generic error response.
        
        Args:
            request: FastAPI request object
            exc: Exception that was raised
            
        Returns:
            JSONResponse with error details
        """
        logger.error(
            f"Unhandled exception in {request.method} {request.url.path}: {exc}",
            exc_info=True
        )
        
        # Return a generic error response
        return JSONResponse(
            status_code=500,
            content={
                "detail": "An internal server error occurred",
                "error_type": type(exc).__name__,
                "message": str(exc)
            }
        )
    
    @classmethod
    def register_handlers(cls, app):
        """
        Register all exception handlers with the FastAPI app.
        
        Args:
            app: FastAPI application instance
        """
        app.add_exception_handler(GraphInterrupt, cls.graph_interrupt_handler)
        app.add_exception_handler(GraphBubbleUp, cls.graph_bubble_up_handler)
        app.add_exception_handler(HTTPException, cls.http_exception_handler)
        app.add_exception_handler(Exception, cls.global_exception_handler)
        logger.info("Global exception handlers registered")
