# Automating Infrastructure on Google Cloud with Terraform

See [Challenge Lab](https://partner.cloudskillsboost.google/focuses/16515?parent=catalog){:target="_blank"}

# Challenge

In this lab, we're going to:

- Import existing infrastructure into your Terraform configuration.
- Build and reference your own Terraform modules.
- Add a remote backend to your configuration.
- Use and implement a module from the Terraform Registry.
- Re-provision, destroy, and update infrastructure.
- Test connectivity between the resources you've created.

# My Solution

As usual, I'll start by defining some variables we can use throughout this challenge:
```bash
gcloud auth list

region=us-east1
zone=ENTER ZONE
prj=ENTER PRJ ID
```

## Task 1 - Create the Configuration Files

We're told to create this folder structure:

```text
main.tf
variables.tf
modules/
└── instances
|   ├── instances.tf
|   ├── outputs.tf
|   └── variables.tf
└── storage
    ├── storage.tf
    ├── outputs.tf
    └── variables.tf
```

```bash
# Create main.tf and variables.tf in the root directory
touch main.tf variables.tf

# Create main directory and its files
mkdir -p modules/instances
mkdir modules/storage

# Create the required files in the 'instances' module directory
touch modules/instances/instances.tf
touch modules/instances/outputs.tf
touch modules/instances/variables.tf

# Create the required files in the 'storage' module directory
touch modules/storage/storage.tf
touch modules/storage/outputs.tf
touch modules/storage/variables.tf
```

Update all three `variables.tf` files to contain these variables:

```javascript
variable "region" {
  description = "The Google Cloud region"
  type        = string
  default     = "us-east1"
}

variable "zone" {
  description = "The Google Cloud zone"
  type        = string
  default     = "Lab-supplied zone"
}

variable "project_id" {
  description = "The ID of the project in which to provision resources."
  type        = string
  default     = "Your project ID"
}
```

Update the root module `main.tf` to include the Google Cloud Provider, which you can always look up in the  [Terraform Registry](https://registry.terraform.io/providers/hashicorp/google/latest/docs){:target="_blank"}. We're asked to include all three of these variables in our `provider` block.

```javascript
terraform {
  required_providers {
    google = {
      source = "hashicorp/google"
    }
  }
}

provider "google" {
  project     = var.project_id
  region      = var.region
  zone        = var.zone
}
```

Now initialise Terraform:

```bash
terraform init
```

## Task 2 - Import Infrastructure

Here, the goal is to bring infrastructure under Terraform control, that has thus far been provisioned outside of Terraform.

We're going to use the Terraform import workflow:

![Terraform import workflow](/assets/images/tf_import_workflow.png)

These are the import steps:

1. Identify the existing infrastructure to be imported.
1. Import the infrastructure into your Terraform state.
1. Write a Terraform configuration that matches that infrastructure.
1. Review the Terraform plan to ensure that the configuration matches the expected state and infrastructure.
1. Apply the configuration to update your Terraform state.

### Step 1 - Identify the existing infrastructure to be imported

Examine one of the existing instances, `tf-instance-1`.  We want to retrieve:

- Network
- Machine type
- Disk

Next we need to include two calls to our `instances` module in our `main.tf`. They will contain empty definitions, so that we can import.

```javascript
module "tf_instance_1" {
  source        = "./modules/instances"
  instance_name = "tf-instance-1"
  zone          = var.zone
  region        = var.region
}

module "tf_instance_2" {
  source        = "./modules/instances"
  instance_name = "tf-instance-2"
  zone          = var.zone
  region        = var.region
}
```

Remember that each module definition must have a unique label.

Now initialise:

```bash
terraform init
```

Now we write the [module configurations](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_instance) in `instances.tf`:

```javascript
resource "google_compute_instance" "instance" {
  name         = var.instance_name
  machine_type = "hard code from existing instance"
  zone         = var.zone

  boot_disk {
    initialize_params {
      # image = "debian-cloud/debian-11"
      image = "hard code from existing instance"
    }
  }

  network_interface {
    # network = "default"
    network = "hard code from existing instance"

    access_config {
      // Ephemeral public IP
    }
  }

  metadata_startup_script = <<-EOT
          #!/bin/bash
      EOT
  allow_stopping_for_update = true
}
```

Update `variables.tf` in the `instance` module, so we can pass in the `instance_name`:

```javascript
variable "instance_name" {
  description = "The name of the instance."
  type        = string
}
```

### Import the Existing Infrastructure into Terraform State

```bash
terraform import module.tf_instance_1.google_compute_instance.instance \
  projects/$prj/zones/$zone/instances/tf-instance-1

terraform import module.tf_instance_2.google_compute_instance.instance \
  projects/$prj/zones/$zone/instances/tf-instance-2

# verify the import
terraform show
```

The import should look like this:

![Terraform import](/assets/images/tf-import.png)

### Plan and Apply

```bash
terraform plan
terraform apply
```

## Task 3 - Configure a Remote Backend

This is pretty easy. The steps are:

1. Provision a GCS bucket with TF.
1. Add a `backend` block that points to the new GCS bucket.
1. Reinitialise Terraform and migrate the state from the local state file to the remote backend.

### Provision the GCS Bucket

Add this resource definition to `main.tf`:

```javascript
resource "google_storage_bucket" "test-bucket-for-state" {
  name        = "Bucket Name You Are Given"
  location    = "US"
  uniform_bucket_level_access = true

  force_destroy = true
}
```

And apply:

```bash
terraform apply
```

### Add the GCS Backend

Modify 'main.tf' and include the backend in the `terraform` block:

```javascript
terraform {
  backend "gcs" {
    bucket  = var.project_id
    prefix  = "terraform/state"
  }
}
```

### Migrate the State

```bash
terraform init -migrate-state
```

It will ask you to confirm you want to migrate the state:

![Terraform migrate state](/assets/images/tf-migrate-state.png)

## Modify and Update the Infrastructure

We need to update `variables.tf` to include a `machine_type`:

```javascript
variable "machine_type" {
  description = "The machine type of an instance"
  type        = string
  default     = "e2-standard-2"
}
```

Then we need to modify `instance.tf` so that it can accept a `machine_type` parameter:

```javascript
resource "google_compute_instance" "instance" {
  name         = var.instance_name
  machine_type = var.machine_type
  zone         = var.zone

  ...
```

Lastly, we need to modify `main.tf` such that we add the specified third instance to our `main.tf`, by calling the module for a third time. We don't need to pass in the `machine_type`, as we've already set it to have a default.

Now initialise (because we've added another module instance) and apply.

```bash
terraform init
terraform apply
```

## Task 5 - Destroy Resources

Now we remove the instance we previously added.  Remove the call to this module from `main.tf`, then reapply:

```bash
terraform init
terraform apply
```

## Task 6 - Use a Module from the Registry

We're going to use the [Google Network Module](https://registry.terraform.io/modules/terraform-google-modules/network/google/6.0.0){:target="_blank"}.

```javascript
module "network" {
  source  = "terraform-google-modules/network/google"
  version = "6.0.0"

  project_id   = var.project_id
  network_name = "Use Supplied VPC Name"
  routing_mode = "GLOBAL"

  subnets = [
    {
      subnet_name           = "subnet-01"
      subnet_ip             = "10.10.10.0/24"
      subnet_region         = var.region
    },
    {
      subnet_name           = "subnet-02"
      subnet_ip             = "10.10.20.0/24"
      subnet_region         = var.region
    }
  ]
}
```

Apply:

```bash
terraform init
terraform apply
```

Update `instances` module to take a `network` parameter and a `subnet` parameter.

In `variables.tf`:

```javascript
variable "network" {
  description = "The network"
  type        = string
}

variable "subnet" {
  description = "The subnet"
  type        = string
}
```

In `instance.tf`:

```javascript
  network_interface {
    network = var.network
    subnetwork = var.subnet

    access_config {
      // Ephemeral public IP
    }
  }
```

Then update `main.tf` to create the instances like this:

```javascript
module "tf_instance_1" {
  source        = "./modules/instances"
  instance_name = "tf-instance-1"
  zone          = var.zone
  region        = var.region

  network       = module.network.network_name
  subnet        = "subnet-01"
}

module "tf_instance_2" {
  source        = "./modules/instances"
  instance_name = "tf-instance-2"
  zone          = var.zone
  region        = var.region

  network       = module.network.network_name
  subnet        = "subnet-02"
}
```

```bash
terraform init
terraform apply
```

## Task 7 - Add a Firewall

Update `main.tf`:

```javascript
resource "google_compute_firewall" "default" {
  name          = "tf-firewall"
  network       = module.network.network_name
  direction     = "INGRESS"
  source_ranges = ["0.0.0.0/0"]

  allow {
    protocol = "tcp"
    ports    = ["80"]
  }
}
```

And one last apply...

```bash
terraform apply
```

And we're done!