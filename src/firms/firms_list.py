"""List of known quantitative finance firms and related keywords"""

# Major quantitative finance firms
QUANT_FIRMS = [
    # Hedge Funds
    "Citadel", "Citadel Securities", "Two Sigma", "Renaissance Technologies",
    "DE Shaw", "D. E. Shaw", "Jump Trading", "Jane Street", "Optiver",
    "IMC Trading", "Akuna Capital", "DRW", "Susquehanna International Group",
    "SIG", "Hudson River Trading", "HRT", "Tower Research", "Virtu Financial",
    "Wolverine Trading", "Old Mission", "Five Rings", "Radix Trading",
    "XR Trading", "Quantitative Investment Management", "QIM",

    # Investment Banks - Quant Divisions
    "Goldman Sachs", "Morgan Stanley", "JP Morgan", "JPMorgan",
    "Bank of America", "Barclays", "Credit Suisse", "UBS",
    "Deutsche Bank", "Citi", "Citigroup",

    # Asset Managers - Quant Divisions
    "BlackRock", "Vanguard", "State Street", "AQR Capital",
    "Bridgewater Associates", "Millennium Management",
    "Point72", "Winton Group", "Man Group", "Schonfeld",

    # Proprietary Trading
    "Chicago Trading Company", "CTC", "Geneva Trading", "Belvedere Trading",
    "Allston Trading", "TransMarket Group", "TMG", "Peak6",
    "Headlands Tech", "Valkyrie Trading",

    # Market Makers
    "Citadel Securities", "Virtu Financial", "Flow Traders",
    "GTS", "Global Trading Systems", "XTX Markets",

    # Crypto/Blockchain Quant & Market Makers
    "Jump Crypto", "Cumberland", "Wintermute", "GSR",
    "Galaxy Digital", "Paradigm", "Framework Ventures",
    "FalconX", "B2C2", "Amber Group", "QCP Capital",
    "Kronos Research", "Folkvang", "CMS Holdings",
    "Alameda Research",  # Historical (defunct 2022)

    # Crypto Exchanges with Quant/Trading Teams
    "Coinbase", "Kraken", "Gemini", "Binance US",

    # Fintech with Quant Focus
    "Robinhood", "Bloomberg", "FactSet", "Refinitiv",
]

# Keywords that indicate quantitative finance events
QUANT_KEYWORDS = [
    # Job Titles
    "quantitative", "quant", "trader", "trading", "systematic",
    "algorithmic", "algo", "market maker", "portfolio manager",
    "risk management", "derivatives", "fixed income",

    # Technical
    "machine learning", "ml", "data science", "statistics",
    "stochastic calculus", "time series", "optimization",
    "high frequency", "hft", "low latency",

    # Finance
    "equity", "options", "futures", "commodities",
    "forex", "rates", "credit", "volatility",
    "arbitrage", "alpha", "factor models",
    "crypto", "cryptocurrency", "blockchain", "defi",
    "digital assets", "market making",

    # Academic
    "financial engineering", "computational finance",
    "mathematical finance", "econometrics",

    # Companies
    *[firm.lower() for firm in QUANT_FIRMS]
]

# Job role keywords for filtering relevant positions
QUANT_JOB_ROLES = [
    "quantitative researcher", "quant researcher", "qr",
    "quantitative trader", "quant trader", "trader",
    "quantitative developer", "quant developer", "quant dev",
    "quantitative analyst", "quant analyst",
    "research scientist", "research engineer",
    "data scientist", "ml engineer", "machine learning",
    "software engineer - trading", "trading systems",
    "portfolio manager", "portfolio analyst",
    "risk analyst", "risk manager",
    "derivatives analyst", "derivatives trader",
    "market maker", "systematic trader",
]

# Campus event sources (can be extended)
CAMPUS_EVENT_SOURCES = {
    "MIT CSAIL": {
        "url": "https://www.csail.mit.edu/events",
        "rss": None,
    },
    "Stanford CS": {
        "url": "https://cs.stanford.edu/events",
        "rss": None,
    },
    "CMU CS": {
        "url": "https://www.cs.cmu.edu/calendar",
        "rss": None,
    },
    "Berkeley EECS": {
        "url": "https://eecs.berkeley.edu/events",
        "rss": None,
    },
    "Princeton CS": {
        "url": "https://www.cs.princeton.edu/events",
        "rss": None,
    },
}

# Careers page patterns for known firms
FIRM_CAREERS_URLS = {
    "Citadel": "https://www.citadel.com/careers/",
    "Two Sigma": "https://careers.twosigma.com/",
    "Jane Street": "https://www.janestreet.com/join-jane-street/",
    "Jump Trading": "https://www.jumptrading.com/careers/",
    "DE Shaw": "https://www.deshaw.com/careers",
    "Hudson River Trading": "https://www.hudsonrivertrading.com/careers/",
    "Optiver": "https://optiver.com/working-at-optiver/career-opportunities/",
    "IMC Trading": "https://careers.imc.com/",
    "Akuna Capital": "https://akunacapital.com/careers",
    "DRW": "https://drw.com/careers/",
    "Susquehanna International Group": "https://sig.com/careers/",
    "Tower Research": "https://www.tower-research.com/careers",
    "Virtu Financial": "https://www.virtu.com/careers/",
    "Old Mission": "https://www.oldmissioncapital.com/careers/",
    "Five Rings": "https://fiverings.com/careers/",
    "AQR Capital": "https://careers.aqr.com/",
    "Millennium": "https://www.mlp.com/careers/",
    "Point72": "https://careers.point72.com/",

    # Crypto/Digital Asset Firms
    "XTX Markets": "https://www.xtxmarkets.com/careers/",
    "Jump Crypto": "https://jumpcrypto.com/careers/",
    "Cumberland": "https://cumberland.io/careers/",
    "Wintermute": "https://www.wintermute.com/careers",
    "GSR": "https://www.gsr.io/careers/",
    "Galaxy Digital": "https://www.galaxydigital.io/careers/",
    "Paradigm": "https://www.paradigm.xyz/opportunities",
    "FalconX": "https://www.falconx.io/careers",
    "B2C2": "https://www.b2c2.com/careers",
    "Coinbase": "https://www.coinbase.com/careers",
    "Kraken": "https://www.kraken.com/careers",
    "Gemini": "https://www.gemini.com/careers",
}

# Engineering blogs and tech content
FIRM_BLOG_URLS = {
    "Citadel": "https://www.citadel.com/news/",
    "Two Sigma": "https://www.twosigma.com/articles/",
    "Jane Street": "https://blog.janestreet.com/",
    "Jump Trading": "https://www.jumptrading.com/insights/",
    "DE Shaw": "https://www.deshaw.com/insights",
    "Hudson River Trading": "https://www.hudsonrivertrading.com/hrtbeat/",
    "Optiver": "https://optiver.com/insights/",
    "IMC Trading": "https://www.imc.com/us/insights/",
    "Akuna Capital": "https://akunacapital.com/news-and-insights",
    "DRW": "https://drw.com/insights/",
    "Susquehanna International Group": "https://sig.com/news-insights/",
    "Tower Research": "https://www.tower-research.com/insights/",
    "AQR Capital": "https://www.aqr.com/Insights",
    "Millennium": "https://www.mlp.com/insights/",
    "Point72": "https://www.point72.com/insights/",
    "Goldman Sachs": "https://www.goldmansachs.com/insights/",
    "Morgan Stanley": "https://www.morganstanley.com/ideas/",
    "JP Morgan": "https://www.jpmorgan.com/insights",

    # Crypto/Digital Asset Firms
    "XTX Markets": "https://www.xtxmarkets.com/insights",
    "Jump Crypto": "https://jumpcrypto.com/writing/",
    "Paradigm": "https://www.paradigm.xyz/writing",
    "Galaxy Digital": "https://www.galaxy.com/insights/",
    "Coinbase": "https://www.coinbase.com/blog",
    "Kraken": "https://blog.kraken.com/",
    "FalconX": "https://www.falconx.io/insights",
}

# Investor relations and reports
FIRM_INVESTOR_URLS = {
    "Citadel": "https://www.citadel.com/investment-strategies/",
    "Two Sigma": "https://www.twosigma.com/funds/",
    "AQR Capital": "https://www.aqr.com/library",
    "Millennium": "https://www.mlp.com/about/",
    "Point72": "https://www.point72.com/",
    "Bridgewater Associates": "https://www.bridgewater.com/research-and-insights/",
    "Goldman Sachs": "https://www.goldmansachs.com/investor-relations/",
    "Morgan Stanley": "https://www.morganstanley.com/about-us-ir",
    "JP Morgan": "https://www.jpmorganchase.com/ir/investor-relations",
    "BlackRock": "https://ir.blackrock.com/",

    # Crypto/Digital Asset Firms
    "Galaxy Digital": "https://investor.galaxydigital.io/",
    "Coinbase": "https://investor.coinbase.com/",
}

# YouTube channels and video content
FIRM_YOUTUBE_CHANNELS = {
    "Citadel": "UCR6pJLJj5PJqQvXYhLpKEHQ",  # Citadel
    "Two Sigma": "UCjOhwAU8VNpxCpJqKyf8sYA",  # Two Sigma
    "Jane Street": "UCDsK_KHQ-xRqRfMd1xvEXkg",  # Jane Street
    "AQR Capital": "UCyPXdMWkJqFvqJfvqFmRRRg",  # AQR Capital Management
    "Goldman Sachs": "UCRJzYKfa-8L6pKqVq4DqbpQ",  # Goldman Sachs
    "Morgan Stanley": "UCzjNRcGmWqf0xDDJEJDnRjg",  # Morgan Stanley
    "JP Morgan": "UCe3v8hXGwVd1eMDmvFr2G7w",  # JPMorgan Chase & Co.
    "BlackRock": "UCp_SdNPEZmBEcrwEh1W2OXg",  # BlackRock

    # Crypto/Digital Asset Firms
    "Coinbase": "UCd1KHfthXPRlmVMFXG8jhmA",  # Coinbase
    "Galaxy Digital": "UCjvhJObOwSKZ8qYx5iQOahw",  # Galaxy Digital
    "Paradigm": "UCLVz6W-fFL_vPZvNdMqMqaw",  # Paradigm (if available)
}
