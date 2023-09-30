# Monitor and Log with Google Cloud Operations Suite

See [Challenge Lab](https://www.cloudskillsboost.google//course_sessions/5101003/labs/408319){:target="_blank"}

# Challenge

We're told that we have a Cloud Function that is responsible for subscriber video file upload and subsequent transcoding. We need to make use of Google Cloud Operations to provide insight around use of this Function. 

In this lab, we're going to:

- Initialize Cloud Monitoring.
- Configure a Compute Engine application for Cloud Operations Monitoring custom metrics.
- Create a custom metric using Cloud Operations logging events.
- Add custom metrics to a Cloud Monitoring Dashboard.
- Create a Cloud Operations alert.

# General Guidance

We're given some tips. We're told that:

1. The startup script for the Compute Instance is in the Compute Instance metadata key called startup_script.
2. The Compute Instance must have the Cloud Monitoring agent installed and the Go application requires environment variables to be configured with the Google Cloud project, the instance ID, and the compute engine zone.
1. The Video Queue length monitoring Go application writes the queue length metric data to a metric called custom.googleapis.com/opencensus/my.videoservice.org/measure/input_queue_size associated with the gce_instance resource type.
1. To create the custom log based metric, the easiest filter to use is the advanced filter query textPayload=~"file_format\: ([4,8]K).*". That is a regular expression that matches all Cloud Operations events for the two high resolution video formats you are interested in. You can use the same regular expression and configure labels in the metric definition, which creates a separate time series for each of the two high resolution formats.
1. You must use the name provided for the custom log based metric that monitors the rate at which high resolution videos are processed: Custom Metric Name.

# My Solution

As usual, I'll start by defining some variables we can use throughout this challenge:

```bash
gcloud auth list

region=ENTER REGION
zone=ENTER ZONE
prj=ENTER PRJ ID
```

## Task 1 - Configure Cloud Monitoring

## Task 2 - Configure a Compute Instance to generate Custom Cloud Monitoring metrics

## Task 3 - Create a custom metric using Cloud Operations logging events

## Task 4 - Add custom metrics to the Media Dashboard in Cloud Operations Monitoring

## Task 5 - Create a Cloud Operations alert based on the rate of high resolution video file uploads


And we're done!