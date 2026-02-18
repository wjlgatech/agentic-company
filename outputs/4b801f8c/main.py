# main.py
"""
AI Native Trading Company Platform - Main Application Entry Point
"""
import asyncio
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from api.routes import auth, trading, portfolio, analytics, admin
from core.config import settings
from core.database import init_db
from services.market_data_service import MarketDataService
from services.trading_engine import TradingEngine
from services.risk_manager import RiskManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("Starting AI Trading Platform...")
    await init_db()
    
    # Initialize core services
    market_data_service = MarketDataService()
    trading_engine = TradingEngine()
    risk_manager = RiskManager()
    
    # Start background services
    asyncio.create_task(market_data_service.start())
    asyncio.create_task(trading_engine.start())
    asyncio.create_task(risk_manager.start_monitoring())
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Trading Platform...")
    await market_data_service.stop()
    await trading_engine.stop()
    await risk_manager.stop()

app = FastAPI(
    title="AI Native Trading Platform",
    description="Advanced AI-powered trading platform for stocks and cryptocurrencies",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(trading.router, prefix="/api/v1/trading", tags=["trading"])
app.include_router(portfolio.router, prefix="/api/v1/portfolio", tags=["portfolio"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )