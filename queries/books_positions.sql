-- Extract EOD books and records positions
SELECT 
    as_of_date,
    instrument_id,
    book,
    quantity,
    market_value
FROM fct_books_position
WHERE as_of_date = '2026-08-15';
