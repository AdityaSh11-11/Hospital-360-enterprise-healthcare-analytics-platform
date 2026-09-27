INSERT INTO warehouse.dim_date
(
    date_key,
    full_date,
    day,
    day_name,
    week_of_year,
    month,
    month_name,
    quarter,
    year,
    is_weekend
)

SELECT

    TO_CHAR(d, 'YYYYMMDD')::INTEGER,

    d::DATE,

    EXTRACT(DAY FROM d)::INTEGER,

    TRIM(TO_CHAR(d, 'Day')),

    EXTRACT(WEEK FROM d)::INTEGER,

    EXTRACT(MONTH FROM d)::INTEGER,

    TRIM(TO_CHAR(d, 'Month')),

    EXTRACT(QUARTER FROM d)::INTEGER,

    EXTRACT(YEAR FROM d)::INTEGER,

    EXTRACT(ISODOW FROM d) IN (6, 7)

FROM generate_series(
    DATE '2020-01-01',
    DATE '2035-12-31',
    INTERVAL '1 day'
) AS d

ON CONFLICT (date_key)
DO NOTHING;