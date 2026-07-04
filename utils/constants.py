"""Shared constants for the Instagram Product Analytics platform."""

COUNTRIES = [
    "United States", "India", "Brazil", "Indonesia", "Mexico",
    "United Kingdom", "Germany", "Japan", "France", "Canada",
    "Australia", "South Korea", "Turkey", "Spain", "Italy",
    "Nigeria", "Philippines", "Argentina", "Colombia", "Egypt",
]

DEVICES = ["iOS", "Android", "Web"]

ACQUISITION_CHANNELS = [
    "Organic", "Paid Social", "Referral", "App Store Search",
    "Influencer", "Cross-promotion", "Email", "Push Notification",
]

EVENT_TYPES = [
    "app_open", "feed_view", "reel_view", "story_view", "post_view",
    "like", "comment", "share", "follow", "unfollow", "save",
    "dm_send", "profile_view", "search", "explore_view",
]

FEATURES = [
    "Reels", "Stories", "Feed", "Explore", "DMs", "Live",
    "Shopping", "Notes", "Broadcast Channels", "Collab Posts",
]

CONTENT_TYPES = ["post", "reel", "story", "live", "carousel"]

EXPERIMENT_NAMES = [
    "reels_autoplay_v2", "story_highlights_redesign", "explore_ranking_ml",
    "feed_chronological_toggle", "dm_reactions", "shopping_tab_prominence",
    "creator_bonus_program", "comment_sorting", "reels_remix_prompt",
]

EXPERIMENT_VARIANTS = ["control", "treatment_a", "treatment_b"]

USER_SEGMENTS = [
    "Power User", "Regular", "Casual", "Lurker", "New User", "At Risk", "Churned",
]

META_COLORS = {
    "primary": "#E1306C",
    "secondary": "#833AB4",
    "gradient_start": "#405DE6",
    "gradient_mid": "#5851DB",
    "gradient_end": "#C13584",
    "background": "#FAFAFA",
    "card": "#FFFFFF",
    "text": "#262626",
    "text_secondary": "#8E8E8E",
    "success": "#00C853",
    "warning": "#FF9800",
    "danger": "#F44336",
    "blue": "#0095F6",
}
