import boto3
import time
import botocore.exceptions

"""
TODO: ENABLE DELETION OF RESOURCES CREATED BY SAGEMAKER SPACES. 
"""

class SageMakerDomainObliviator:
    def __init__(self, region, endpoint_url) -> None:
        self.region = region
        if endpoint_url is None:
            self.sm_client = boto3.client('sagemaker', region_name=region)
        else:
            self.sm_client = boto3.client('sagemaker', region_name=region, endpoint_url=endpoint_url)

    def delete_domains_with_dependencies(self, domain_ids: list[str]):
        for domain_id in domain_ids:
            self.delete_apps_blocking(self.list_apps(domain_id), domain_id)
            self.delete_user_profiles_blocking(self.list_user_profiles(domain_id), domain_id)
            self.delete_domain_blocking(domain_id)

    def list_all_domain_ids_in_region(self):
        domain_list = []

        response = self.sm_client.list_domains()
        domain_list.extend(response['Domains'])

        while 'NextToken' in response:
            response = self.sm_client.list_domains(NextToken=response['NextToken'])
            domain_list.extend(response['Domains'])

        domain_id_list = [domain['DomainId'] for domain in domain_list]

        return domain_id_list

    def list_apps(self, domain_id: str) -> list:
        app_list = []

        response = self.sm_client.list_apps(DomainIdEquals=domain_id)
        app_list.extend(response['Apps'])

        while 'NextToken' in response:
            response = self.sm_client.list_apps(DomainIdEquals=domain_id, NextToken=response['NextToken'])
            app_list.extend(response['Apps'])

        return app_list

    def delete_apps_blocking(self, app_list, domain_id: str) -> None:
        """
        Deletes app list provided. Blocks till the apps are deleted.
        """
        for app in app_list:
            if app["Status"] in ["Deleted", "Deleting"]:
                print(f'App {app["AppName"]} is already in status {app["Status"]}')
                continue

            if 'UserProfileName' in app:
                print(f'deleting app {app["AppName"]}, {app}')
                self.sm_client.delete_app(DomainId=domain_id, UserProfileName=app['UserProfileName'],
                                          AppType=app['AppType'], AppName=app['AppName'])

        # Wait for app deletion
        for app in app_list:
            while True:
                if 'UserProfileName' in app:
                    # This is a user-profile app
                    result = self.sm_client.describe_app(DomainId=domain_id, UserProfileName=app['UserProfileName'],
                                                         AppType=app['AppType'], AppName=app['AppName'])
                    print(f'{result["AppArn"]} is in status {result["Status"]}')
                    if result["Status"] != "Deleting":
                        print(f'{app["AppName"]} Status: {result["Status"]}')
                        break
                    print(f'Waiting for {result["AppArn"]} to be deleted')
                    time.sleep(30)
                else:
                    # Most likely a Spaces app
                    print(f'Seems like {app["AppName"]} is a Spaces App. Not deleting Spaces app.')
                    break

    def list_user_profiles(self, domain_id: str) -> list:
        user_profile_list = []

        response = self.sm_client.list_user_profiles(DomainIdEquals=domain_id)
        user_profile_list.extend(response['UserProfiles'])

        while ('NextToken' in response):
            response = self.sm_client.list_user_profiles(DomainIdEquals=domain_id, NextToken=response['NextToken'])
            user_profile_list.extend(response['UserProfiles'])

        return user_profile_list

    def delete_user_profiles_blocking(self, user_profile_list, domain_id: str) -> None:

        # Delete User Profiles
        for up in user_profile_list:
            print(f'deleting user-profile {up["UserProfileName"]}')
            try:
                self.sm_client.delete_user_profile(DomainId=domain_id, UserProfileName=up['UserProfileName'])
            except botocore.errorfactory.ResourceNotFound as ex:
                print(f"Resource not found {ex}")

        # Wait for user profile deletion
        for up in user_profile_list:
            try:
                while True:
                    result = self.sm_client.describe_user_profile(DomainId=domain_id,
                                                                  UserProfileName=up['UserProfileName'])
                    if result["Status"] != "Deleting":
                        break
                    time.sleep(30)
            except self.sm_client.exceptions.ResourceNotFound as ex:
                None

    def delete_domain_blocking(self, domain_id: str):
        try:
            print(f"Deleting domain {domain_id}")
            self.sm_client.delete_domain(DomainId=domain_id, RetentionPolicy={'HomeEfsFileSystem': 'Delete'})
            try:
                while True:
                    result = self.sm_client.describe_domain(DomainId=domain_id)
                    if result["Status"] != "Deleting":
                        print(f"Domain: {domain_id} is in status: {result['Status']}")
                        break
                    time.sleep(30)
            except self.sm_client.exceptions.ResourceNotFound as ex:
                print(f"Deleted domain: {domain_id}")
                None

        except botocore.exceptions.ClientError as ex:
            print(f'Caught error: [{ex}]')
