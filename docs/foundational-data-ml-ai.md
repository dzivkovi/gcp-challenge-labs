# Perform Foundational Data, ML, and AI Tasks in Google Cloud

See [Challenge Lab](https://partner.cloudskillsboost.google/focuses/13318?parent=catalog)

# Objective

This lab is in three parts:

1. [Create a simple DataFlow job](#create-a-simple-dataflow-job)
1. [Create a simple Dataproc job](#create-a-simple-dataproc-job)
1. [Create a simple Dataprep job](#create-a-simple-dataprep-job)
1. [Perform one of the three Google machine learning backed API tasks](#perform-one-of-the-three-google-machine-learning-backed-api-tasks)

If done efficiently, you can probably complete this whole lab in about 20 minutes.

## Setup

First, let's define some variables we can use throughout this challenge.  In Cloud Shell:

```bash
export PROJECT_ID=<what the lab tells you>
export BUCKET_NAME=<whatever the lab tells you>
export lab=<what the lab tells you>
export region=<what the lab tells you>
export machine_type=e2-standard-2
```

## Create a simple DataFlow job

### Objectives

We need to ingest a csv file, and process the data into BigQuery, using a Dataflow template. Dataflow requires Google Cloud Storage for temporary data.

### My Solution

First, we create a three node cluster, using the required machine type for our nodes.  Note that this takes a couple of minutes to run.

It's crucial to get your storagea and BigQuery regions right!

In Cloud Shell: 

```bash
bq --location=$region mk $lab
gsutil mb -l $region gs://$BUCKET_NAME/
```

Now we can simply create the Dataflow job from the Console:

1. Console --> Dataflow
1. Create Job from Template
1. Enter the job parameters from the lab
1. Run the job.

That's it!  You can monitor the job progress in the Dataflow page.  It takes a couple of minutes to run.

## Create a simple Dataproc job

### Objectives

We're asked to create a Dataproc cluster with some specific configuration settings.  Once the cluster is created, we need to SSH onto one of the clusters nodes, and from there, copy the input text from GCS to the HDFS storage of the Dataproc cluster itself. We then need to run a Spark job that we've been given.

### My Solution

In Cloud Shell:

```bash
gcloud config set dataproc/region $region
gcloud dataproc clusters create my-cluster \
  --worker-machine-type=$machine_type \
  --num-workers=2 \
  --worker-boot-disk-size 500
```

This creates a cluster with two workers, using the specified machine type.  It takes a couple of minutes for the cluster to be created. Once it has been created, open the Compute Engine page, and from there, SSH onto one of the worker machines in the cluster.

From the SSH session:

```bash
hdfs dfs -cp gs://cloud-training/gsp323/data.txt /data.txt
```

Now, back in Cloud Shell:

```bash
gcloud dataproc jobs submit spark --cluster my-cluster \
  --class org.apache.spark.examples.SparkPageRank \
  --max-failures-per-hour=1 \
  --jars file:///usr/lib/spark/examples/jars/spark-examples.jar -- /data.txt
```

This runs a Spark job with a main class of `org.apache.spark.examples.SparkPageRank`, with the specified jar location, with max retries set to `1`, and with the final parameter of `/data.txt`, which is read from HDFS.

It runs and completes pretty quickly.

## Create a simple Dataprep job

### Objectives

Here we're going to do some simple data wrangling of an input csv file, using Dataprep.

### My Solution

This is all done through the Console.

1. Launch Dataprep.  Accept all the prompts.
1. Select `New Flow`.
1. Import data --> Cloud Storage --> Edit path: `gs://cloud-training`
1. Now search for the folder you've been given, e.g. `gsp323`.
1. Find the `runs.csv` file and select it.
1. Import and add to flow.

Name the flow.  E.g. `Lab Runs`.  (What you call it doesn't matter.)

Now we'll edit the recipe:

1. runs --> Edit recipe
1. Select the column that contains the _state_, and select the taller column that represents `SUCCESS`. `Keep rows` --> Add.
1. Add step --> Filter contains --> Condition=contains, column=9, pattern to match=`/(^0$|^0\.0$)/` --> Delete macthing rows.
1. Finally, let's rename all the columns as requested, by selecting `New step` and then entering the following:

```text
rename type: manual mapping: [column2,'runid'],[column3,'userid'],[column4,'labid'],[column5,'lab_title'],[column6,'start'],[column7,'end'],[column8,'time'],[column9,'score'],[column10,'state']
```

Finally, **Run** the job, and run it with Dataflow.

It takes a couple of minutes.

## Perform one of the three Google machine learning backed API tasks

### Objectives

You can do any of the three ML API tasks.  But here, I've gone with the **Natural Language API** task. For this task, we need to analyse the text:

_"Old Norse texts portray Odin as one-eyed and long-bearded, frequently wielding a spear named Gungnir and wearing a cloak and a broad hat."_

### My Solution

We need to create a service account, obtain its key file, give the service the _storage.admin_ role:

```bash
gcloud iam service-accounts create lab-svc

# create service account key file, replacing the project name below
gcloud iam service-accounts keys create key.json --iam-account lab-svc@$PROJECT_ID.iam.gserviceaccount.com

# Add storage admin
gcloud projects add-iam-policy-binding $PROJECT_ID --member=serviceAccount:lab-svc@$PROJECT_ID.iam.gserviceaccount.com --role=roles/storage.admin

export GOOGLE_APPLICATION_CREDENTIALS="/home/$USER/key.json"

# authenticate (activate) the service account
gcloud auth activate-service-account --key-file key.json
```

Now we can call the API:

```bash
gcloud ml language analyze-entities --content="Old Norse texts portray Odin as one-eyed and long-bearded, frequently wielding a spear named Gungnir and wearing a cloak and a broad hat." > result.json
```

Finally, we need to copy the result file to the specified bucket, in order for the lab to validate.  Your required file name might be different.

```bash
gsutil cp result.json gs://$PROJECT_ID-marking/task4-cnl-907.result
```