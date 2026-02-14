from typing import List, Dict, Optional
import asyncio
import aiohttp
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from abc import ABC, abstractmethod

@dataclass
class ContentItem:
    """Represents a discovered content item"""
    platform: str
    url: str
    title: str
    content: str
    author: str
    engagement_score: float
    relevance_score: float
    timestamp: datetime
    summary: str

class ContentScraperInterface(ABC):
    """Interface for platform-specific content scrapers"""
    
    @abstractmethod
    async def scrape_content(self, limit: int = 50) -> List[ContentItem]:
        pass

class LinkedInScraper(ContentScraperInterface):
    """LinkedIn content scraper implementation"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.linkedin.com/v2"
    
    async def scrape_content(self, limit: int = 50) -> List[ContentItem]:
        """Scrape AI-related content from LinkedIn"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        async with aiohttp.ClientSession() as session:
            # Search for AI-related posts
            search_params = {
                "keywords": "artificial intelligence,AI engineering,machine learning",
                "count": limit
            }
            
            async with session.get(
                f"{self.base_url}/posts",
                headers=headers,
                params=search_params
            ) as response:
                data = await response.json()
                
                content_items = []
                for post in data.get("elements", []):
                    item = ContentItem(
                        platform="LinkedIn",
                        url=post.get("permalink", ""),
                        title=post.get("commentary", "")[:100],
                        content=post.get("commentary", ""),
                        author=post.get("author", {}).get("name", ""),
                        engagement_score=self._calculate_engagement(post),
                        relevance_score=0.0,  # Will be calculated later
                        timestamp=datetime.fromtimestamp(post.get("createdTime", 0) / 1000),
                        summary=""
                    )
                    content_items.append(item)
                
                return content_items
    
    def _calculate_engagement(self, post: Dict) -> float:
        """Calculate engagement score based on likes, comments, shares"""
        likes = post.get("socialDetail", {}).get("totalSocialActivityCounts", {}).get("numLikes", 0)
        comments = post.get("socialDetail", {}).get("totalSocialActivityCounts", {}).get("numComments", 0)
        shares = post.get("socialDetail", {}).get("totalSocialActivityCounts", {}).get("numShares", 0)
        
        return (likes * 1.0 + comments * 2.0 + shares * 3.0) / 100.0

class MediumScraper(ContentScraperInterface):
    """Medium content scraper implementation"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.medium.com/v1"
    
    async def scrape_content(self, limit: int = 50) -> List[ContentItem]:
        """Scrape AI-related content from Medium"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        async with aiohttp.ClientSession() as session:
            # Search for AI-related articles
            search_params = {
                "tag": "artificial-intelligence",
                "limit": limit
            }
            
            async with session.get(
                f"{self.base_url}/posts",
                headers=headers,
                params=search_params
            ) as response:
                data = await response.json()
                
                content_items = []
                for article in data.get("data", []):
                    item = ContentItem(
                        platform="Medium",
                        url=article.get("url", ""),
                        title=article.get("title", ""),
                        content=article.get("content", ""),
                        author=article.get("author", {}).get("name", ""),
                        engagement_score=self._calculate_engagement(article),
                        relevance_score=0.0,
                        timestamp=datetime.fromisoformat(article.get("publishedAt", "")),
                        summary=""
                    )
                    content_items.append(item)
                
                return content_items
    
    def _calculate_engagement(self, article: Dict) -> float:
        """Calculate engagement score for Medium article"""
        claps = article.get("virtuals", {}).get("totalClapCount", 0)
        responses = article.get("virtuals", {}).get("responsesCreatedCount", 0)
        
        return (claps * 0.1 + responses * 5.0) / 100.0

class FacebookScraper(ContentScraperInterface):
    """Facebook content scraper implementation"""
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = "https://graph.facebook.com/v18.0"
    
    async def scrape_content(self, limit: int = 50) -> List[ContentItem]:
        """Scrape AI-related content from Facebook"""
        params = {
            "access_token": self.access_token,
            "q": "artificial intelligence AI technology",
            "type": "post",
            "limit": limit
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/search",
                params=params
            ) as response:
                data = await response.json()
                
                content_items = []
                for post in data.get("data", []):
                    item = ContentItem(
                        platform="Facebook",
                        url=f"https://facebook.com/{post.get('id', '')}",
                        title=post.get("message", "")[:100],
                        content=post.get("message", ""),
                        author=post.get("from", {}).get("name", ""),
                        engagement_score=self._calculate_engagement(post),
                        relevance_score=0.0,
                        timestamp=datetime.fromisoformat(post.get("created_time", "")),
                        summary=""
                    )
                    content_items.append(item)
                
                return content_items
    
    def _calculate_engagement(self, post: Dict) -> float:
        """Calculate engagement score for Facebook post"""
        reactions = post.get("reactions", {}).get("summary", {}).get("total_count", 0)
        comments = post.get("comments", {}).get("summary", {}).get("total_count", 0)
        shares = post.get("shares", {}).get("count", 0)
        
        return (reactions * 1.0 + comments * 2.0 + shares * 3.0) / 100.0

class RelevanceScorer:
    """Scores content relevance based on AI engineering, product design, business wealth, individual empowerment"""
    
    RELEVANCE_KEYWORDS = {
        "ai_engineering": [
            "machine learning", "deep learning", "neural networks", "AI development",
            "MLOps", "model training", "algorithms", "data science", "AI architecture"
        ],
        "product_design": [
            "UX design", "product management", "user experience", "design thinking",
            "product strategy", "user research", "prototyping", "design systems"
        ],
        "business_wealth": [
            "entrepreneurship", "startup", "business growth", "revenue", "investment",
            "wealth building", "financial success", "business strategy", "scaling"
        ],
        "individual_empowerment": [
            "personal development", "career growth", "skill building", "leadership",
            "productivity", "self-improvement", "empowerment", "success mindset"
        ]
    }
    
    def score_relevance(self, content: ContentItem) -> float:
        """Calculate relevance score based on content analysis"""
        text = f"{content.title} {content.content}".lower()
        
        total_score = 0.0
        for category, keywords in self.RELEVANCE_KEYWORDS.items():
            category_score = sum(1 for keyword in keywords if keyword in text)
            total_score += category_score
        
        # Normalize score to 0-1 range
        max_possible_score = sum(len(keywords) for keywords in self.RELEVANCE_KEYWORDS.values())
        return min(total_score / max_possible_score, 1.0)

class ContentSummarizer:
    """Generates concise summaries of content items"""
    
    async def summarize(self, content: ContentItem) -> str:
        """Generate a summary of the content item"""
        # In a real implementation, this would use an AI summarization service
        # For now, we'll create a simple extractive summary
        
        sentences = content.content.split('. ')
        if len(sentences) <= 2:
            return content.content
        
        # Take first and last sentences as summary
        summary = f"{sentences[0]}. {sentences[-1]}"
        return summary[:200] + "..." if len(summary) > 200 else summary

class ContentDiscoveryAgent:
    """Main agent for content discovery and curation"""
    
    def __init__(self, linkedin_api_key: str, medium_api_key: str, facebook_access_token: str):
        self.scrapers = [
            LinkedInScraper(linkedin_api_key),
            MediumScraper(medium_api_key),
            FacebookScraper(facebook_access_token)
        ]
        self.relevance_scorer = RelevanceScorer()
        self.summarizer = ContentSummarizer()
        self.logger = logging.getLogger(__name__)
    
    async def discover_content(self, daily_limit: int = 100) -> List[ContentItem]:
        """Discover and curate content from all platforms"""
        self.logger.info(f"Starting content discovery with limit: {daily_limit}")
        
        # Distribute limit across platforms
        per_platform_limit = daily_limit // len(self.scrapers)
        
        all_content = []
        tasks = []
        
        for scraper in self.scrapers:
            task = scraper.scrape_content(per_platform_limit)
            tasks.append(task)
        
        # Execute scraping in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                self.logger.error(f"Scraping error: {result}")
                continue
            all_content.extend(result)
        
        # Score relevance and generate summaries
        for item in all_content:
            item.relevance_score = self.relevance_scorer.score_relevance(item)
            item.summary = await self.summarizer.summarize(item)
        
        # Filter and sort by combined score
        filtered_content = [item for item in all_content if item.relevance_score > 0.3]
        
        # Sort by combined relevance and engagement score
        sorted_content = sorted(
            filtered_content,
            key=lambda x: (x.relevance_score * 0.7 + x.engagement_score * 0.3),
            reverse=True
        )
        
        self.logger.info(f"Discovered {len(sorted_content)} relevant content items")
        return sorted_content[:5]  # Return top 5 candidates
    
    async def present_candidates(self, candidates: List[ContentItem]) -> Dict:
        """Present top candidates in a format ready for client review"""
        presentation = {
            "timestamp": datetime.now().isoformat(),
            "total_candidates": len(candidates),
            "candidates": []
        }
        
        for i, candidate in enumerate(candidates):
            candidate_data = {
                "rank": i + 1,
                "platform": candidate.platform,
                "title": candidate.title,
                "author": candidate.author,
                "summary": candidate.summary,
                "relevance_score": round(candidate.relevance_score, 2),
                "engagement_score": round(candidate.engagement_score, 2),
                "url": candidate.url,
                "timestamp": candidate.timestamp.isoformat()
            }
            presentation["candidates"].append(candidate_data)
        
        return presentation