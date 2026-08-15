-- Extract closing market prices
SELECT 
    instrument_id,
    price_date,
    close_price,
    source
FROM fct_market_prices;
