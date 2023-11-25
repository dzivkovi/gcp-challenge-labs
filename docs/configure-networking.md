# Configure Google Cloud Networking

See [Challenge Lab](https://www.cloudskillsboost.google/focuses/60966?parent=catalog){:target="_blank"}

# Challenge

You've been asked to:

1. [Create a VPC network](#create-a-vpc-network)
1. [Create a Firewall rule](#create-a-firewall-rule)
1. [Create the VM instance with no public IP address](#create-the-vm-instance-with-no-public-ip-address)
1. [Connect to cymbal-vm-internal via SSH to test the IAP tunnel](#connect-to-cymbal-vm-internal-via-ssh-to-test-the-iap-tunnel)
1. [Enable Private Google Access](#enable-private-google-access)
1. [Enable VPC Flow logs](#enable-vpc-flow-logs)
1. [Create a Cloud NAT gateway](#create-a-cloud-nat-gateway)
1. [Verify the Cloud NAT gateway](#verify-the-cloud-nat-gateway)

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

## Create a VPC network

Remember: don't enable Google private access yet.

```bash
gcloud compute networks create $vpc_name --subnet-mode=custom
gcloud compute networks subnets create $subnet_name \
  --range=$subnet_ip_range --stack-type=IPV4_ONLY \
  --network=$vpc_name --region=$region
```
 
## Create a Firewall rule

Here we define a firewall rule to allow ingress from the IAP proxies to machines in our network. 
When tunnelling SSH over IAP, the IAP proxies connect to the instance's internal IP address.

Guidance for SSH over IAP can be found [here](https://cloud.google.com/iap/docs/using-tcp-forwarding){:target="_blank"}

```bash
gcloud compute firewall-rules create $fw_rule_iap --network $vpc_name \
  --direction=INGRESS --allow tcp:22 --source-ranges="$iap_src_range"
```

## Create the VM instance with no public IP address

```bash
gcloud compute instances create $instance_name \
  --network=$vpc_name --subnet=$subnet_name \
  --machine-type=$mach_type --image-project=debian-cloud --image-family=debian-11 \
  --no-address
```

Note, if we wanted, we could also enable `OS Login` to control access to the instances using IAM permissions. In this case, we would do the following:

```bash
# First when creating the instance, add this flag:
# --metadata enable-oslogin=true

# Then assign OS Login IAM roles to our user
gcloud projects add-iam-policy-binding $prj \
    --member=user:EMAIL \
    --role=roles/compute.osLogin
```

Check in the console that your instance has no external IP address.

## Connect to cymbal-vm-internal via SSH to test the IAP tunnel

Now we use SSH to connect to the VM, tunnelling SSH over IAP. Whenever a VM does not have an external IP address (like our VM), then `gcloud compute ssh` automatically tunnels over IAP. But regardless, we can explicitly specify that the connection uses the IAP tunnel by specifying `--tunnel-through-iap`.

If our user did not have permission to use IAP to access our instances, then we could add the roles defined below. However, in this lab, our user already has necessary permission.

```bash
# grant roles for IAP TCP forwarding and SSH access
gcloud projects add-iam-policy-binding $prj \
    --member=user:EMAIL \
    --role=roles/iap.tunnelResourceAccessor

gcloud projects add-iam-policy-binding $prj \
    --member=user:EMAIL \
    --role=roles/compute.instanceAdmin.v1
```

Now let's actually connect with SSH: 

```bash
gcloud compute ssh $instance_name --tunnel-through-iap
```

If you use a passphrase for your SSH connection, make a note of it. Once we've checked the connectivity works, you can `exit` from the SSH session.

## Enable Private Google Access

Now we enable Private Google Access. This allows VM instances without external IP addresses to reach public Google APIs and services, through the VPC's default internet gateway. Private Google Access is enabled at the subnet level.

Back in Cloud Shell:

```bash
gcloud compute networks subnets update $subnet_name \
  --region=$region --enable-private-ip-google-access

# You can verify with this
gcloud compute networks subnets describe $subnet_name \
  --region=$region --format="get(privateIpGoogleAccess)"
```

## Enable VPC Flow logs

VPC Flow logs record a sample of network flows sent from and received by VM instances. VPC flow logs are also configured at subnet level.

```bash
gcloud compute networks subnets update $subnet_name \
  --region=$region --enable-flow-logs
```

## Create a Cloud NAT gateway

Although our instance can now access Google APIs and services, it still can't access resources on the Internet.  We can enable outbound access from our VM - even though it has no external IP address - by using Cloud NAT.

```bash
# First, we need to create a Cloud Router
gcloud compute routers create $nat_router \
  --project=$prj --network=$vpc_name --region=$region  

# Then we can create the NAT Gateway
gcloud compute routers nats create $nat_gateway \
  --region=$region --router=$nat_router \
  --auto-allocate-nat-external-ips --nat-all-subnet-ip-ranges \
  --enable-logging
```

## Verify the Cloud NAT gateway

Finally, we can test that our instance has Internet connectivity. Once again, connect using SSH over IAP.

And then, from the SSH session:

```bash
sudo apt-get update
```

The update should run fine.

And we're done!