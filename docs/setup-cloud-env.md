# Set Up and Configure a Cloud Environment in Google Cloud

See [Challenge Lab](https://www.cloudskillsboost.google//course_sessions/5054365/labs/403518){:target="_blank"}

# Challenge

There's a lot to do here!  We're asked to:

- Create a development VPC with three subnets.
- Create a production VPC with three subnets.
- Create a bastion that is connected to both VPCs.
- Create a development Cloud SQL Instance and connect and prepare the WordPress environment.
- Create a Kubernetes cluster in the development VPC for WordPress.
- Prepare the Kubernetes cluster for the WordPress environment. 
- Create a WordPress deployment using the supplied configuration.
- Enable an uptime check in Cloud Monitoring.
- Provide access for an additional engineer.

You're given some standards to follow:

- Create all resources in the specified region and zone, unless otherwise directed.
- Naming is normally `team-resource`, e.g. an instance could be named `kraken-webserver1`
- Allocate cost effective resource sizes. Use compute machines of type `e2-medium` unless told otherwise.

# My Solution

Although the tasks are not particularly difficult, I found it quite challenging to get this done in time.  I finished it with about 16 seconds to spare!  Though, if I did it again, and followed the automation I built along the way, I'm sure I could do it much more quickly.  One of the challenges is that provisioning of Cloud SQL and of GKE takes quite a bit of time.

Okay, as usual, I try to automate with Cloud CLI as much as possible.  Of course, you can use the Console if you prefer.

## Prep

Let's start by defining some variables we can use throughout this challenge:

```bash
gcloud auth list

region=us-east1
zone=us-east1-b

# Dev network
vpc_dev=griffin-dev-vpc
sn_dev_wp=griffin-dev-wp
sn_dev_wp_cidr=192.168.16.0/20
sn_dev_mgmt=griffin-dev-mgmt
sn_dev_mgmt_cidr=192.168.32.0/20

# Prod network
vpc_prod=griffin-prod-vpc
sn_prod_wp=griffin-prod-wp
sn_prod_wp_cidr=192.168.48.0/20
sn_prod_mgmt=griffin-prod-mgmt
sn_prod_mgmt_cidr=192.168.64.0/20

# default machine size
mach=e2-medium

# Dev GKE cluster name
gke=griffin-dev

# The user we need to give access to.
user2=supply-your-user-email

gcloud config set compute/region $region
gcloud config set compute/zone $zone
```

Substitute for any variables you've been given, in your instance of the challenge.

## Setup the Networks

Here we have to create two networks: one for `Dev` and one for `Prod`. Both will contain two subnets.

```bash
# First, the Dev network
gcloud compute networks create $vpc_dev --subnet-mode=custom --mtu=1460 --bgp-routing-mode=regional
gcloud compute networks subnets create $sn_dev_wp \
  --range=$sn_dev_wp_cidr --stack-type=IPV4_ONLY \
  --network=$vpc_dev --region=$region
gcloud compute networks subnets create $sn_dev_mgmt \
  --range=$sn_dev_mgmt_cidr --stack-type=IPV4_ONLY \
  --network=$vpc_dev --region=$region

# Then the Prod network
gcloud compute networks create $vpc_prod --subnet-mode=custom --mtu=1460 --bgp-routing-mode=regional
gcloud compute networks subnets create $sn_prod_wp \
  --range=$sn_prod_wp_cidr --stack-type=IPV4_ONLY \
  --network=$vpc_prod --region=$region
gcloud compute networks subnets create $sn_prod_mgmt \
  --range=$sn_prod_mgmt_cidr --stack-type=IPV4_ONLY \
  --network=$vpc_prod --region=$region

# And firewall rules, so we can connect to our bastion
gcloud compute firewall-rules create fw-ssh-dev --network $vpc_dev --allow tcp:22,tcp:3389,icmp
gcloud compute firewall-rules create fw-ssh-prod --network $vpc_prod --allow tcp:22,tcp:3389,icmp
```

## Create the Bastion Host

The important thing to note is that this bastion host needs to connect to both VPCs.  So you need to configure two network interfaces.

```bash
gcloud compute instances create bastion \
  --project=$prj \
  --zone=$zone \
  --machine-type=$mach \
  --network-interface=network-tier=PREMIUM,stack-type=IPV4_ONLY,subnet=$sn_dev_mgmt \
  --network-interface=network-tier=PREMIUM,stack-type=IPV4_ONLY,subnet=$sn_prod_mgmt \
  --metadata=enable-oslogin=true \
  --scopes=https://www.googleapis.com/auth/devstorage.read_only,https://www.googleapis.com/auth/logging.write,https://www.googleapis.com/auth/monitoring.write,https://www.googleapis.com/auth/servicecontrol,https://www.googleapis.com/auth/service.management.readonly,https://www.googleapis.com/auth/trace.append
```

## Setup a CloudSQL MySQL Instance

First, I create a regional (highly available) Cloud SQL instance:

```bash
gcloud sql instances create griffin-dev-db \
  --database-version=MYSQL_8_0_31 \
  --tier=db-n1-standard-1 \
  --region=$region \
  --edition=enterprise \
  --root-password=<whatever!>

# Now connect to it (from Cloud Shell)
gcloud sql connect griffin-dev-db --user=root --quiet
```

Now we'll run some DB setup, as given in the instructions:

```sql
CREATE DATABASE wordpress;
CREATE USER "wp_user"@"%" IDENTIFIED BY "stormwind_rules";
GRANT ALL PRIVILEGES ON wordpress.* TO "wp_user"@"%";
FLUSH PRIVILEGES;
```

Finally, exit from the SQL client back to Cloud Shell:

```bash
exit
```

## Setup Google Kubernetes Engine (GKE)

We're told we need a 2-node zonal cluster, provisioned in the `dev` VPC.

```bash
gcloud container clusters create $gke \
  --network=$vpc_dev --subnetwork=$sn_dev_wp \
  --num-nodes=2 \
  --zone $zone \
  --machine-type=$mach \
  --scopes "https://www.googleapis.com/auth/projecthosting,storage-rw"
```

It takes about 5 minutes to provision the GKE cluster.

Now we need to download some pre-prepared `yaml` files. I create a clean directory to store these files:

```bash
mkdir wp && cd $_
gsutil cp gs://cloud-training/gsp321/wp-k8s/* .
```

Now we're told to edit `wp-env.yaml` and substitute the username and password provided, in the `Secret`.

So the final yaml looks like this:

```yaml
kind: PersistentVolumeClaim
apiVersion: v1
metadata:
  name: wordpress-volumeclaim
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 200Gi
---
apiVersion: v1
kind: Secret
metadata:
  name: database
type: Opaque
stringData:
  username: wp_user
  password: stormwind_rules
```

Then we need to generate a service account key and use it to create a Kubernetes secret for the Cloud SQL instance credentials. We're told how to do this:

```bash
gcloud iam service-accounts keys create key.json \
    --iam-account=cloud-sql-proxy@$GOOGLE_CLOUD_PROJECT.iam.gserviceaccount.com
kubectl create secret generic cloudsql-instance-credentials \
    --from-file key.json
```

Now we're ready to apply our `wp-env.yaml`, in order to create our PVC and secret:

```bash
kubectl apply -f wp-env.yaml
```

Next, we need to update `wp-deployment.yaml` and replace `YOUR_SQL_INSTANCE` with our instance connection name. It will be in the format `<project>:region:griffin-dev-db`.

Now we can create the `deployment` and the `service`:

```bash
kubectl apply -f wp-deployment.yaml
kubectl apply -f wp-service.yaml
```

You can check the status of the service and its associated load balancer creation:

```bash
kubectl get services
```

Here's a useful command for retrieving the external IP address of the newly created LB:

```bash
kubectl get svc wordpress -o=jsonpath="{.status.loadBalancer.ingress[0].ip}"
```

Fire up this IP address in the browser to check that WordPress is running.

I don't think you need to explicitly set up a firewall rule to access the LB, but just in case you do:

```bash
gcloud compute firewall-rules create wp-service-lb-fw \
  --direction=INGRESS \
  --network=$vpc_dev \
  --allow tcp:80 --source-ranges="0.0.0.0/0" \
  --destination-ranges="<enter-ip>/32"
```

## Setup an Uptime Check in Cloud Monitoring

We're told to create an uptime check. In the Console, navigate to Monitoring. Create an **Uptime Check**.  Configure it as follows:

- Check type: HTTP.
- Resource type: URL.
- Hostname: provide the LB external IP address.
- Path: `/`

And create.

## Grant Access to User 2

We're told that make User 2 an Editor of our project.

I do this by exporting the existing IAM policy, adding the new user to it, and then applying the new policy.

```bash
cd ..
gcloud projects get-iam-policy $prj --format=json > policy.json
```

Find the entry for `roles/editor`, and add a new member for your user 2, by adding the line `user:the-email-address`.

Now reapply:

```bash
gcloud projects set-iam-policy $prj policy.json
```

And we're done!