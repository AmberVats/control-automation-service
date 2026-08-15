-- Extract valid active instruments master
SELECT 
    instrument_id,
    ticker,
    asset_class,
    ccy,
    status
FROM dim_instruments
WHERE status = 'ACTIVE';
