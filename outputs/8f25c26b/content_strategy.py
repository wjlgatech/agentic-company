# content_strategy.py
from typing import Dict, List
from dataclasses import dataclass
from datetime import datetime, timedelta
import json

@dataclass
class ContentPost:
    platform: str
    content: str
    media_type: str
    posting_time: datetime
    hashtags: List[str]
    engagement_hooks: List[str]
    cta: str
    community_variant: str

class ContentStrategy:
    """Create 14-day content calendar with viral-optimized posts."""
    
    def __init__(self):
        self.content_calendar: List[ContentPost] = []
        self.demo_scenarios: List[Dict] = []
        
    def create_content_calendar(self) -> List[ContentPost]:
        """Generate 14-day content calendar with daily posts."""
        base_date = datetime.now()
        
        content_templates = [
            {
                "day": 1,
                "platform": "Twitter",
                "content": "🚀 What if you could start a company in 10 minutes? Not just an idea - a REAL company with AI agents handling everything. Thread 🧵",
                "media_type": "text_thread",
                "hashtags": ["#AIAgents", "#OpenClaw", "#Entrepreneurship"],
                "engagement_hooks": ["What if", "Thread emoji", "Bold claim"],
                "cta": "Join the waitlist to see how →",
                "community_variant": "solopreneur"
            },
            {
                "day": 2,
                "platform": "LinkedIn",
                "content": "I just watched someone create a fully functional e-commerce business in under 10 minutes using AI agents. Here's what blew my mind:",
                "media_type": "video_demo",
                "hashtags": ["#AIAutomation", "#FutureOfWork", "#Innovation"],
                "engagement_hooks": ["Personal story", "Specific timeframe", "Curiosity gap"],
                "cta": "Want early access? Comment 'AGENTS' below",
                "community_variant": "professional"
            },
            # Would continue with 12 more days of content
        ]
        
        for template in content_templates:
            post_date = base_date + timedelta(days=template["day"] - 1)
            post = ContentPost(
                platform=template["platform"],
                content=template["content"],
                media_type=template["media_type"],
                posting_time=post_date,
                hashtags=template["hashtags"],
                engagement_hooks=template["engagement_hooks"],
                cta=template["cta"],
                community_variant=template["community_variant"]
            )
            self.content_calendar.append(post)
            
        return self.content_calendar
    
    def create_demo_scenarios(self) -> List[Dict]:
        """Script 20+ demo scenarios for different use cases."""
        scenarios = [
            {
                "title": "E-commerce Store in 10 Minutes",
                "business_type": "e-commerce",
                "duration": "10:00",
                "script": "Watch as AI agents set up product catalog, payment processing, and customer service...",
                "viral_hooks": ["10-minute timeframe", "Complete automation", "Real business"],
                "platforms": ["YouTube", "TikTok", "LinkedIn"]
            },
            {
                "title": "Consulting Agency Launch",
                "business_type": "service",
                "duration": "8:30",
                "script": "From zero to client-ready consulting business with AI handling proposals, scheduling...",
                "viral_hooks": ["Service business angle", "B2B focus", "Professional appeal"],
                "platforms": ["LinkedIn", "Twitter", "YouTube"]
            },
            {
                "title": "Content Creator Business",
                "business_type": "creator",
                "duration": "7:45",
                "script": "AI agents build content calendar, handle sponsorships, manage social media...",
                "viral_hooks": ["Creator economy", "Social media automation", "Passive income"],
                "platforms": ["TikTok", "Instagram", "YouTube"]
            },
            # Would continue with 17+ more scenarios
        ]
        
        self.demo_scenarios = scenarios
        return scenarios
    
    def get_platform_variants(self, base_content: str, platform: str) -> str:
        """Generate platform-specific content variants."""
        variants = {
            "Twitter": f"{base_content[:250]}... 🧵",
            "LinkedIn": f"💼 {base_content}\n\nWhat are your thoughts?",
            "TikTok": f"🎬 {base_content} #fyp #entrepreneur",
            "Reddit": f"Discussion: {base_content}\n\nWould love to hear your experiences!"
        }
        
        return variants.get(platform, base_content)