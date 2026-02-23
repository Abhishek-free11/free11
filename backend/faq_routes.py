"""
FAQ Routes for FREE11
Help center and frequently asked questions
"""

from fastapi import APIRouter
from typing import List, Dict

faq_router = APIRouter(prefix="/faq", tags=["FAQ"])

# FAQ Data - PRORGA compliant messaging
FAQ_ITEMS = [
    {
        "id": "what-are-coins",
        "category": "coins",
        "question": "What are FREE11 Coins?",
        "answer": "FREE11 Coins are non-withdrawable reward tokens that you earn through skill-based cricket predictions and other activities. They can only be redeemed for goods and services from our partner brands. FREE11 Coins are NOT money, NOT cryptocurrency, and cannot be converted to cash or transferred to other users.",
        "priority": 1
    },
    {
        "id": "coins-not-money",
        "category": "coins",
        "question": "Can I withdraw FREE11 Coins as cash?",
        "answer": "No. FREE11 Coins are NOT money and cannot be withdrawn, transferred, or converted to cash under any circumstances. They exist solely as reward tokens for redeeming brand-funded goods and services. This is by design to ensure FREE11 remains a skill-based platform compliant with all regulations.",
        "priority": 2
    },
    {
        "id": "how-earn-coins",
        "category": "coins",
        "question": "How do I earn FREE11 Coins?",
        "answer": "You earn coins primarily through skill-based cricket predictions. When you correctly predict ball outcomes during live matches, you earn coins based on your accuracy. Additional earning methods include daily check-ins and booster activities (watching ads, mini-games), but your skill in predictions is what drives the most rewards.",
        "priority": 3
    },
    {
        "id": "coin-transfer",
        "category": "coins",
        "question": "Can I transfer coins to friends?",
        "answer": "No. FREE11 Coins are non-transferable. Each user earns and redeems their own coins independently. This ensures fairness and prevents any form of coin manipulation or trading.",
        "priority": 4
    },
    {
        "id": "what-redeem",
        "category": "redemption",
        "question": "What can I redeem my coins for?",
        "answer": "You can redeem coins for a variety of brand-funded rewards including mobile recharges (starting from ₹10), OTT subscriptions, food vouchers, gift cards, and premium products. All rewards are funded by our brand partners, not by FREE11.",
        "priority": 5
    },
    {
        "id": "brand-funded",
        "category": "redemption",
        "question": "What does 'Brand-funded' mean?",
        "answer": "All rewards in the FREE11 shop are funded by our brand partners (like Amazon, Swiggy, Jio) as part of their customer acquisition strategy. FREE11 does not subsidize rewards. This ensures a sustainable ecosystem where brands reach engaged users and users get real value.",
        "priority": 6
    },
    {
        "id": "is-gambling",
        "category": "legal",
        "question": "Is FREE11 a gambling or betting app?",
        "answer": "Absolutely not. FREE11 is a skill-based prediction platform. You earn rewards based on your knowledge and accuracy in predicting cricket outcomes. There is no betting, no stakes, no cash deposits, and no cash withdrawals. Coins cannot be purchased with money. FREE11 is fully compliant with PRORGA guidelines for skill-based gaming.",
        "priority": 7
    },
    {
        "id": "predictions-work",
        "category": "predictions",
        "question": "How do cricket predictions work?",
        "answer": "During live IPL matches, you predict what will happen on each ball (runs, wicket, wide, etc.). If your prediction is correct, you earn coins. The harder the prediction (like predicting a six or wicket), the more coins you earn. Your prediction accuracy determines your rank on leaderboards.",
        "priority": 8
    },
    {
        "id": "what-clans",
        "category": "social",
        "question": "What are Clans?",
        "answer": "Clans are groups of users who compete together for bragging rights. Join a clan to participate in group challenges, maintain clan streaks, and climb the clan leaderboard. Clans are about community and friendly competition - there is no coin pooling or transfers between clan members.",
        "priority": 9
    },
    {
        "id": "leaderboard-ranking",
        "category": "social",
        "question": "How are leaderboards ranked?",
        "answer": "Leaderboards rank users by SKILL metrics, not by total coins. Your position is determined by prediction accuracy percentage, streak length, and correct predictions count. This ensures the leaderboard rewards genuine skill, not just time spent on the app.",
        "priority": 10
    },
    {
        "id": "coin-expiry",
        "category": "coins",
        "question": "Do coins expire?",
        "answer": "Coins do not expire as long as you remain an active user. However, accounts inactive for extended periods (60+ days) may receive reminders to use their coins. We encourage regular engagement to get the most value from your earnings.",
        "priority": 11
    },
    {
        "id": "account-security",
        "category": "account",
        "question": "How is my account secured?",
        "answer": "Your account is protected with secure authentication. We never store your password in plain text. All transactions and predictions are logged securely. Never share your login credentials with anyone.",
        "priority": 12
    }
]

@faq_router.get("/all")
async def get_all_faqs():
    """Get all FAQ items sorted by priority"""
    sorted_faqs = sorted(FAQ_ITEMS, key=lambda x: x["priority"])
    return sorted_faqs

@faq_router.get("/categories")
async def get_faq_categories():
    """Get list of FAQ categories"""
    categories = list(set(faq["category"] for faq in FAQ_ITEMS))
    return {
        "categories": [
            {"id": "coins", "name": "Coins & Earnings", "icon": "💰"},
            {"id": "redemption", "name": "Redemption & Rewards", "icon": "🎁"},
            {"id": "predictions", "name": "Cricket Predictions", "icon": "🏏"},
            {"id": "social", "name": "Clans & Leaderboards", "icon": "👥"},
            {"id": "legal", "name": "Legal & Compliance", "icon": "🛡️"},
            {"id": "account", "name": "Account & Security", "icon": "🔐"},
        ]
    }

@faq_router.get("/category/{category}")
async def get_faqs_by_category(category: str):
    """Get FAQs filtered by category"""
    filtered = [faq for faq in FAQ_ITEMS if faq["category"] == category]
    return sorted(filtered, key=lambda x: x["priority"])

@faq_router.get("/{faq_id}")
async def get_faq_by_id(faq_id: str):
    """Get a specific FAQ by ID"""
    for faq in FAQ_ITEMS:
        if faq["id"] == faq_id:
            return faq
    return {"error": "FAQ not found"}
