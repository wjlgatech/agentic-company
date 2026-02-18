# tests/conftest.py
"""
Test configuration and fixtures
"""
import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from httpx import AsyncClient
from fastapi.testclient import TestClient

from main import app
from core.database import Base, get_db
from models.user import User
from models.portfolio import Portfolio, Position
from models.trade import Trade, TradeType, TradeStatus, OrderType

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
    echo=False
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestSessionLocal() as session:
        yield session
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client with database dependency override"""
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    app.dependency_overrides.clear()

@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user"""
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=User.hash_password("testpass123"),
        first_name="Test",
        last_name="User",
        is_active=True,
        is_verified=True,
        can_trade_stocks=True,
        can_trade_crypto=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest.fixture
async def test_portfolio(db_session: AsyncSession, test_user: User) -> Portfolio:
    """Create a test portfolio"""
    portfolio = Portfolio(
        user_id=test_user.id,
        name="Test Portfolio",
        description="Test portfolio for unit tests",
        cash_balance=10000.0,
        is_active=True
    )
    db_session.add(portfolio)
    await db_session.commit()
    await db_session.refresh(portfolio)
    return portfolio

@pytest.fixture
async def test_position(db_session: AsyncSession, test_portfolio: Portfolio) -> Position:
    """Create a test position"""
    position = Position(
        portfolio_id=test_portfolio.id,
        symbol="AAPL",
        asset_type="stock",
        quantity=10.0,
        average_price=150.0,
        current_price=155.0,
        market_value=1550.0,
        unrealized_pnl=50.0,
        unrealized_pnl_pct=3.33
    )
    db_session.add(position)
    await db_session.commit()
    await db_session.refresh(position)
    return position