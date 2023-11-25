# Configuring VPN Connectivity between Google Cloud and AWS

See [Challenge Lab](https://partner.cloudskillsboost.google/focuses/60967?parent=catalog){:target="_blank"}

# Challenge

You've been asked to:

1. TBC

# My Solution

I prefer to use the Cloud Shell and gcloud CLI, because it makes the steps much more repeatable.

## Prep

Let's start by defining some variables we can use throughout this challenge. Run the following from the Cloud Shell:

```bash
gcloud auth list

# Network
prj=<enter-your-project> # use your own project ID
region=us-central1
vpc_name=cymbal-privatenet
subnet_name=cymbal-privatenet-us
subnet_ip_range=10.0.0.0/24
nat_router=cymbal-nat-router
nat_gateway=cymbal-nat-config

# IAP firewall rule
fw_rule_iap=cymbal-privatenet-allow-iap-ssh
iap_src_range=35.235.240.0/20 # standard IAP range

# private instance
instance_name=cymbal-vm-internal
zone=us-central1-c
mach_type=e2-micro

# setting defaults
gcloud config set project $prj  
gcloud config set compute/region $region
gcloud config set compute/zone $zone
```

Substitute for any variables you've been given.

## TBC
