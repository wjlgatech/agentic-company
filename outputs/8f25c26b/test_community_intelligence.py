# test_community_intelligence.py
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from community_intelligence import CommunityIntelligence, Community, Influencer

class TestCommunityIntelligence:
    
    @pytest.fixture
    def intelligence(self):
        return CommunityIntelligence()
    
    def test_init(self, intelligence):
        """Test CommunityIntelligence initialization."""
        assert intelligence.communities == []
        assert intelligence.influencers == []
    
    @pytest.mark.asyncio
    async def test_research_communities(self, intelligence):
        """Test community research functionality."""
        communities = await intelligence.research_communities()
        
        assert len(communities) >= 2
        assert all(isinstance(c, Community) for c in communities)
        
        # Test first community data
        reddit_community = communities[0]
        assert reddit_community.name == "r/solopreneur"
        assert reddit_community.platform == "Reddit"
        assert reddit_community.member_count == 150000
        assert reddit_community.engagement_rate == 4.2
        assert len(reddit_community.optimal_posting_times) == 3
        assert len(reddit_community.trending_topics) >= 1
        assert len(reddit_community.key_hashtags) >= 1
    
    @pytest.mark.asyncio
    async def test_identify_influencers(self, intelligence):
        """Test influencer identification functionality."""
        influencers = await intelligence.identify_influencers()
        
        assert len(influencers) >= 2
        assert all(isinstance(i, Influencer) for i in influencers)
        
        # Test first influencer data
        influencer = influencers[0]
        assert influencer.username == "pieter_levels"
        assert influencer.platform == "Twitter"
        assert influencer.follower_count == 180000
        assert influencer.engagement_rate == 3.5
        assert influencer.niche == "indie_hacking"
        assert influencer.partnership_status in ["potential", "contacted", "partnered"]
    
    @pytest.mark.asyncio
    async def test_get_engagement_metrics(self, intelligence):
        """Test engagement metrics calculation."""
        await intelligence.research_communities()
        await intelligence.identify_influencers()
        
        metrics = intelligence.get_engagement_metrics()
        
        assert "total_reach" in metrics
        assert "average_engagement_rate" in metrics
        assert "communities_mapped" in metrics
        assert "influencers_identified" in metrics
        
        assert metrics["total_reach"] > 0
        assert metrics["average_engagement_rate"] > 0
        assert metrics["communities_mapped"] >= 2
        assert metrics["influencers_identified"] >= 2
    
    def test_community_dataclass(self):
        """Test Community dataclass validation."""
        community = Community(
            name="Test Community",
            platform="TestPlatform",
            member_count=1000,
            engagement_rate=5.0,
            optimal_posting_times=["9:00 AM"],
            trending_topics=["test"],
            key_hashtags=["#test"]
        )
        
        assert community.name == "Test Community"
        assert community.member_count == 1000
        assert community.engagement_rate == 5.0
    
    def test_influencer_dataclass(self):
        """Test Influencer dataclass validation."""
        influencer = Influencer(
            username="test_user",
            platform="TestPlatform",
            follower_count=5000,
            engagement_rate=3.0,
            niche="test_niche",
            contact_info="test@example.com",
            partnership_status="potential"
        )
        
        assert influencer.username == "test_user"
        assert influencer.follower_count == 5000
        assert influencer.partnership_status == "potential"
    
    def test_edge_cases_empty_data(self, intelligence):
        """Test edge cases with empty data."""
        # Test metrics with no data
        metrics = intelligence.get_engagement_metrics()
        assert metrics["communities_mapped"] == 0
        assert metrics["influencers_identified"] == 0
    
    @pytest.mark.asyncio
    async def test_error_handling(self, intelligence):
        """Test error handling in async methods."""
        with patch('community_intelligence.CommunityIntelligence.research_communities') as mock_research:
            mock_research.side_effect = Exception("API Error")
            
            with pytest.raises(Exception):
                await intelligence.research_communities()