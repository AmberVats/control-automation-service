-- Extract EOD risk positions
SELECT 
    as_of_date,
    instrument_id,
    book,
    quantity,
    market_value
FROM fct_risk_position
WHERE as_of_date = '2026-08-15';
