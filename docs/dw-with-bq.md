# Build and Optimise Data Warehouses with BigQuery

See [Challenge Lab](https://partner.cloudskillsboost.google/focuses/14827?parent=catalog){:target="_blank"}

## Overview

"You are part of an international public health organisation which is tasked with developing a machine learning model to predict the daily case count for countries during the Covid-19 pandemic. As a junior member of the Data Science team you've been assigned to use your data warehousing skills to develop a table containing the features for the machine learning model."

Topics tested:

- Use BigQuery to access public COVID and other demographic datasets.
- Create a new BigQuery dataset which will store your tables.
- Add a new date partitioned table to your dataset.
- Add new columns to this table with appropriate data types.
- Run a series of JOINS to populate these new columns with data drawn from other tables.

## Objectives Overview

1. [Create Date-Partitioned Table](#create-date-partitioned-table)
1. [Add Columns to the Schema](#add-columns-to-the-schema)
1. [Add Country Population Data](#add-country-population-data)
1. [Add Country Area Data](#add-country-area-data)
1. [Add Mobility Averages Data](#add-mobility-averages-data)
1. [Query Missing Data](#query-missing-data)

## Setup

First, make a note of your `dataset_name` and your `table_name`.  For this doc, I'll be using `covid_733` and `oxford_policy_tracker_360`, respectively.

Now, create your dataset.  I did this in the Cloud Console. I.e. `Create Data Set`, and call it `covid_733`. We can leave everything else with defaults. If you prefer, you could use `bq` from the command line.

## Create Date-Partitioned Table

We need to create our `oxford_policy_tracker_360` table, which should be a copy of the `bigquery-public-data.covid19_govt_response.oxford_policy_tracker`, but should be:

- Partitioned by date
- With expiry of 720 days
- And exclude certain regions.

This was my solution:

```sql
CREATE OR REPLACE TABLE covid_733.oxford_policy_tracker_360
PARTITION BY date
OPTIONS(
  partition_expiration_days=720,
  description="oxford_policy_tracker partitioned by date"
) AS
SELECT *
FROM `bigquery-public-data.covid19_govt_response.oxford_policy_tracker`
WHERE alpha_3_code NOT IN ("GBR", "BRA", "CAN", "USA")
```

It simply creates a new table, sets up partitioning, and defines/populates the table using the existing table.

You should end up with something that looks like this:

<img src="{{'/assets/images/partitioned_tracker.png' | relative_url }}" alt="Partitioned Tracker Table" style="width:500px;" />

## Add Columns to the Schema

We need to add a bunch of additional columns to our table. We're told what they are. The catch is that some of these columns (all of the columns with the `mobility` prefix) are part of a **RECORD**, which is represented using the `STRUCT` keyword.  Think of them like _sub-columns_.

Here's my solution:

```sql
ALTER TABLE covid_733.oxford_policy_tracker_360
  ADD COLUMN population    INTEGER,
  ADD COLUMN country_area  FLOAT64,
  ADD COLUMN mobility      STRUCT<
    avg_retail      FLOAT64,
    avg_grocery     FLOAT64,
    avg_parks       FLOAT64,
    avg_transit     FLOAT64,
    avg_workplace   FLOAT64,
    avg_residential FLOAT64>;
```

If you now refresh your table's schema and scroll to the end, you can see your new columns have been added:

<img src="{{'/assets/images/tracker_cols_added.png' | relative_url }}" alt="Columns Added" style="width:480px;" />

## Add Country Population Data

Now we need to add country data from a different table.  This is easy enough.  We just do an `UPDATE-SET-FROM`. Note that our table stores the 3-character country codes in the field called `alpha_3_code`, as is hinted by the supplied SQL in the lab.

```sql
# use 3-char country codes
UPDATE
    covid_733.oxford_policy_tracker_360 t0
SET
    t0.population  = t2.pop_data_2019
FROM
  (SELECT DISTINCT country_territory_code, pop_data_2019 
   FROM `bigquery-public-data.covid19_ecdc.covid_19_geographic_distribution_worldwide`
  ) AS t2
WHERE t0.alpha_3_code = t2.country_territory_code;
```

## Add Country Area Data

This is basically the same as the previous step, except we use a different source table for the country area data.  Also note that this source table does have a country code field, but using only two character codes.  This is no good, so we'll join on the full country name.

```sql
# The census_bureau_international table uses 2-char country codes, so we can't use that
UPDATE
    covid_733.oxford_policy_tracker_360 t0
SET
    t0.country_area = t2.country_area
FROM
  (SELECT DISTINCT country_name, country_area
   FROM `bigquery-public-data.census_bureau_international.country_names_area`
  ) AS t2
WHERE t0.country_name = t2.country_name;
```

## Add Mobility Averages Data

This one was slightly tricker.  I had to look up the syntax for this.

We're already given this query:

```sql
SELECT country_region, date,
      AVG(retail_and_recreation_percent_change_from_baseline) as avg_retail,
      AVG(grocery_and_pharmacy_percent_change_from_baseline)  as avg_grocery,
      AVG(parks_percent_change_from_baseline) as avg_parks,
      AVG(transit_stations_percent_change_from_baseline) as avg_transit,
      AVG( workplaces_percent_change_from_baseline ) as avg_workplace,
      AVG( residential_percent_change_from_baseline)  as avg_residential
FROM `bigquery-public-data.covid19_google_mobility.mobility_report`
GROUP BY country_region, date
```

This gives us averages for various values, each as a separate column.  Our rows are unique by a combination of country, and date.

We need to insert these values, joining on both country and date.  But when we update our target rows, we need to update our single _STRUCT_, using the six different averages that compose our RECORD.

I did it like this:

```sql
# We need to average a number of records per country and data,
# to get a single average of each child column in the mobility record
UPDATE
    covid_733.oxford_policy_tracker_360 t0
SET
    t0.mobility  = STRUCT(t2.avg_retail, 
                         t2.avg_grocery,
                         t2.avg_parks,
                         t2.avg_transit,
                         t2.avg_workplace,
                         t2.avg_residential)
FROM
  (SELECT country_region, date,
      AVG(retail_and_recreation_percent_change_from_baseline) as avg_retail,
      AVG(grocery_and_pharmacy_percent_change_from_baseline)  as avg_grocery,
      AVG(parks_percent_change_from_baseline) as avg_parks,
      AVG(transit_stations_percent_change_from_baseline) as avg_transit,
      AVG( workplaces_percent_change_from_baseline ) as avg_workplace,
      AVG( residential_percent_change_from_baseline)  as avg_residential
   FROM `bigquery-public-data.covid19_google_mobility.mobility_report`
   GROUP BY country_region, date
  ) AS t2
WHERE t0.country_name = t2.country_region
  AND t0.date = t2.date;
```

If you now refresh the preview of your table data and scroll to the far right, you'll see it looks something like this:

<img src="{{'/assets/images/mobility_data.png' | relative_url }}" alt="Mobility Data" style="width:640px;" />

## Query Missing Data

Finally, we're asked to look for missing data in our table.  Specifically:

- Countries that are missing population data
- Countries that are missing country area data

Where we're missing both, we should show the country twice.

So my strategy is:

- Look up all the distinct countries in the `country_names_area` table.
- Use this table as a left join, and join to our table.
- Join on where our table has a null value for `population`.
- Now, repeat these steps, but join on hwere our table has a null value for `country_area`.

At this point, we have results from two queries, and both are simply a list of country names.  Now we want to add them together, so we'll use `UNION ALL`.  We want to use the `ALL` option, since we don't want to exclude duplicates.

The final query looks like this:

```sql
# countries missing population information in the tracker
SELECT DISTINCT 
  countries.country_name
FROM `bigquery-public-data.census_bureau_international.country_names_area` AS countries
LEFT JOIN `covid_733.oxford_policy_tracker_360` AS tracker
ON countries.country_name = tracker.country_name
WHERE tracker.population IS NULL
UNION ALL
# countries missing country area information in the tracker
SELECT DISTINCT 
  countries.country_name
FROM `bigquery-public-data.census_bureau_international.country_names_area` AS countries
LEFT JOIN `covid_733.oxford_policy_tracker_360` AS tracker
ON countries.country_name = tracker.country_name
WHERE tracker.country_area IS NULL
ORDER BY country_name
```

That's it. Not so bad!