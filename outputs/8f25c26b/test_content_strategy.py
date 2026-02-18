# test_content_strategy.py
import pytest
from datetime import datetime, timedelta
from content_strategy import ContentStrategy, ContentPost

class TestContentStrategy:
    
    @pytest.fixture
    def strategy(self):
        return ContentStrategy()
    
    def test_init(self, strategy):
        """Test ContentStrategy initialization."""
        assert strategy.content_calendar == []
        assert strategy.demo_scenarios == []
    
    def test_create_content_calendar(self, strategy):
        """Test content calendar creation."""
        calendar = strategy.create_content_calendar()
        
        assert len(calendar) >= 2  # At least 2 days of content
        assert all(isinstance(post, ContentPost) for post in calendar)
        
        # Test first post
        first_post = calendar[0]
        assert first_post.platform in ["Twitter", "LinkedIn", "TikTok", "Reddit"]
        assert len(first_post.content) > 0
        assert len(first_post.hashtags) >= 1
        assert len(first_post.engagement_hooks) >= 1
        assert len(first_post.cta) > 0
        assert isinstance(first_post.posting_time, datetime)
    
    def test_create_demo_scenarios(self, strategy):
        """Test demo scenarios creation."""
        scenarios = strategy.create_demo_scenarios()
        
        assert len(scenarios) >= 3
        assert all(isinstance(scenario, dict) for scenario in scenarios)
        
        # Test first scenario
        first_scenario = scenarios[0]
        required_keys = ["title", "business_type", "duration", "script", "viral_hooks", "platforms"]
        for key in required_keys:
            assert key in first_scenario
        
        assert first_scenario["title"] == "E-commerce Store in 10 Minutes"
        assert first_scenario["business_type"] == "e-commerce"
        assert len(first_scenario["viral_hooks"]) >= 1
        assert len(first_scenario["platforms"]) >= 1
    
    def test_get_platform_variants(self, strategy):
        """Test platform-specific content variants."""
        base_content = "This is a test content for platform variants"
        
        twitter_variant = strategy.get_platform_variants(base_content, "Twitter")
        linkedin_variant = strategy.get_platform_variants(base_content, "LinkedIn")
        tiktok_variant = strategy.get_platform_variants(base_content, "TikTok")
        reddit_variant = strategy.get_platform_variants(base_content, "Reddit")
        
        assert "🧵" in twitter_variant
        assert "💼" in linkedin_variant
        assert "#fyp" in tiktok_variant
        assert "Discussion:" in reddit_variant
        
        # Test unknown platform
        unknown_variant = strategy.get_platform_variants(base_content, "UnknownPlatform")
        assert unknown_variant == base_content
    
    def test_content_post_dataclass(self):
        """Test ContentPost dataclass validation."""
        post_time = datetime.now()
        post = ContentPost(
            platform="Twitter",
            content="Test content",
            media_type="text",
            posting_time=post_time,
            hashtags=["#test"],
            engagement_hooks=["hook1"],
            cta="Click here",
            community_variant="test"
        )
        
        assert post.platform == "Twitter"
        assert post.content == "Test content"
        assert post.posting_time == post_time
        assert len(post.hashtags) == 1
    
    def test_content_calendar_chronological_order(self, strategy):
        """Test that content calendar is in chronological order."""
        calendar = strategy.create_content_calendar()
        
        if len(calendar) > 1:
            for i in range(1, len(calendar)):
                assert calendar[i].posting_time >= calendar[i-1].posting_time
    
    def test_demo_scenarios_variety(self, strategy):
        """Test that demo scenarios cover different business types."""
        scenarios = strategy.create_demo_scenarios()
        business_types = [scenario["business_type"] for scenario in scenarios]
        
        # Should have variety in business types
        unique_types = set(business_types)
        assert len(unique_types) >= 2
        
        # Should include key business types
        expected_types = ["e-commerce", "service", "creator"]
        for expected_type in expected_types:
            assert expected_type in business_types
    
    def test_edge_cases_long_content(self, strategy):
        """Test edge cases with long content."""
        long_content = "A" * 500  # Very long content
        twitter_variant = strategy.get_platform_variants(long_content, "Twitter")
        
        # Twitter variant should be truncated
        assert len(twitter_variant) < len(long_content)
        assert "🧵" in twitter_variant
    
    def test_content_hooks_effectiveness(self, strategy):
        """Test that content has effective engagement hooks."""
        calendar = strategy.create_content_calendar()
        
        for post in calendar:
            # Each post should have engagement hooks
            assert len(post.engagement_hooks) > 0
            
            # Content should contain some hook elements
            content_lower = post.content.lower()
            hook_indicators = ["what if", "here's", "watch", "🚀", "💼", "thread", "🧵"]
            has_hook = any(indicator in content_lower for indicator in hook_indicators)
            assert has_hook, f"Post missing engagement hooks: {post.content[:50]}..."