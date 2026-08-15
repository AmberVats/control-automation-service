"""
Demo data seeder for Control Automation Service.
Populates local database with realistic positions, trades, prices, and instruments
including deliberate anomalies for control verification.
"""
from sqlalchemy import create_engine, text
from src.db.session import DATABASE_URL, init_db

def seed_demo_data(db_url=None):
    url = db_url or DATABASE_URL
    engine = create_engine(url)
    init_db(engine)

    with engine.connect() as conn:
        # Create staging / source mock tables
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS fct_risk_position (
            as_of_date TEXT,
            instrument_id TEXT,
            book TEXT,
            quantity REAL,
            market_value REAL
        );
        """))

        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS fct_books_position (
            as_of_date TEXT,
            instrument_id TEXT,
            book TEXT,
            quantity REAL,
            market_value REAL
        );
        """))

        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS dim_instruments (
            instrument_id TEXT PRIMARY KEY,
            ticker TEXT,
            asset_class TEXT,
            ccy TEXT,
            status TEXT
        );
        """))

        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS fct_trades (
            trade_id TEXT PRIMARY KEY,
            instrument_id TEXT,
            book TEXT,
            trader TEXT,
            side TEXT,
            quantity REAL,
            price REAL,
            trade_date TEXT,
            settle_date TEXT
        );
        """))

        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS fct_market_prices (
            instrument_id TEXT,
            price_date TEXT,
            close_price REAL,
            source TEXT
        );
        """))

        # Clear existing demo data
        conn.execute(text("DELETE FROM fct_risk_position"))
        conn.execute(text("DELETE FROM fct_books_position"))
        conn.execute(text("DELETE FROM dim_instruments"))
        conn.execute(text("DELETE FROM fct_trades"))
        conn.execute(text("DELETE FROM fct_market_prices"))

        # 1. Seed Instruments
        conn.execute(text("""
        INSERT INTO dim_instruments (instrument_id, ticker, asset_class, ccy, status) VALUES
        ('EQ_AAPL', 'AAPL', 'EQUITY', 'USD', 'ACTIVE'),
        ('EQ_MSFT', 'MSFT', 'EQUITY', 'USD', 'ACTIVE'),
        ('EQ_GOOG', 'GOOG', 'EQUITY', 'USD', 'ACTIVE'),
        ('BND_UK10Y', 'UK10Y', 'RATES', 'GBP', 'ACTIVE'),
        ('FX_EURUSD', 'EURUSD', 'FX', 'USD', 'ACTIVE');
        """))

        # 2. Seed Positions (Risk System vs Books & Records)
        # Note: AAPL matches; MSFT has a $120 break (> $50 tolerance); GOOG is missing from Books (break)
        conn.execute(text("""
        INSERT INTO fct_risk_position (as_of_date, instrument_id, book, quantity, market_value) VALUES
        ('2026-08-15', 'EQ_AAPL', 'GLOBAL_EQ', 5000, 750000.00),
        ('2026-08-15', 'EQ_MSFT', 'GLOBAL_EQ', 3000, 960120.00),
        ('2026-08-15', 'EQ_GOOG', 'GLOBAL_EQ', 1500, 240000.00);
        """))

        conn.execute(text("""
        INSERT INTO fct_books_position (as_of_date, instrument_id, book, quantity, market_value) VALUES
        ('2026-08-15', 'EQ_AAPL', 'GLOBAL_EQ', 5000, 750000.00),
        ('2026-08-15', 'EQ_MSFT', 'GLOBAL_EQ', 3000, 960000.00),
        ('2026-08-15', 'BND_UK10Y', 'RATES_DESK', 100000, 98500.00);
        """))

        # 3. Seed Trades (includes one with missing trader and one with invalid instrument)
        conn.execute(text("""
        INSERT INTO fct_trades (trade_id, instrument_id, book, trader, side, quantity, price, trade_date, settle_date) VALUES
        ('TRD_001', 'EQ_AAPL', 'GLOBAL_EQ', 'J_DOE', 'BUY', 500, 150.25, '2026-08-15', '2026-08-17'),
        ('TRD_002', 'EQ_MSFT', 'GLOBAL_EQ', 'A_SMITH', 'SELL', 200, 320.00, '2026-08-15', '2026-08-17'),
        ('TRD_003', 'EQ_INVALID_XYZ', 'GLOBAL_EQ', 'J_DOE', 'BUY', 100, 50.00, '2026-08-15', '2026-08-17');
        """))

        # 4. Seed Market Prices (includes 1 stale price from 2026-08-10)
        conn.execute(text("""
        INSERT INTO fct_market_prices (instrument_id, price_date, close_price, source) VALUES
        ('EQ_AAPL', '2026-08-15', 150.25, 'BLOOMBERG'),
        ('EQ_MSFT', '2026-08-15', 320.00, 'BLOOMBERG'),
        ('EQ_GOOG', '2026-08-10', 160.00, 'REUTERS');
        """))

        conn.commit()
        print("Demo database seeded successfully with mock financial tables.")

if __name__ == "__main__":
    seed_demo_data()
