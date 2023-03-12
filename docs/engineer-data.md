# Engineer Data in Google Cloud

See [Challenge Lab](https://partner.cloudskillsboost.google/focuses/13335?parent=catalog){:target="_blank"}

## Overview

_"You have started a new role as a Data Engineer for TaxiCab Inc. You are expected to import some historical data to a working BigQuery dataset, and build a basic model that predicts fares based on information available when a new ride starts. Leadership is interested in building an app and estimating for users how much a ride will cost. The source data will be provided in your project."_

What we already know:

- We have been provided with a dataset called `taxirides`, with imported historical data in the table `historical_taxi_rides_raw`. We will **explore** this data, and use it to **train our mode**.
- We are also given another table: `taxirides.report_prediction_data`. **We will be applying our model against this data to make predictions.**  Consequently, we need to be mindful that our model can only be built using fields that are present in `report_prediction_data`, or using fields that can be calculated using data in this table.

## Objectives Overview

1. [Setup](#setup)
1. [Explore](#explore-the-data)
1. [Clean The Data](#clean-the-data)
1. [Create the Model](#create-the-model)
1. [Evaluate the Model](#evaluate-the-model)
1. [Make Predictions](#make-predictions)

## Setup

We are provided with a number of variables that we should make a note of.  Your data will look differnet.  But for the purposes of this page, these are the values I'm using:

|Variable|Value|Notes|
|--------|-----|-----|
|Project ID|qwiklabs-gcp-04-529175540efd|The project we will work in, and where our dataset lives|
|table|taxi_training_data_388|The name of the _cleaned_ data table we need to create| 
|Fare Amount|fare_amount_797|The name of the _label_ for our model|
|Number|2|A value that we will use in some of our queries|
|Example Value|$3.0|Another value that we will use in some of our queries|
|Model name|fare_model_926|The name we need to give to our model|

## Explore the Data

Let's first examine the data:

```sql
WITH 
  daynames AS
    (SELECT ['Sun', 'Mon', 'Tues', 'Wed', 'Thurs', 'Fri', 'Sat'] AS daysofweek),
  taxitrips AS (
    SELECT
      (tolls_amount + fare_amount) AS fare_amount_797,
      daysofweek[ORDINAL(EXTRACT(DAYOFWEEK FROM pickup_datetime))] AS dayofweek,
      EXTRACT(HOUR FROM pickup_datetime) AS hourofday,
      pickup_longitude AS pickuplon,
      pickup_latitude AS pickuplat,
      dropoff_longitude AS dropofflon,
      dropoff_latitude AS dropofflat,
      trip_distance,
      passenger_count AS passengers
    FROM `taxirides.historical_taxi_rides_raw`, daynames
  )
  SELECT *
  FROM taxitrips
```

Notes about this query:

- We add up `tolls_amount` and `fare_amount`, and return the sum as `fare_amount_797`. This is the value we will want to predict with our model; i.e. it is the _label_.
- We are dynamically creating a table called `taxitrips` by joining the `taxirides.historical_taxi_rides_raw` table with `daynames`.

The results look something like this:

<img src="{{'/assets/images/exploring_historical_taxi_rides.png' | relative_url }}" alt="Exploring Historical Taxi Rides Table" style="width:640px;" />

## Clean the Data

We need to clean the data in order to create our model. There are many ways we could do this.  One good option is to visually clean the data using _Dataprep_, and then execute the clean using a Dataprep-generated Dataflow pipeline.

But personally, I think it's easy enough to clean the data using SQL, and generate the new table directly using this SQL.

Here's my guidance:

- You need to save the cleaned data in a new table, with the name we were given. This will be the _training data_ for our model.
- Thus, we need to include the _features_ we want to test in our model. The trick here is that we want our model features to ideally have the same field names as the test data we will test the model on later.  So it makes sense to make the field names look the same as the prediction time data.
- These are the features I wanted to test:
  - Hour of Day
  - Pick up address
  - Drop off address
  - Distance
  - Number of passengers

- However, although `distance` is a field in our historical data, it is not a field present in our `report_prediction_data`.  So, we can't just use `distance`.  But, as strongly hinted by the lab instructions, we can _calculate_ distance using the _geo_ functions.
- We need to follow the rules given in the lab.  For me, these rules include:
  - Only include data where `trip_distance` is greater than the supplied value (i.e. `2`).
  - Only include data where `passenger_count` is greater than the supplied value (i.e. `2`).
  - Only include data where `fare_amount` is greater than the supplied value (i.e. `$3`).
  - Remove fields with unreasonable geometric coordinates.
  - Ensure the number of rows in the cleaned data is under 1 million. (The source data has over 1 billion rows.)

Let's start by doing this:

```sql
WITH 
  daynames AS (
    SELECT ['Sun', 'Mon', 'Tues', 'Wed', 'Thurs', 'Fri', 'Sat'] AS daysofweek
  ),
  taxitrips AS (
    SELECT
      (tolls_amount + fare_amount) AS fare_amount_797,
      daysofweek[ORDINAL(EXTRACT(DAYOFWEEK FROM pickup_datetime))] AS dayofweek,
      EXTRACT(HOUR FROM pickup_datetime) AS hourofday,
      pickup_longitude AS pickuplon,
      pickup_latitude AS pickuplat,
      dropoff_longitude AS dropofflon,
      dropoff_latitude AS dropofflat,
      trip_distance,
      passenger_count AS passengers
    FROM `taxirides.historical_taxi_rides_raw`, daynames
    WHERE
      trip_distance > 2 AND
      passenger_count > 2 AND
      fare_amount >= 3 AND
      ABS(pickup_longitude) <= 90 AND pickup_longitude != 0 AND
      ABS(pickup_latitude) <= 90 AND pickup_latitude != 0 AND
      ABS(dropoff_longitude) <= 90 AND dropoff_longitude != 0 AND
      ABS(dropoff_latitude) <= 90 AND dropoff_latitude != 0       
  )
  SELECT * FROM taxitrips
```

This is a good start.  It filters according to the rules, removes a few unusual pickup and dropoff coordinates, and ultimately reduces the record count from over 1 billion to about 72 million. But we need to get to under 1 million.  So here's a cool trick:

```sql
WITH 
  params AS (
    SELECT
      1 AS TRAIN,
      2 AS EVAL
  ),
  daynames AS (
    SELECT ['Sun', 'Mon', 'Tues', 'Wed', 'Thurs', 'Fri', 'Sat'] AS daysofweek
  ),
  taxitrips AS (
    SELECT
      (tolls_amount + fare_amount) AS fare_amount_797,
      daysofweek[ORDINAL(EXTRACT(DAYOFWEEK FROM pickup_datetime))] AS dayofweek,
      EXTRACT(HOUR FROM pickup_datetime) AS hourofday,
      pickup_longitude AS pickuplon,
      pickup_latitude AS pickuplat,
      dropoff_longitude AS dropofflon,
      dropoff_latitude AS dropofflat,
      trip_distance,
      passenger_count AS passengers
    FROM `taxirides.historical_taxi_rides_raw`, daynames, params
    WHERE
      MOD(ABS(FARM_FINGERPRINT(CAST(pickup_datetime AS STRING))), 150) 
        IN (params.TRAIN, params.EVAL) AND
      trip_distance > 2 AND
      passenger_count > 2 AND
      fare_amount >= 3 AND
      ABS(pickup_longitude) <= 90 AND pickup_longitude != 0 AND
      ABS(pickup_latitude) <= 90 AND pickup_latitude != 0 AND
      ABS(dropoff_longitude) <= 90 AND dropoff_longitude != 0 AND
      ABS(dropoff_latitude) <= 90 AND dropoff_latitude != 0       
  )
  SELECT * FROM taxitrips
```

In this new query, we've converted the timestamp to a unique number, and then we apply a `mod` function to this number, using `mod 150`. If the result is `1` or `2`, then we keep the row.  Thus, we are ultimately reducing the size of the data 75-fold, which gets us to under 1 million.

Of course, we could have achieved the same reduction just with `mod 75`.  But by creating these two enumerated constants - `params.TRAIN` and `params.EVAL`, we have the ability to reuse this query to return half the data has training data, and the other half as evaluation data. We might not use this, but it's good to be able to.

However, we still have a problem. We're stil generating our cleaned data using `trip_distance`, but this field won't be available to us in our test data.  So instead, we need to calculate distance. We can do it like this:

```sql
CREATE OR REPLACE TABLE taxirides.taxi_training_data_388 AS
WITH 
  params AS (
    SELECT
      1 AS TRAIN,
      2 AS EVAL
  ),
  daynames AS
    (SELECT ['Sun', 'Mon', 'Tues', 'Wed', 'Thurs', 'Fri', 'Sat'] AS daysofweek),
  taxitrips AS (
    SELECT
      (tolls_amount + fare_amount) AS fare_amount_797,
      pickup_datetime,
      daysofweek[ORDINAL(EXTRACT(DAYOFWEEK FROM pickup_datetime))] AS dayofweek,
      EXTRACT(HOUR FROM pickup_datetime) AS hourofday,
      pickup_longitude AS pickuplon,
      pickup_latitude AS pickuplat,
      dropoff_longitude AS dropofflon,
      dropoff_latitude AS dropofflat,
      ST_Distance(ST_GeogPoint(pickup_longitude, pickup_latitude), 
                  ST_GeogPoint(dropoff_longitude, dropoff_latitude)) AS trip_distance,
      passenger_count AS passengers
    FROM `taxirides.historical_taxi_rides_raw`, daynames, params
    WHERE
      MOD(ABS(FARM_FINGERPRINT(CAST(pickup_datetime AS STRING))),150) 
        IN (params.TRAIN, params.EVAL) AND   
      trip_distance > 2 AND
      passenger_count > 2 AND
      fare_amount > 3 AND
      ABS(pickup_longitude) <= 90 AND pickup_longitude != 0 AND
      ABS(pickup_latitude) <= 90 AND pickup_latitude != 0 AND
      ABS(dropoff_longitude) <= 90 AND dropoff_longitude != 0 AND
      ABS(dropoff_latitude) <= 90 AND dropoff_latitude != 0 AND 
      ST_Distance(ST_GeogPoint(pickup_longitude, pickup_latitude), 
                  ST_GeogPoint(dropoff_longitude, dropoff_latitude)) > 2     
  )
  SELECT * FROM taxitrips
```

Notes about the above query:

- We're now calculating `trip_distance`, from pickup and dropoff locations.
- In the `WHERE` clause, I'm including only rows where both the `historical_taxi_rides_raw.trip_distance` and the calculated `trip_distance` are `> 2`.
- Finally, I'm storing the results in a new table, with the name required.

Here's the schema of the new table:

<img src="{{'/assets/images/taxi-training-cleaned-schema.png' | relative_url }}" alt="Cleaned Data Schema" style="width:640px;" />

And here's what its data looks like:

<img src="{{'/assets/images/taxi-training-cleaned.png' | relative_url }}" alt="Cleaned Data" style="width:640px;" />

## Create the Model

Now we're ready to create the model.

Since we've already got the cleaned data in a new table, we can simply use that data to create the model. We're trying to predict numeric values, rather than make boolean predictions.  So it makes sense to create a _linear regression_ model using BigQuery ML.

```sql
CREATE or REPLACE MODEL taxirides.fare_model_926
OPTIONS
  (model_type='linear_reg', labels=['fare_amount_797']) AS
WITH
  params AS (
    SELECT
      0 AS TRAIN,
      1 AS EVAL
  ),
  training_data AS (
    SELECT * EXCEPT(pickup_datetime, TRAIN, EVAL)
    FROM `taxirides.taxi_training_data_388`, params
    WHERE 
      MOD(ABS(FARM_FINGERPRINT(CAST(pickup_datetime AS STRING))), 2) = params.TRAIN
  )
  SELECT * FROM training_data 
```

Note how I'm still using the `params` enumeration.  But when building the model, I'm only using half the data; i.e. the half where `mod 2 == 0`.

The model takes a couple of minutes to build.  If we then open the model and click on the _Evaluate_ tab:

<img src="{{'/assets/images/taxi_fare_model.png' | relative_url }}" alt="Taxi Fare Model" style="width:640px;" />

## Evaluate the Model

We're told that our model needs have RMSE (Root Mean Squared Error) of less than 10. Clearly, we've already achieved this goal, as seen from the screenshot above.  I.e. we have a `mean squared error` of just over 10; so the square root of this value is going to be a little over 3. But let's run a query, to be sure:

```sql
SELECT 
  *, 
  SQRT(mean_squared_error) as rmse
FROM ML.EVALUATE(MODEL taxirides.fare_model_926, (
WITH
  params AS (
    SELECT
      0 AS TRAIN,
      1 AS EVAL
  ),
  training_data AS (
    SELECT *
    FROM `taxirides.taxi_training_data_388`, params
    WHERE 
      MOD(ABS(FARM_FINGERPRINT(CAST(pickup_datetime AS STRING))), 2) = params.EVAL
  )
  SELECT * FROM training_data
))
```

You can see that this query is very similar to the query that I used to build the model.  But this time, I'm using _the other half_ of the training data to evaluate the model.

Here's the result:

<img src="{{'/assets/images/evaluate_taxi_model.png' | relative_url }}" alt="Evaluate Model" style="width:640px;" />

You can see that the RMSE is `3.4`. So this is good!  If our RMSE was over 10, we would have to do more feature engineering to refine our model.

## Make Predictions

Finally we're ready to predict _total fare_ for all the rows in our test data:

```sql
CREATE OR REPLACE TABLE taxirides.2015_fare_amount_predictions AS
SELECT * FROM ML.PREDICT(MODEL taxirides.fare_model_926, (
  WITH 
    daynames AS (
      SELECT ['Sun', 'Mon', 'Tues', 'Wed', 'Thurs', 'Fri', 'Sat'] AS daysofweek
    ),
    test_data AS (
      SELECT
        daysofweek[ORDINAL(EXTRACT(DAYOFWEEK FROM pickup_datetime))] AS dayofweek,
      EXTRACT(HOUR FROM pickup_datetime) AS hourofday,
        pickuplon,
        pickuplat,
        dropofflon,
        dropofflat,
        ST_Distance(ST_GeogPoint(pickuplon, pickuplat), 
                    ST_GeogPoint(dropofflon, dropofflat)) AS trip_distance,
        passengers
      FROM `taxirides.report_prediction_data`, daynames
    )
    SELECT * FROM test_data 
  )
)
```

In the query above we're applying the model to `report_prediction_data` table, and storing the results in a new table. 

The data looks like this:

<img src="{{'/assets/images/taxi-fare-predictions.png' | relative_url }}" alt="Predictions" style="width:640px;" />

And that's it. We're done!