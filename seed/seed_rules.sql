-- seed_rules.sql
-- Deterministic categorization rules for Personal Finance Automation
-- Higher priority = evaluated first
-- condition JSONB supports: mcc, descriptor_regex, amount_range, account, direction
-- action JSONB: category, subcategory

-- MCC-based rules (Priority 100 - highest confidence)

-- Groceries & Food Stores
INSERT INTO rules (priority, condition, action, active) VALUES
(100, '{"mcc": ["5411", "5422", "5499"]}', '{"category": "Groceries", "subcategory": "Supermarket"}', true),

-- Dining & Restaurants
(100, '{"mcc": ["5812", "5814"]}', '{"category": "Dining", "subcategory": "Restaurant"}', true),
(100, '{"mcc": ["5813"]}', '{"category": "Dining", "subcategory": "Bar"}', true),

-- Transportation
(100, '{"mcc": ["4111", "4121", "4131"]}', '{"category": "Transport", "subcategory": "Rideshare"}', true),
(100, '{"mcc": ["4011"]}', '{"category": "Transport", "subcategory": "Railroad"}', true),
(100, '{"mcc": ["3000", "3001", "3002", "3003", "3004", "3005", "3006", "3007", "3008", "3009", "3010", "3011"]}', '{"category": "Travel-Air", "subcategory": "Airlines"}', true),
(100, '{"mcc": ["4112"]}', '{"category": "Transport", "subcategory": "Rail"}', true),
(100, '{"mcc": ["4722"]}', '{"category": "Travel-Other", "subcategory": "Travel Agency"}', true),

-- Fuel & Gas Stations
(100, '{"mcc": ["5541", "5542", "5983"]}', '{"category": "Fuel", "subcategory": "Gas Station"}', true),

-- Utilities
(100, '{"mcc": ["4814", "4815", "4816"]}', '{"category": "Mobile", "subcategory": "Wireless"}', true),
(100, '{"mcc": ["4899", "4900"]}', '{"category": "Utilities", "subcategory": "Cable/Utilities"}', true),
(100, '{"mcc": ["4812"]}', '{"category": "Mobile", "subcategory": "Telecom"}', true),

-- Healthcare
(100, '{"mcc": ["5912", "5122"]}', '{"category": "Healthcare", "subcategory": "Pharmacy"}', true),
(100, '{"mcc": ["8011", "8021", "8031", "8041", "8042", "8043", "8049", "8050", "8062", "8071", "8099"]}', '{"category": "Healthcare", "subcategory": "Medical"}', true),

-- Entertainment
(100, '{"mcc": ["7832", "7841"]}', '{"category": "Entertainment", "subcategory": "Movies"}', true),
(100, '{"mcc": ["5735"]}', '{"category": "Entertainment", "subcategory": "Music"}', true),

-- Hotels
(100, '{"mcc": ["3501", "3502", "3503", "3504", "3505", "3506", "3507", "3508", "3509", "3510", "3511", "3512", "3513", "3514", "3515", "3516", "3517", "3518", "3519", "3520", "3521", "3522", "3523", "3524", "3525", "3526", "3527", "3528", "3529", "3530", "3531", "3532", "3533", "3534", "3535", "3536", "3537", "3538", "3539", "3540", "3541", "3542", "3543", "3544", "3545", "3546", "3547", "3548", "3549", "3550", "3551", "3552", "3553", "3554", "3555", "3556", "3557", "3558", "3559", "3560", "3561", "3562", "3563", "3564", "3565", "3566", "3567", "3568", "3569", "3570", "3571", "3572", "3573", "3574", "3575", "3576", "3577", "3578", "3579", "3580", "3581", "3582", "3583", "3584", "3585", "3586", "3587", "3588", "3589", "3590", "3591", "3592", "3593", "3594", "3595", "3596", "3597", "3598", "3599", "7011"]}', '{"category": "Travel-Hotel", "subcategory": "Lodging"}', true),

-- Pet Care
(100, '{"mcc": ["0742", "5995"]}', '{"category": "Pets", "subcategory": "Veterinary"}', true),

-- Descriptor-based rules (Priority 50 - high confidence patterns)

-- Subscription Services
(50, '{"descriptor_regex": "(?i)(NETFLIX|HULU|SPOTIFY|ICLOUD|AMAZON PRIME|YOUTUBE|DISNEY\\+|HBO MAX|PEACOCK|PARAMOUNT\\+|APPLE MUSIC|APPLE TV)"}', '{"category": "Subscriptions", "subcategory": "Streaming"}', true),
(50, '{"descriptor_regex": "(?i)(ADOBE|MICROSOFT 365|DROPBOX|ZOOM|SLACK|GITHUB|JETBRAINS)"}', '{"category": "Subscriptions", "subcategory": "Software"}', true),
(50, '{"descriptor_regex": "(?i)(AUDIBLE|KINDLE UNLIMITED|SCRIBD)"}', '{"category": "Subscriptions", "subcategory": "Reading"}', true),

-- Groceries (Major Chains)
(50, '{"descriptor_regex": "(?i)(HY-VEE|HYVEE|FAREWAY|COSTCO|WAL.*MART.*SUPER|TARGET|ALDI|KROGER|SAFEWAY|WHOLE FOODS|TRADER JOE)"}', '{"category": "Groceries", "subcategory": "Supermarket"}', true),

-- Airlines
(50, '{"descriptor_regex": "(?i)(DELTA|UNITED|AMERICAN AIR|SOUTHWEST|JETBLUE|SPIRIT|FRONTIER|ALASKA AIR)"}', '{"category": "Travel-Air", "subcategory": "Airlines"}', true),

-- Hotels
(50, '{"descriptor_regex": "(?i)(MARRIOTT|HILTON|HYATT|IHG|HOLIDAY INN|HAMPTON INN|SHERATON|WESTIN|COURTYARD|RESIDENCE INN)"}', '{"category": "Travel-Hotel", "subcategory": "Hotel"}', true),

-- Income
(50, '{"descriptor_regex": "(?i)(PAYROLL|DIRECT DEP|ACH CREDIT|SALARY|WAGES)", "direction": "credit"}', '{"category": "Income", "subcategory": "Salary"}', true),
(50, '{"descriptor_regex": "(?i)(VENMO CASHOUT|ZELLE|CASH APP)", "direction": "credit"}', '{"category": "Transfers", "subcategory": "P2P"}', true),

-- Fast Food
(50, '{"descriptor_regex": "(?i)(MCDONALD|BURGER KING|WENDY|TACO BELL|KFC|CHICK-FIL-A|CHIPOTLE|PANERA|SUBWAY|ARBY)"}', '{"category": "Dining", "subcategory": "Fast Food"}', true),

-- Coffee Shops
(50, '{"descriptor_regex": "(?i)(STARBUCKS|DUNKIN|CARIBOU|PEET|DUTCH BROS)"}', '{"category": "Dining", "subcategory": "Coffee"}', true),

-- Gas Stations (Brands)
(50, '{"descriptor_regex": "(?i)(CASEY|SHELL|BP|MOBIL|EXXON|CHEVRON|MARATHON|SPEEDWAY|CIRCLE K|PILOT|LOVES|KWIK TRIP|QT |QUIKTRIP)"}', '{"category": "Fuel", "subcategory": "Gas Station"}', true),

-- Retail
(50, '{"descriptor_regex": "(?i)(AMAZON\\.COM|AMZN|WALMART\\.COM|ETSY|EBAY)"}', '{"category": "Shopping", "subcategory": "Online"}', true),
(50, '{"descriptor_regex": "(?i)(HOME DEPOT|LOWES|MENARDS|ACE HARDWARE)"}', '{"category": "Shopping", "subcategory": "Hardware"}', true),

-- Utilities
(50, '{"descriptor_regex": "(?i)(ALLIANT|MIDAMERICAN|ELECTRIC|GAS COMPANY|WATER UTILITY)"}', '{"category": "Utilities", "subcategory": "Electric/Gas"}', true),
(50, '{"descriptor_regex": "(?i)(COMCAST|XFINITY|SPECTRUM|ATT|VERIZON FIO|CENTURYLINK|GOOGLE FIBER)"}', '{"category": "Internet", "subcategory": "ISP"}', true),
(50, '{"descriptor_regex": "(?i)(VERIZON WIRELESS|ATT WIRELESS|T-MOBILE|SPRINT)"}', '{"category": "Mobile", "subcategory": "Wireless"}', true),

-- Fitness
(50, '{"descriptor_regex": "(?i)(PLANET FITNESS|LA FITNESS|ANYTIME FITNESS|YMCA|CROSSFIT|ORANGETHEORY)"}', '{"category": "Subscriptions", "subcategory": "Fitness"}', true),

-- Pharmacy
(50, '{"descriptor_regex": "(?i)(CVS|WALGREENS|RITE AID|PHARMACY)"}', '{"category": "Healthcare", "subcategory": "Pharmacy"}', true),

-- Car Services
(50, '{"descriptor_regex": "(?i)(JIFFY LUBE|OIL CHANGE|AUTO REPAIR|TIRE|MIDAS|FIRESTONE)"}', '{"category": "Transport", "subcategory": "Maintenance"}', true),

-- Insurance
(50, '{"descriptor_regex": "(?i)(GEICO|STATE FARM|PROGRESSIVE|ALLSTATE|FARMERS INS)"}', '{"category": "Insurance", "subcategory": "Auto"}', true),

-- Charitable Donations
(50, '{"descriptor_regex": "(?i)(DONATION|CHARITY|RED CROSS|UNICEF|GOODWILL|SALVATION ARMY)"}', '{"category": "Gifts/Charity", "subcategory": "Charity"}', true);
