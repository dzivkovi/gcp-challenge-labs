# Perform Foundational Infrastructure Tasks in Google Cloud

See [Challenge Lab](https://www.cloudskillsboost.google//course_sessions/5014354/labs/403971){:target="_blank"}

# Challenge

You've been asked to:

- Create a bucket for storing the photographs.
- Create a Pub/Sub topic that will be used by a Cloud Function you create.
- Create a Cloud Function.
- Remove the previous cloud engineer’s access from the memories project.

You're given some standards to follow:

- Create all resources in the specified region and zone, unless otherwise directed.
- Use the project VPCs.
- Naming is normally `team-resource`, e.g. an instance could be named `kraken-webserver1`
- Allocate cost effective resource sizes. Projects are monitored and excessive resource use will result in the containing project's termination (and possibly yours), so beware. Use:
  - e2-micro for small Linux VMs
  - e2-medium for Windows or other applications such as Kubernetes nodes.

# My Solution

I prefer to use the Cloud Shell and gcloud CLI, because it makes the steps much more repeatable.

## Prep

Let's start by defining some variables we can use throughout this challenge:

```bash
gcloud auth list

prj=qwiklabs-gcp-04-d047d2a3a544
region=us-central1
zone=us-central1-f
bucket=qwiklabs-gcp-04-d047d2a3a544-bucket
topic=topic-memories-333
cfunc=memories-thumbnail-creator
user1=student-00-18a23fbbbab4@qwiklabs.net
user2=student-04-519d4e4dc131@qwiklabs.net

gcloud config set compute/region $region
gcloud config set compute/zone $zone
```

Substitute for any variables you've been given, in your instance of the challenge.

## Task 1 - Create the Bucket

```bash
gsutil mb gs://$bucket
```

## Task 2 - Create the Pub/Sub Topic

```bash
gcloud pubsub topics create $topic
```

## Task 3 - Create the Cloud Function

You need to create a folder for your function code.

```bash
mkdir thumbnail && cd $_
```

Now create your `index.js`.  It should look like this:

```javascript
const functions = require('@google-cloud/functions-framework');
const crc32 = require("fast-crc32c");
const { Storage } = require('@google-cloud/storage');
const gcs = new Storage();
const { PubSub } = require('@google-cloud/pubsub');
const imagemagick = require("imagemagick-stream");
functions.cloudEvent('', cloudEvent => {
  const event = cloudEvent.data;
  console.log(`Event: ${event}`);
  console.log(`Hello ${event.bucket}`);
  const fileName = event.name;
  const bucketName = event.bucket;
  const size = "64x64"
  const bucket = gcs.bucket(bucketName);
  const topicName = "";
  const pubsub = new PubSub();
  if ( fileName.search("64x64_thumbnail") == -1 ){
    // doesn't have a thumbnail, get the filename extension
    var filename_split = fileName.split('.');
    var filename_ext = filename_split[filename_split.length - 1];
    var filename_without_ext = fileName.substring(0, fileName.length - filename_ext.length );
    if (filename_ext.toLowerCase() == 'png' || filename_ext.toLowerCase() == 'jpg'){
      // only support png and jpg at this point
      console.log(`Processing Original: gs://${bucketName}/${fileName}`);
      const gcsObject = bucket.file(fileName);
      let newFilename = filename_without_ext + size + '_thumbnail.' + filename_ext;
      let gcsNewObject = bucket.file(newFilename);
      let srcStream = gcsObject.createReadStream();
      let dstStream = gcsNewObject.createWriteStream();
      let resize = imagemagick().resize(size).quality(90);
      srcStream.pipe(resize).pipe(dstStream);
      return new Promise((resolve, reject) => {
        dstStream
          .on("error", (err) => {
            console.log(`Error: ${err}`);
            reject(err);
          })
          .on("finish", () => {
            console.log(`Success: ${fileName} → ${newFilename}`);
              // set the content-type
              gcsNewObject.setMetadata(
              {
                contentType: 'image/'+ filename_ext.toLowerCase()
              }, function(err, apiResponse) {});
              pubsub
                .topic(topicName)
                .publisher()
                .publish(Buffer.from(newFilename))
                .then(messageId => {
                  console.log(`Message ${messageId} published.`);
                })
                .catch(err => {
                  console.error('ERROR:', err);
                });
          });
      });
    }
    else {
      console.log(`gs://${bucketName}/${fileName} is not an image I can handle`);
    }
  }
  else {
    console.log(`gs://${bucketName}/${fileName} already has a thumbnail`);
  }
});
```

Create `package.json`:

```json
{
  "name": "thumbnails",
  "version": "1.0.0",
  "description": "Create Thumbnail of uploaded image",
  "scripts": {
    "start": "node index.js"
  },
  "dependencies": {
    "@google-cloud/functions-framework": "^3.0.0",
    "@google-cloud/pubsub": "^2.0.0",
    "@google-cloud/storage": "^5.0.0",
    "fast-crc32c": "1.0.4",
    "imagemagick-stream": "4.1.1"
  },
  "devDependencies": {},
  "engines": {
    "node": ">=4.3.2"
  }
}
```

Now we're ready to create the Cloud Function:

```bash
gcloud functions deploy $cfunc \
  --gen2 \
  --stage-bucket $bucket \
  --trigger-topic $topic \
  --runtime nodejs20
```

## Task 4 - Test by Uploading an Image

Retrieve a picture, and download it to your Cloud Shell. From there, copy it to your bucket.

```bash
curl https://storage.googleapis.com/cloud-training/gsp315/map.jpg --output map.jpg
gsutil cp map.jpg gs://$bucket
```

Verify that the thumbnails are created in the bucket automatically.

![Thumbnail Created](/assets/images/thumbnail-created.png){: style="width:640px"}

## Task 5 - Remove User 2 Access from the Project

Finally, we're told to remove user 2, who has been given `Viewer` access to our project.

```bash
cd ~
gcloud projects get-iam-policy $prj --format=json > policy.json
```

Edit the policy, and remove the user:

![Thumbnail Created](/assets/images/upd-pol.png){: style="width:640px"}

Now apply the new policy:

```bash
# edit the policy
gcloud projects set-iam-policy $prj policy.json
```

All done!