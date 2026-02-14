# agents/content_discovery.py
"""
Content Discovery & Curation Agent
Monitors LinkedIn, Medium, and Facebook for high-quality AI-related content
"""

import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

from core.models import ContentItem, EngagementMetrics
from core.config import Config
from integrations.social_platforms import LinkedInAPI, MediumAPI, FacebookAPI

logger = logging.getLogger(__name__)

@dataclass
class CurationResult:
    """Result of content curation process"""
    total_found: int
    filtered_count: int
    top_candidates: List[ContentItem]
    execution_time: float

class ContentDiscoveryAgent:
    """Automated content discovery and curation agent"""
    
    def __init__(self, config: Config):
        self.config = config
        self.linkedin_api = LinkedInAPI(config.linkedin_credentials)
        self.medium_api = MediumAPI(config.medium_credentials)
        self.facebook_api = FacebookAPI(config.facebook_credentials)
        
        self.ai_topics = [
            "artificial intelligence", "machine learning", "deep learning",
            "neural networks", "AI automation", "generative AI", "ChatGPT",
            "AI tools", "AI productivity", "AI business", "AI future"
        ]
        
        self.relevance_threshold = 80  # Minimum relevance score
        self.target_daily_posts = 10
        
    async def discover_content(self) -> List[ContentItem]:
        """
        Main discovery method - finds and curates content from all platforms
        Target: Complete within 5 minutes, find 10+ posts, filter by relevance >80%
        """
        start_time = datetime.now()
        logger.info("Starting content discovery process")
        
        try:
            # Parallel content discovery from all platforms
            tasks = [
                self._discover_linkedin_content(),
                self._discover_medium_content(),
                self._discover_facebook_content()
            ]
            
            platform_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Combine and process results
            all_content = []
            for result in platform_results:
                if isinstance(result, Exception):
                    logger.warning(f"Platform discovery failed: {result}")
                    continue
                all_content.extend(result)
            
            # Score and filter content
            scored_content = await self._score_content_relevance(all_content)
            filtered_content = [
                item for item in scored_content 
                if item.relevance_score >= self.relevance_threshold
            ]
            
            # Sort by engagement and relevance
            top_candidates = sorted(
                filtered_content,
                key=lambda x: (x.relevance_score * 0.6 + x.engagement_metrics.total_score * 0.4),
                reverse=True
            )[:3]  # Top 3 candidates for client review
            
            execution_time = (datetime.now() - start_time).total_seconds() / 60
            
            logger.info(
                f"Discovery completed in {execution_time:.2f} minutes. "
                f"Found {len(all_content)} posts, filtered to {len(filtered_content)}, "
                f"presenting top {len(top_candidates)} candidates"
            )
            
            # Validate acceptance criteria
            if len(all_content) < self.target_daily_posts:
                logger.warning(f"Only found {len(all_content)} posts, target was {self.target_daily_posts}")
            
            if execution_time > 5:
                logger.warning(f"Discovery took {execution_time:.2f} minutes, target was 5 minutes")
            
            return top_candidates
            
        except Exception as e:
            logger.error(f"Content discovery failed: {str(e)}")
            raise
    
    async def _discover_linkedin_content(self) -> List[ContentItem]:
        """Discover content from LinkedIn"""
        try:
            posts = []
            for topic in self.ai_topics:
                topic_posts = await self.linkedin_api.search_posts(
                    query=topic,
                    time_range=timedelta(days=1),
                    min_engagement=100
                )
                posts.extend(topic_posts)
            
            return await self._convert_to_content_items(posts, "linkedin")
            
        except Exception as e:
            logger.error(f"LinkedIn discovery failed: {str(e)}")
            return []
    
    async def _discover_medium_content(self) -> List[ContentItem]:
        """Discover content from Medium"""
        try:
            articles = []
            for topic in self.ai_topics:
                topic_articles = await self.medium_api.search_articles(
                    tag=topic,
                    published_since=datetime.now() - timedelta(days=2),
                    min_claps=50
                )
                articles.extend(topic_articles)
            
            return await self._convert_to_content_items(articles, "medium")
            
        except Exception as e:
            logger.error(f"Medium discovery failed: {str(e)}")
            return []
    
    async def _discover_facebook_content(self) -> List[ContentItem]:
        """Discover content from Facebook"""
        try:
            posts = []
            for topic in self.ai_topics:
                topic_posts = await self.facebook_api.search_public_posts(
                    query=topic,
                    time_range=timedelta(days=1),
                    min_engagement=50
                )
                posts.extend(topic_posts)
            
            return await self._convert_to_content_items(posts, "facebook")
            
        except Exception as e:
            logger.error(f"Facebook discovery failed: {str(e)}")
            return []
    
    async def _convert_to_content_items(self, raw_posts: List[Dict], platform: str) -> List[ContentItem]:
        """Convert platform-specific posts to ContentItem objects"""
        content_items = []
        
        for post in raw_posts:
            try:
                engagement = EngagementMetrics(
                    likes=post.get('likes', 0),
                    shares=post.get('shares', 0),
                    comments=post.get('comments', 0),
                    views=post.get('views', 0)
                )
                
                content_item = ContentItem(
                    id=f"{platform}_{post['id']}",
                    title=post.get('title', '')[:100],
                    content=post.get('content', ''),
                    author=post.get('author', ''),
                    platform=platform,
                    url=post.get('url', ''),
                    published_date=post.get('published_date', datetime.now()),
                    engagement_metrics=engagement,
                    relevance_score=0  # Will be calculated separately
                )
                
                content_items.append(content_item)
                
            except Exception as e:
                logger.warning(f"Failed to convert post {post.get('id', 'unknown')}: {str(e)}")
                continue
        
        return content_items
    
    async def _score_content_relevance(self, content_items: List[ContentItem]) -> List[ContentItem]:
        """Score content relevance using AI analysis"""
        from integrations.openai_client import OpenAIClient
        
        openai_client = OpenAIClient(self.config.openai_api_key)
        
        for item in content_items:
            try:
                # Use AI to score relevance to AI topics and content quality
                prompt = f"""
                Rate this content for relevance to AI/technology topics and overall quality on a scale of 0-100.
                Consider: topic relevance, content depth, engagement potential, and educational value.
                
                Title: {item.title}
                Content: {item.content[:500]}...
                
                Respond with just a number (0-100):
                """
                
                response = await openai_client.complete(prompt, max_tokens=10)
                try:
                    score = int(response.strip())
                    item.relevance_score = min(100, max(0, score))
                except ValueError:
                    item.relevance_score = 50  # Default score if parsing fails
                    
            except Exception as e:
                logger.warning(f"Failed to score content {item.id}: {str(e)}")
                item.relevance_score = 50  # Default score
        
        return content_items