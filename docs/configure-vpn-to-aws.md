# Configuring VPN Connectivity between Google Cloud and AWS

See:

- [Challenge Lab](https://partner.cloudskillsboost.google/focuses/60967?parent=catalog){:target="_blank"}
- [Create HA VPN to AWS peer gateways](https://cloud.google.com/network-connectivity/docs/vpn/how-to/creating-ha-vpn#create_ha_vpn_to_aws_peer_gateways){:target="_blank"}

# Challenge

You've been asked to configure VPN connectivity between Google Cloud and AWS. The lab requires you to use both Google Cloud, and AWS. Credentials for both are provided in the lab.

The tasks are:

1. [Create the HA VPN gateway and Cloud Router on Google Cloud](#create-the-ha-vpn-gateway-and-cloud-router-on-google-cloud)
1. [Create an AWS Customer gateway and a Target gateway](#create-an-aws-customer-gateway-and-a-target-gateway)
1. [Create a VPN connection with dynamic routing on AWS](#create-a-vpn-connection-with-dynamic-routing-on-aws)
1. [Create an external peer VPN gateway and VPN tunnels on Google Cloud](#create-an-external-peer-vpn-gateway-and-vpn-tunnels-on-google-cloud)
1. [Add BGP peers to the Cloud Router]()
1. [Verify the configuration]()

# My Solution

This is a pretty tough lab!

We will setup an HA VPN gateway from GCP to AWS, using an _AWS target gateway_ of type _virtual private gateway_.

I prefer to use the Cloud Shell and gcloud CLI, because it makes the steps much more repeatable.

## Prep

Note that the Google Cloud VPC has already been created.

Let's start by defining some variables we can use throughout this challenge. Run the following from the Cloud Shell:

```bash
gcloud auth list

# Network
prj=<enter-your-project> # use your own project ID
region=us-east4
vpc_name=cymbal-cloud-vpc
vpn_gw=cymbal-cloud-ha-vpn-gw
cloud_router=cymbal-cloud-router
bgp_asn=65534
aws_asn=65001
gcp_external_peer_gw=gcp-to-aws-vpn-gw

# setting defaults
gcloud config set project $prj  
gcloud config set compute/region $region
```

Substitute for any variables you've been given.

## Create the HA VPN gateway and Cloud Router on Google Cloud

Here we create an HA VPN gateway to achieve a 99.99% SLA. To do this, we setup a tunnel pair, where each gateway interface has one tunnel. The gateway has two interfaces.

```bash
gcloud compute vpn-gateways create $vpn_gw \
    --network=$vpc_name --region=$region
```

Make a note of the external IP addresses of the two interfaces.

![Create HA VPN Gateway](/assets/images/create_vpn_gateway.png)

Now create the **Cloud Router**.

```bash
# First, we need to create a Cloud Router
gcloud compute routers create $cloud_router \
  --network=$vpc_name --region=$region --asn=$bgp_asn 
```

## Create an AWS Customer gateway and a Target gateway

Follow the provided instructions in the lab, to perform setup on the AWS side. This is done using SSH from a GCE instance, or from the AWS console.

Start by obtaining the VPC ID of your AWS VPC:

![AWS VPC ID](/assets/images/aws_vpc.png)

We will:

- **Create two _AWS Customer gateways_** with dynamic routing. Run the supplied command, and each time, pass in one of the two external IP addresses for each interface on our Google Cloud VPN Gateway. Make a note of the customer gateway IDs, as we'll need them later. \
![Create AWS customer gateways](/assets/images/create_aws_customer_gw.png)
- **Create one _virtual private gateway_** (the VPN endpoint on the AWS side). The gateway exposes two intefaces. Make a note of the VPN gateway ID assigned.
- Attach the AWS virtual private gateway to the AWS VPC. \
![Attach VPN gateway to VPC](/assets/images/aws_attach_vpn_gateway.png)

## Create a VPN connection with dynamic routing on AWS

Here we setup two VPN connections with dynamic routing between the single AWS _virtual private gateway_ and the two AWS customer gateways. Again, follow the lab instructions for AWS setup.

Note that the four IP `TunnelInsideCidr` addresses are inferrable, based on the IP addresses specified later in the instructions for the tunnels. E.g. if your VPN tunnel first IP address is `169.254.10.2` then the `TunnelInsideCidr` for the corresponding AWS VPN connection will be `169.254.10.0/30`.

You will end up running two commands like this:

```bash
aws ec2 create-vpn-connection \
   --type ipsec.1 \
   --customer-gateway-id cgw-0e6fe48be2a01c25c \
   --vpn-gateway-id vgw-09bdfb794749c6644 \
   --options TunnelOptions='[{TunnelInsideCidr=169.254.10.1/30,PreSharedKey=gcprocks},{TunnelInsideCidr=169.254.20.1/30,PreSharedKey=gcprocks}]'
   
aws ec2 create-vpn-connection \
   --type ipsec.1 \
   --customer-gateway-id cgw-0cea6882c7aad930c \
   --vpn-gateway-id vgw-09bdfb794749c6644 \
   --options TunnelOptions='[{TunnelInsideCidr=169.254.30.1/30,PreSharedKey=gcprocks},{TunnelInsideCidr=169.254.40.1/30,PreSharedKey=gcprocks}]'
```

Each time, you may need to page down after executing the command, to retrieve the two outside IP addresses for each connection. If you fail to record your outside IP addresses, you can always retrieve them from your SSH session like this:

```bash
aws ec2 describe-vpn-connections
```

You can check the VPN connections are available in `VPN Connections` in the AWS Console.

## Create an external peer VPN gateway and VPN tunnels on Google Cloud

Now, back in Google Cloud, we create VPN tunnels to AWS using IKEv2 encryption.

First, create a Google Cloud external peer VPN gateway with four interfaces, using the four AWS private gateway outside addresses.

The challenge lab hints that you should use the outside IP addresses from the first AWS private gateway for interfaces 1 and 2, and the outside IP addresses from the second AWS private gateway for interfaces 3 and 4. Note, however, that the `external-vpn-gateways create` command expects `interfaces` to be identified from `0` to `3` inclusive.

So you end up with a command like this:

```bash
# Create the external peer VPN gateway
# The number of interfaces on the external VPN gateway 
# are determined by the number of interfaces provided
# I.e. four external VPN interfaces --> FOUR_IPS_REDUNDANCY
gcloud compute external-vpn-gateways create $gcp_external_peer_gw \
   --interfaces 0=34.203.132.63,1=52.201.113.232,2=3.225.181.154,3=52.200.76.9
```

(Don't forget to use your own IP addresses!)

Now create four VPN tunnels, using the four external interfaces of the Google Cloud external VPN gateway.

Your GCP VPN gateway only has two interfaces. So we will pair up:

- GW interface 0 with peer interfaces 0, 1
- GW interface 1 with peer interfaces 2, 3

(The requested interface names in the instructions are very misleading.)

```bash
gcloud compute vpn-tunnels create tunnel-1 \
   --peer-external-gateway=$gcp_external_peer_gw \
   --peer-external-gateway-interface=0 \
   --region=$region --router=$cloud_router \
   --ike-version=2 --shared-secret=gcprocks \
   --vpn-gateway=$vpn_gw \
   --interface=0

gcloud compute vpn-tunnels create tunnel-2 \
   --peer-external-gateway=$gcp_external_peer_gw \
   --peer-external-gateway-interface=1 \
   --region=$region --router=$cloud_router \
   --ike-version=2 --shared-secret=gcprocks \
   --vpn-gateway=$vpn_gw \
   --interface=0

gcloud compute vpn-tunnels create tunnel-3 \
   --peer-external-gateway=$gcp_external_peer_gw \
   --peer-external-gateway-interface=2 \
   --region=$region --router=$cloud_router \
   --ike-version=2 --shared-secret=gcprocks \
   --vpn-gateway=$vpn_gw \
   --interface=1

gcloud compute vpn-tunnels create tunnel-4 \
   --peer-external-gateway=$gcp_external_peer_gw \
   --peer-external-gateway-interface=3 \
   --region=$region --router=$cloud_router \
   --ike-version=2 --shared-secret=gcprocks \
   --vpn-gateway=$vpn_gw \
   --interface=1 
```

## Add BGP peers to the Cloud Router

Here we can use Cloud Router to establish a BGP session with the peer network over the VPN tunnels. Then, Cloud Router automatically learns teh subnet IP addresses of the Google network, and advertises them to the peer network.

We have four BGP peers to establish, for each of the four tunnels.

```bash
# first, add an interface to the Cloud Router for each tunnel
for i in {1..4}; do
    gcloud compute routers add-interface $cloud_router \
      --interface-name=int-$i --vpn-tunnel=tunnel-$i --region=$region \
      --ip-address=169.254.$((i * 10)).2 --mask-length=24
done

# now add a BGP peer
gcloud compute routers add-bgp-peer $cloud_router \
   --peer-name=aws-conn1-tunn1 --interface=int-1 --peer-ip-address=169.254.10.1 \
   --peer-asn=$aws_asn --region=$region

gcloud compute routers add-bgp-peer $cloud_router \
   --peer-name=aws-conn1-tunn2 --interface=int-2 --peer-ip-address=169.254.20.1 \
   --peer-asn=$aws_asn --region=$region

gcloud compute routers add-bgp-peer $cloud_router \
   --peer-name=aws-conn2-tunn1 --interface=int-3 --peer-ip-address=169.254.30.1 \
   --peer-asn=$aws_asn --region=$region

gcloud compute routers add-bgp-peer $cloud_router \
   --peer-name=aws-conn2-tunn2 --interface=int-4 --peer-ip-address=169.254.40.1 \
   --peer-asn=$aws_asn --region=$region   

# second tunnel...
```