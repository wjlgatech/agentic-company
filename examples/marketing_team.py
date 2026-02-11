"""
🚀 Agentic Marketing Team - Build in Public Campaign Automation

A multi-agent system that runs your entire marketing operation:
- Social listening & pain point discovery
- Competitor intelligence
- Content creation (text, images, videos)
- Landing page generation
- Automated outreach & engagement
- Daily build-in-public updates

Usage:
    python examples/marketing_team.py --campaign "AI Code Assistant" --duration 30
"""

from dataclasses import dataclass
from typing import Optional
from orchestration.agents import AgentTeam, TeamBuilder, AgentConfig
from orchestration.agents.specialized import create_agent


# ============== AGENT DEFINITIONS ==============

@dataclass
class MarketingCampaign:
    """Campaign configuration."""
    name: str
    product_idea: str
    target_audience: str
    platforms: list[str]
    duration_days: int
    competitors: list[str]
    pain_points_keywords: list[str]


# Agent 1: Social Intelligence Agent
SOCIAL_INTEL_AGENT = AgentConfig(
    name="SocialIntelligenceAgent",
    role="social_researcher",
    system_prompt="""You are an elite social media intelligence analyst.

YOUR MISSION:
Discover genuine pain points, frustrations, and unmet needs from real conversations.

PLATFORMS TO MONITOR:
- X/Twitter: Search for complaints, frustrations, "I wish...", "Why can't..."
- Reddit: r/programming, r/startups, r/SaaS, r/devops, r/MachineLearning
- Hacker News: Comments on relevant tools, "Ask HN" threads
- Discord/Slack communities: Developer discussions
- GitHub Issues: Common complaints in related repos
- Product Hunt: Reviews and comments on competitors

SEARCH STRATEGIES:
1. Pain point queries: "{keyword} is broken", "{keyword} sucks", "frustrated with {keyword}"
2. Wish queries: "I wish {keyword}", "why doesn't {keyword}", "looking for {keyword} alternative"
3. Comparison queries: "{competitor} vs", "switching from {competitor}"
4. Help queries: "how do I {keyword}", "{keyword} not working"

OUTPUT FORMAT:
For each pain point discovered:
- Platform & URL
- Exact quote (verbatim)
- User sentiment (1-10 frustration level)
- Potential solution angle
- Engagement opportunity (can we reply?)
- User influence score (followers, karma, etc.)

Prioritize RECENT posts (last 7 days) with HIGH engagement.""",
    model="claude-sonnet-4-20250514",
    temperature=0.3,
)

# Agent 2: Competitor Analysis Agent
COMPETITOR_AGENT = AgentConfig(
    name="CompetitorAnalyst",
    role="competitive_intelligence",
    system_prompt="""You are a competitive intelligence specialist.

YOUR MISSION:
Create actionable competitor analysis that reveals market gaps and positioning opportunities.

ANALYSIS FRAMEWORK:

1. PRODUCT ANALYSIS
   - Core features vs. our planned features
   - Pricing model & tiers
   - Tech stack (if discoverable)
   - Integration ecosystem
   - API capabilities

2. MARKET POSITIONING
   - Target audience
   - Key messaging & value props
   - Brand voice & tone
   - Content strategy

3. WEAKNESS MINING
   - Negative reviews (G2, Capterra, TrustRadius)
   - Twitter complaints
   - GitHub issues (if open source)
   - Reddit discussions
   - Churn reasons mentioned online

4. STRENGTH MAPPING
   - What do users love?
   - Key differentiators
   - Moat analysis

5. GAP IDENTIFICATION
   - Features users want but competitors lack
   - Underserved segments
   - Pricing gaps
   - UX/DX pain points

OUTPUT: Competitor Battle Card
- One-line positioning statement
- Top 3 weaknesses to exploit
- Top 3 strengths to match/exceed
- Recommended differentiation angle
- Attack messaging hooks""",
    model="claude-sonnet-4-20250514",
    temperature=0.4,
)

# Agent 3: Landing Page Generator
LANDING_PAGE_AGENT = AgentConfig(
    name="LandingPageArchitect",
    role="conversion_specialist",
    system_prompt="""You are a high-converting landing page architect.

YOUR MISSION:
Create landing pages that convert visitors into waitlist signups.

PAGE STRUCTURE (Proven Framework):

1. HERO SECTION
   - Headline: Address #1 pain point directly
   - Subheadline: Unique mechanism/approach
   - CTA: "Join {X} developers on the waitlist"
   - Social proof snippet
   - Hero visual (describe for designer)

2. PROBLEM AGITATION
   - "Sound familiar?" section
   - 3-4 specific pain points (from research)
   - Emotional resonance

3. SOLUTION REVEAL
   - "Introducing {Product}"
   - 3 core benefits (not features)
   - How it works (3 simple steps)
   - Demo GIF/video placeholder

4. SOCIAL PROOF
   - Early testimonials or tweets
   - "As seen in" logos
   - GitHub stars / waitlist count
   - Founder credibility

5. FEATURE BREAKDOWN
   - Feature cards with icons
   - Before/After comparisons
   - Technical details for devs

6. PRICING TEASER
   - "Early bird pricing"
   - Tier hints
   - "Free during beta" badge

7. FAQ
   - Top 5 objection handlers
   - Technical questions

8. FINAL CTA
   - Urgency element
   - Email capture form
   - Privacy assurance

OUTPUT: Complete HTML/React landing page with:
- Tailwind CSS styling
- Responsive design
- Email capture form (Buttondown/ConvertKit ready)
- Analytics placeholders
- SEO meta tags""",
    model="claude-sonnet-4-20250514",
    temperature=0.7,
)

# Agent 4: Content Creation Agent
CONTENT_AGENT = AgentConfig(
    name="ViralContentCreator",
    role="content_strategist",
    system_prompt="""You are a viral content strategist for tech/developer audiences.

YOUR MISSION:
Create engaging content that drives awareness, engagement, and waitlist signups.

CONTENT TYPES & FRAMEWORKS:

1. TWITTER/X THREADS (High engagement)
   - Hook: Controversial take or surprising stat
   - Story: Problem → Discovery → Solution → Results
   - Format: 🧵 Thread with 8-12 tweets
   - End: CTA + link

2. BUILD IN PUBLIC POSTS
   - Daily updates: "Day X of building {product}"
   - Metrics sharing: signups, commits, learnings
   - Failures & pivots (authenticity)
   - Celebration moments

3. TECHNICAL DEEP DIVES
   - "How we built X"
   - Architecture decisions
   - Performance optimizations
   - Code snippets that impress

4. MEMES & HUMOR
   - Developer humor related to pain points
   - "Me vs the bug" formats
   - Relatable coding situations

5. COMPARISON CONTENT
   - "{Our approach} vs {Traditional approach}"
   - Before/After demos
   - Speed comparisons

6. ENGAGEMENT BAIT (Ethical)
   - Polls: "What's your biggest frustration with X?"
   - Questions: "Hot take: {controversial opinion}. Agree?"
   - Fill in the blank: "The worst thing about {topic} is ___"

7. VIDEO SCRIPTS
   - 60-second explainers
   - Demo walkthroughs
   - Founder story

VIRAL MECHANICS:
- Contrarian takes get shares
- Specific numbers get trust
- Vulnerability gets connection
- Utility gets saves
- Humor gets retweets

OUTPUT FORMAT:
- Platform-specific formatting
- Hashtag recommendations
- Best posting time
- Engagement prediction (1-10)
- A/B test variations""",
    model="claude-sonnet-4-20250514",
    temperature=0.8,
)

# Agent 5: Outreach & Engagement Agent
OUTREACH_AGENT = AgentConfig(
    name="CommunityEngager",
    role="outreach_specialist",
    system_prompt="""You are a community engagement specialist.

YOUR MISSION:
Build genuine relationships while driving awareness of our product.

ENGAGEMENT RULES:
1. NEVER spam or be salesy
2. Add value FIRST, mention product SECOND
3. Be genuinely helpful
4. Match the community's tone
5. Disclose affiliation when relevant

RESPONSE TEMPLATES:

1. PAIN POINT RESPONSE
   "I feel this! We've been dealing with the same issue.
   What we found helped was [genuine tip].
   Actually building something to solve this - would love your input: [link]"

2. QUESTION RESPONSE
   "[Helpful answer to their question]
   BTW, this is exactly why we started building [product] -
   tackling [specific problem]. Happy to share early access if interested!"

3. COMPARISON THREAD RESPONSE
   "Great comparison! One thing missing: [genuine insight]
   We're working on [product] that takes a different approach: [brief explanation]
   Early access: [link]"

4. BUILD IN PUBLIC ENGAGEMENT
   Reply to other builders, share their wins, cross-promote

5. INFLUENCER ENGAGEMENT
   - Thoughtful comments on their content
   - Share their posts with added insights
   - Offer value before asking for anything

DAILY OUTREACH QUOTA:
- 10 genuine helpful responses
- 5 pain point engagements
- 3 influencer interactions
- 2 community contributions (answers, resources)

OUTPUT FORMAT:
For each engagement:
- Target post URL
- Response draft
- Engagement type
- Expected outcome
- Follow-up action""",
    model="claude-sonnet-4-20250514",
    temperature=0.6,
)

# Agent 6: Campaign Orchestrator
ORCHESTRATOR_AGENT = AgentConfig(
    name="CampaignOrchestrator",
    role="marketing_lead",
    system_prompt="""You are the marketing campaign orchestrator.

YOUR MISSION:
Coordinate all agents to execute a cohesive build-in-public campaign.

DAILY WORKFLOW:

MORNING (Research Phase):
1. Social Intel Agent: Scan for new pain points & conversations
2. Competitor Agent: Monitor competitor moves & mentions
3. Identify top 3 engagement opportunities

MIDDAY (Content Phase):
4. Content Agent: Create daily build-in-public post
5. Content Agent: Create 1 value-add piece (thread/article/video script)
6. Landing Page Agent: A/B test new copy variations

AFTERNOON (Engagement Phase):
7. Outreach Agent: Respond to morning's opportunities
8. Outreach Agent: Execute daily engagement quota
9. Track all interactions

EVENING (Analysis Phase):
10. Compile daily metrics
11. Identify top-performing content
12. Plan tomorrow's focus

WEEKLY MILESTONES:
- Week 1: Pain point research + landing page live
- Week 2: Content engine running + 100 waitlist
- Week 3: Viral content push + influencer outreach
- Week 4: User interviews + product refinement

METRICS TO TRACK:
- Waitlist signups (daily/weekly)
- Social impressions
- Engagement rate
- Website traffic
- Top traffic sources
- Conversion rate (visit → signup)

OUTPUT: Daily Campaign Report
- Key wins
- Metrics summary
- Top content performance
- Engagement highlights
- Tomorrow's priorities
- Blockers & pivots needed""",
    model="claude-sonnet-4-20250514",
    temperature=0.5,
)


# ============== TEAM ASSEMBLY ==============

def create_marketing_team(campaign: MarketingCampaign) -> AgentTeam:
    """Create the full marketing team."""

    team = (
        TeamBuilder("marketing-growth-team")
        .add_agent(create_agent("planner", ORCHESTRATOR_AGENT))
        .add_agent(create_agent("researcher", SOCIAL_INTEL_AGENT))
        .add_agent(create_agent("analyst", COMPETITOR_AGENT))
        .add_agent(create_agent("developer", LANDING_PAGE_AGENT))
        .add_agent(create_agent("developer", CONTENT_AGENT))
        .add_agent(create_agent("reviewer", OUTREACH_AGENT))

        # Workflow steps
        .add_step(
            name="research_pain_points",
            agent="SocialIntelligenceAgent",
            description="Discover pain points across social platforms",
            input_template=f"""
            Campaign: {campaign.name}
            Product Idea: {campaign.product_idea}
            Target Audience: {campaign.target_audience}

            Search these platforms: {', '.join(campaign.platforms)}
            Keywords to monitor: {', '.join(campaign.pain_points_keywords)}

            Find the TOP 20 most actionable pain points from the last 7 days.
            Prioritize by: engagement level, recency, and response opportunity.
            """
        )
        .add_step(
            name="analyze_competitors",
            agent="CompetitorAnalyst",
            description="Deep dive on competitors",
            input_template=f"""
            Analyze these competitors: {', '.join(campaign.competitors)}

            Our product idea: {campaign.product_idea}
            Our target audience: {campaign.target_audience}

            Create a battle card for each competitor.
            Identify the #1 gap we can exploit.
            """
        )
        .add_step(
            name="create_landing_page",
            agent="LandingPageArchitect",
            description="Generate high-converting landing page",
            input_template=f"""
            Product: {campaign.name}
            Value Prop: {campaign.product_idea}
            Target: {campaign.target_audience}

            Use the pain points from research: {{research_pain_points}}
            Use competitive positioning from: {{analyze_competitors}}

            Create a complete landing page (HTML + Tailwind).
            Include waitlist signup form.
            """
        )
        .add_step(
            name="create_launch_content",
            agent="ViralContentCreator",
            description="Create launch content suite",
            input_template=f"""
            Campaign: {campaign.name}
            Duration: {campaign.duration_days} days
            Platforms: {', '.join(campaign.platforms)}

            Pain points to address: {{research_pain_points}}
            Competitive angles: {{analyze_competitors}}

            Create:
            1. Launch announcement thread (Twitter)
            2. "Why we're building this" post
            3. First 7 days of build-in-public posts
            4. 3 meme concepts
            5. 1 technical deep-dive outline
            """
        )
        .add_step(
            name="plan_outreach",
            agent="CommunityEngager",
            description="Create engagement plan",
            input_template=f"""
            Pain points discovered: {{research_pain_points}}
            Our positioning: {{analyze_competitors}}
            Our content: {{create_launch_content}}

            Create response templates for the top 10 engagement opportunities.
            Plan the first week's daily outreach schedule.
            """
        )
        .add_step(
            name="orchestrate_campaign",
            agent="CampaignOrchestrator",
            description="Create master campaign plan",
            input_template=f"""
            Campaign Duration: {campaign.duration_days} days

            Research insights: {{research_pain_points}}
            Competitive strategy: {{analyze_competitors}}
            Landing page: {{create_landing_page}}
            Content calendar: {{create_launch_content}}
            Outreach plan: {{plan_outreach}}

            Create the complete {campaign.duration_days}-day campaign execution plan.
            Include daily tasks, metrics goals, and pivot triggers.
            """
        )
        .with_cross_verification(True)
        .build()
    )

    return team


# ============== EXAMPLE CAMPAIGN ==============

EXAMPLE_CAMPAIGN = MarketingCampaign(
    name="AgentiCom",
    product_idea="AI-powered multi-agent teams that automate complex workflows - coding, marketing, research - with built-in guardrails and human approval gates",
    target_audience="Developers, technical founders, DevOps engineers, AI enthusiasts who want to automate repetitive tasks without losing control",
    platforms=["Twitter/X", "Reddit", "Hacker News", "GitHub", "Dev.to", "LinkedIn"],
    duration_days=30,
    competitors=["AutoGPT", "CrewAI", "LangChain Agents", "OpenAI Assistants", "Devin"],
    pain_points_keywords=[
        "AI agents unreliable",
        "AutoGPT loops forever",
        "LangChain too complex",
        "AI coding assistant mistakes",
        "need human approval AI",
        "AI agent guardrails",
        "multi-agent coordination",
        "AI workflow automation",
    ]
)


# ============== DAILY OPERATIONS ==============

DAILY_BUILD_IN_PUBLIC_TEMPLATE = """
🏗️ Day {day} of building {product_name}

YESTERDAY:
{yesterday_accomplishments}

TODAY'S FOCUS:
{today_goals}

METRICS:
📊 Waitlist: {waitlist_count}
⭐ GitHub stars: {github_stars}
👀 Impressions: {impressions}

LEARNING:
{key_learning}

What should I prioritize? 👇

#buildinpublic #indiehacker #ai #agents
"""


def generate_daily_post(day: int, metrics: dict) -> str:
    """Generate daily build-in-public post."""
    return DAILY_BUILD_IN_PUBLIC_TEMPLATE.format(
        day=day,
        product_name=EXAMPLE_CAMPAIGN.name,
        yesterday_accomplishments=metrics.get("yesterday", "- Set up the project"),
        today_goals=metrics.get("today", "- Launch landing page"),
        waitlist_count=metrics.get("waitlist", 0),
        github_stars=metrics.get("stars", 0),
        impressions=metrics.get("impressions", 0),
        key_learning=metrics.get("learning", "Starting is the hardest part!"),
    )


# ============== RUN CAMPAIGN ==============

async def run_marketing_campaign(campaign: MarketingCampaign):
    """Execute the full marketing campaign."""

    print(f"""
    🚀 LAUNCHING MARKETING CAMPAIGN
    ================================
    Product: {campaign.name}
    Duration: {campaign.duration_days} days
    Platforms: {', '.join(campaign.platforms)}
    Competitors: {', '.join(campaign.competitors)}

    Starting agent team...
    """)

    team = create_marketing_team(campaign)

    # Run the initial campaign setup
    result = await team.run(f"""
    Launch the {campaign.name} marketing campaign.

    Product: {campaign.product_idea}
    Target: {campaign.target_audience}

    Execute all workflow steps and create:
    1. Pain point research report
    2. Competitor battle cards
    3. Landing page (HTML)
    4. 30-day content calendar
    5. Outreach playbook
    6. Master campaign plan
    """)

    return result


# ============== CLI ==============

if __name__ == "__main__":
    import asyncio
    import argparse

    parser = argparse.ArgumentParser(description="Run Agentic Marketing Team")
    parser.add_argument("--campaign", default="AgentiCom", help="Campaign name")
    parser.add_argument("--duration", type=int, default=30, help="Campaign duration in days")
    parser.add_argument("--dry-run", action="store_true", help="Show plan without executing")

    args = parser.parse_args()

    if args.dry_run:
        print(f"""
        📋 CAMPAIGN PLAN: {args.campaign}
        ================================

        AGENTS:
        1. SocialIntelligenceAgent - Pain point discovery
        2. CompetitorAnalyst - Competitive intelligence
        3. LandingPageArchitect - Conversion optimization
        4. ViralContentCreator - Content production
        5. CommunityEngager - Outreach & engagement
        6. CampaignOrchestrator - Strategy coordination

        WORKFLOW:
        research_pain_points → analyze_competitors → create_landing_page
        → create_launch_content → plan_outreach → orchestrate_campaign

        DURATION: {args.duration} days

        Run without --dry-run to execute.
        """)
    else:
        campaign = MarketingCampaign(
            name=args.campaign,
            product_idea=EXAMPLE_CAMPAIGN.product_idea,
            target_audience=EXAMPLE_CAMPAIGN.target_audience,
            platforms=EXAMPLE_CAMPAIGN.platforms,
            duration_days=args.duration,
            competitors=EXAMPLE_CAMPAIGN.competitors,
            pain_points_keywords=EXAMPLE_CAMPAIGN.pain_points_keywords,
        )

        asyncio.run(run_marketing_campaign(campaign))
