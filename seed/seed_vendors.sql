-- seed_vendors.sql
-- Canonical vendor mappings with aliases for normalization
-- Supports fuzzy matching via array of common variants
-- Format: canonical_vendor, default_category, default_subcat, aliases[]

-- Grocery Stores
INSERT INTO vendors (canonical_vendor, default_category, default_subcat, aliases) VALUES
('Hy-Vee', 'Groceries', 'Supermarket', ARRAY['HY-VEE #', 'HYVEE #', 'HY VEE', 'HYVEE', 'HY-VEE STORE']),
('Fareway', 'Groceries', 'Supermarket', ARRAY['FAREWAY #', 'FAREWAY STORE', 'FAREWAY MEAT']),
('Costco', 'Groceries', 'Warehouse Club', ARRAY['COSTCO #', 'COSTCO WHSE', 'COSTCO WHOLESALE']),
('Walmart Supercenter', 'Groceries', 'Supermarket', ARRAY['WALMART SUPERCENTER', 'WAL-MART SUPER', 'WALMART #']),
('Target', 'Shopping', 'Department Store', ARRAY['TARGET #', 'TARGET STORE', 'TARGET T-']),
('Aldi', 'Groceries', 'Discount Grocer', ARRAY['ALDI #', 'ALDI STORE']),
('Whole Foods', 'Groceries', 'Organic', ARRAY['WHOLE FOODS #', 'WFM', 'WHOLE FOODS MARKET']),
('Trader Joes', 'Groceries', 'Specialty', ARRAY['TRADER JOE''S #', 'TRADER JOES', 'TJS']),

-- Restaurants & Dining
('Starbucks', 'Dining', 'Coffee', ARRAY['STARBUCKS #', 'SBUX #', 'STARBUCKS STORE']),
('Dunkin', 'Dining', 'Coffee', ARRAY['DUNKIN'' #', 'DUNKIN DONUTS', 'DUNKIN''DONUTS']),
('Chipotle', 'Dining', 'Fast Food', ARRAY['CHIPOTLE #', 'CHIPOTLE MEXICAN']),
('Panera Bread', 'Dining', 'Fast Casual', ARRAY['PANERA #', 'PANERA BREAD #']),
('Chick-fil-A', 'Dining', 'Fast Food', ARRAY['CHICK-FIL-A #', 'CFA #', 'CHICKFILA']),

-- Gas Stations
('Casey''s', 'Fuel', 'Gas Station', ARRAY['CASEY''S #', 'CASEYS #', 'CASEYS STORE']),
('Shell', 'Fuel', 'Gas Station', ARRAY['SHELL #', 'SHELL OIL']),
('Kwik Trip', 'Fuel', 'Gas Station', ARRAY['KWIK TRIP #', 'KWIKTRIP']),
('QuikTrip', 'Fuel', 'Gas Station', ARRAY['QT #', 'QUIKTRIP #', 'QUIK TRIP']),
('BP', 'Fuel', 'Gas Station', ARRAY['BP #', 'BP STATION']),
('Mobil', 'Fuel', 'Gas Station', ARRAY['MOBIL #', 'EXXONMOBIL']),

-- Subscription Services
('Netflix', 'Subscriptions', 'Streaming', ARRAY['NETFLIX.COM', 'NETFLIX COM', 'NETFLIX INC']),
('Spotify', 'Subscriptions', 'Music', ARRAY['SPOTIFY.COM', 'SPOTIFY USA', 'SPOTIFY AB']),
('Amazon Prime', 'Subscriptions', 'Membership', ARRAY['AMAZON PRIME', 'AMZN PRIME', 'PRIME VIDEO']),
('Disney+', 'Subscriptions', 'Streaming', ARRAY['DISNEYPLUS', 'DISNEY PLUS', 'DISNEY+']),
('Hulu', 'Subscriptions', 'Streaming', ARRAY['HULU.COM', 'HULU LLC']),
('Apple iCloud', 'Subscriptions', 'Cloud Storage', ARRAY['APPLE.COM/BILL', 'ICLOUD STORAGE', 'APPLE ICLOUD']),
('YouTube Premium', 'Subscriptions', 'Streaming', ARRAY['YOUTUBE PREMIUM', 'GOOGLE YOUTUBE', 'YT PREMIUM']),

-- Airlines
('Delta Airlines', 'Travel-Air', 'Airlines', ARRAY['DELTA AIR', 'DELTA.COM', 'DL DELTA']),
('United Airlines', 'Travel-Air', 'Airlines', ARRAY['UNITED AIR', 'UNITED.COM', 'UA UNITED']),
('Southwest Airlines', 'Travel-Air', 'Airlines', ARRAY['SOUTHWEST AIR', 'SOUTHWEST.COM', 'WN SOUTHWEST']),
('American Airlines', 'Travel-Air', 'Airlines', ARRAY['AMERICAN AIR', 'AA.COM', 'AA AMERICAN']),

-- Hotels
('Marriott', 'Travel-Hotel', 'Hotel', ARRAY['MARRIOTT #', 'MARRIOTT HOTEL', 'MARRIOTT INTL']),
('Hilton', 'Travel-Hotel', 'Hotel', ARRAY['HILTON #', 'HILTON HOTEL', 'HILTON HOTELS']),
('Holiday Inn', 'Travel-Hotel', 'Hotel', ARRAY['HOLIDAY INN #', 'IHG HOLIDAY INN']),
('Hampton Inn', 'Travel-Hotel', 'Hotel', ARRAY['HAMPTON INN #', 'HAMPTON BY HILTON']),

-- Utilities & Services
('Alliant Energy', 'Utilities', 'Electric/Gas', ARRAY['ALLIANT ENERGY', 'ALLIANT PAYMENT']),
('Comcast Xfinity', 'Internet', 'ISP', ARRAY['COMCAST', 'XFINITY', 'COMCAST CABLE']),
('Verizon Wireless', 'Mobile', 'Wireless', ARRAY['VERIZON WIRELESS', 'VZWRLSS', 'VZW']),
('AT&T', 'Mobile', 'Wireless', ARRAY['ATT*', 'AT&T WIRELESS', 'ATT MOBILITY']),

-- Retail
('Amazon', 'Shopping', 'Online', ARRAY['AMAZON.COM', 'AMZN.COM/BILL', 'AMZN MKTP US', 'AMAZON MKTPLACE']),
('Home Depot', 'Shopping', 'Hardware', ARRAY['HOME DEPOT #', 'THE HOME DEPOT']),
('Lowes', 'Shopping', 'Hardware', ARRAY['LOWES #', 'LOWE''S']),

-- Healthcare
('CVS Pharmacy', 'Healthcare', 'Pharmacy', ARRAY['CVS/PHARMACY #', 'CVS #', 'CVS STORE']),
('Walgreens', 'Healthcare', 'Pharmacy', ARRAY['WALGREENS #', 'WAG #']),

-- Fitness
('Planet Fitness', 'Subscriptions', 'Fitness', ARRAY['PLANET FITNESS', 'PLANET FIT', 'PF BLACK CARD']),
('LA Fitness', 'Subscriptions', 'Fitness', ARRAY['LA FITNESS', 'LAF']),

-- Pet Care
('PetSmart', 'Pets', 'Pet Supplies', ARRAY['PETSMART #', 'PETSMART STORE']),
('Banfield Pet Hospital', 'Pets', 'Veterinary', ARRAY['BANFIELD #', 'BANFIELD VET']);
