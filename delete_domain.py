import argparse
import sys

from DeleteSageMakerDomain.SageMakerDomainObliviator import SageMakerDomainObliviator

delete_domain_argument_parser = argparse.ArgumentParser(description='Deletes a given SageMaker domain')

delete_domain_argument_parser.add_argument("--region", required=True, help="The region for domain: like us-west-2")
delete_domain_argument_parser.add_argument("--delete-all-domains-in-region", required=False, help="Bool flag to delete all domains in region.")
delete_domain_argument_parser.add_argument("--domain-id-list", required=False, help="The domain ids to be deleted.", nargs="*")
delete_domain_argument_parser.add_argument("--endpoint-url", required=False, help="Optional endpoint url")

args=delete_domain_argument_parser.parse_args()

if args.delete_all_domains_in_region is None and args.domain_id_list is None:
    print(f'Must provide either the domain ids to be deleted, or specify delete-all-domains-in-region flag.')
    sys.exit()

sageMakerDomainObliviator = SageMakerDomainObliviator(args.region, args.endpoint_url)

if args.delete_all_domains_in_region:
    sageMakerDomainObliviator.delete_domains_with_dependencies(sageMakerDomainObliviator.list_all_domain_ids_in_region())
else:
    sageMakerDomainObliviator.delete_domains_with_dependencies(args.domain_id_list)

# import boto3
# domain_id = "d-pfe81l4vddp7"
# region = "us-east-1"
# sm_client = boto3.client('sagemaker', region_name=region)
#
# spaces = sm_client.list_spaces(DomainIdEquals=domain_id)