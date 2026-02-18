# tests/test_models.py
"""
Unit tests for database models
"""
import pytest
from datetime import datetime
from models.user import User
from models.portfolio import Portfolio, Position
from models.trade import Trade, TradeType, TradeStatus, OrderType

class TestUserModel:
    """Test User model functionality"""
    
    def test_user_creation(self):
        """Test user instance creation"""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password",
            first_name="Test",
            last_name="User"
        )
        
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.first_name == "Test"
        assert user.last_name == "User"
        assert user.is_active == True
        assert user.is_verified == False
        assert user.is_admin == False
    
    def test_password_hashing(self):
        """Test password hashing and verification"""
        password = "testpass123"
        hashed = User.hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 20
        
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password=hashed,
            first_name="Test",
            last_name="User"
        )
        
        assert user.verify_password(password) == True
        assert user.verify_password("wrongpass") == False
    
    def test_user_defaults(self):
        """Test user default values"""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hash",
            first_name="Test",
            last_name="User"
        )
        
        assert user.max_position_size == 0.05
        assert user.max_daily_loss == 0.02
        assert user.can_trade_stocks == False
        assert user.can_trade_crypto == False

class TestPortfolioModel:
    """Test Portfolio model functionality"""
    
    def test_portfolio_creation(self):
        """Test portfolio instance creation"""
        portfolio = Portfolio(
            user_id=1,
            name="Test Portfolio",
            description="A test portfolio",
            cash_balance=10000.0
        )
        
        assert portfolio.user_id == 1
        assert portfolio.name == "Test Portfolio"
        assert portfolio.cash_balance == 10000.0
        assert portfolio.total_value == 0.0
        assert portfolio.is_active == True
        assert portfolio.auto_trading_enabled == False
    
    def test_portfolio_metrics_defaults(self):
        """Test portfolio metrics default values"""
        portfolio = Portfolio(
            user_id=1,
            name="Test Portfolio"
        )
        
        assert portfolio.beta == 1.0
        assert portfolio.sharpe_ratio == 0.0
        assert portfolio.max_drawdown == 0.0
        assert portfolio.volatility == 0.0

class TestPositionModel:
    """Test Position model functionality"""
    
    def test_position_creation(self):
        """Test position instance creation"""
        position = Position(
            portfolio_id=1,
            symbol="AAPL",
            asset_type="stock",
            quantity=10.0,
            average_price=150.0
        )
        
        assert position.portfolio_id == 1
        assert position.symbol == "AAPL"
        assert position.asset_type == "stock"
        assert position.quantity == 10.0
        assert position.average_price == 150.0
        assert position.current_price == 0.0
        assert position.unrealized_pnl == 0.0

class TestTradeModel:
    """Test Trade model functionality"""
    
    def test_trade_creation(self):
        """Test trade instance creation"""
        trade = Trade(
            user_id=1,
            portfolio_id=1,
            symbol="AAPL",
            asset_type="stock",
            trade_type=TradeType.BUY,
            order_type=OrderType.MARKET,
            quantity=10.0
        )
        
        assert trade.user_id == 1
        assert trade.portfolio_id == 1
        assert trade.symbol == "AAPL"
        assert trade.trade_type == TradeType.BUY
        assert trade.order_type == OrderType.MARKET
        assert trade.quantity == 10.0
        assert trade.status == TradeStatus.PENDING
    
    def test_trade_enums(self):
        """Test trade enum values"""
        assert TradeType.BUY == "buy"
        assert TradeType.SELL == "sell"
        
        assert TradeStatus.PENDING == "pending"
        assert TradeStatus.FILLED == "filled"
        assert TradeStatus.CANCELLED == "cancelled"
        
        assert OrderType.MARKET == "market"
        assert OrderType.LIMIT == "limit"