-- Extract daily trade blotter
SELECT 
    trade_id,
    instrument_id,
    book,
    trader,
    side,
    quantity,
    price,
    trade_date,
    settle_date
FROM fct_trades
WHERE trade_date = '2026-08-15';
