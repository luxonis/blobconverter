import os
import sys
import argparse
import blobconverter
import itertools

try:
    from artifactory import ArtifactoryPath
except:
    print("Package \"artifactory\" not found! Please run {} -m pip install artifactory".format(sys.executable), file=sys.stderr)
    sys.exit(1)

parser = argparse.ArgumentParser()
parser.add_argument('username', help='Artifactory username, can be also set using env variable ARTIFACTORY_USERNAME', default=os.getenv('ARTIFACTORY_USERNAME'))
parser.add_argument('password', help='Artifactory password, can be also set using env variable ARTIFACTORY_PASSWORD', default=os.getenv('ARTIFACTORY_PASSWORD'))
parser.add_argument('-url', '--blobconverter-url', type=str, help="URL to custom BlobConverter URL to be used for conversion", required=False)
args = parser.parse_args()

if None in (args.username, args.password):
    parser.print_help()
    sys.exit(1)

if args.blobconverter_url is not None:
    blobconverter.set_defaults(url=args.blobconverter_url)

path = ArtifactoryPath("https://artifacts.luxonis.com/artifactory/blobconverter-backup/blobs", auth=(args.username, args.password))
if not path.exists():
    path.mkdir()

priority_models = ["mobilenet-ssd", "efficientnet-b0", "vehicle-license-plate-detection-barrier-0106", "vehicle-detection-adas-0002", "license-plate-recognition-barrier-0007"
                 "vehicle-attributes-recognition-barrier-0039", "face-detection-retail-0004", "landmarks-regression-retail-0009"]
backup_shaves = range(1, 17)

for model_name, shaves in itertools.product(backup_models, backup_shaves):
    print("Deploying {} with {} shaves...".format(model_name, shaves))
    try:
        path.deploy_file(blobconverter.from_zoo(model_name, shaves=shaves))
    except Exception as ex:
        print("Deployment failed due to {}".format(str(ex)))

for model_name in blobconverter.zoo_list():
    if model_name in priority_models:
        continue
    print("Deploying {}...".format(model_name))
    try:
        path.deploy_file(blobconverter.from_zoo(model_name))
    except Exception as ex:
        print("Deployment failed due to {}".format(str(ex)))

