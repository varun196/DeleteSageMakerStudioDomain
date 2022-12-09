import boto3
import time
import botocore.exceptions

domain_id = "d-uunilzplc5my"
region = "ap-southeast-2"

"""
DOES NOT WORK FOR DELETING SPACES
"""

class SageMakerDomainObliviator:
    def __init__(self, domain_id, region) -> None:
        self.domain_id = domain_id
        self.region = region 
        self.sm_client = boto3.client('sagemaker', region_name=region)

    def list_apps(self) -> list:
        app_list = []

        response = self.sm_client.list_apps(DomainIdEquals=domain_id)
        app_list.extend(response['Apps'])

        while('NextToken' in response):
            response = self.sm_client.list_apps(DomainIdEquals=domain_id, NextToken=response['NextToken'])
            app_list.extend(response['Apps'])
    
        return app_list
    
    def delete_apps_blocking(self, app_list) -> None:
        """
        Deletes app list provided. Blocks till the apps are deleted. 
        """
        for app in app_list:
            if app["Status"] in ["Deleted", "Deleting"]:
                print(f'App {app["AppName"]} is already in status {app["Status"]}')
                continue

            if ('UserProfileName' in app):
                print(f'deleting app {app["AppName"]}, {app}')
                self.sm_client.delete_app(DomainId=domain_id, UserProfileName=app['UserProfileName'], AppType=app['AppType'], AppName=app['AppName'])

        # Wait for app deletion
        for app in app_list:
            while True:
                if ('UserProfileName' in app):
                    result = self.sm_client.describe_app(DomainId=domain_id, UserProfileName=app['UserProfileName'], AppType=app['AppType'], AppName=app['AppName'])
                    print(f'{result["AppArn"]} is in status {result["Status"]}')
                    if result["Status"] != "Deleting":
                        break
                    print(f'Waiting for {result["AppArn"]} to be deleted')
                    time.sleep(30)
                else:
                    break
            
    def list_user_profiles(self) -> list:
        user_profile_list = []

        response = self.sm_client.list_user_profiles(DomainIdEquals=domain_id)
        user_profile_list.extend(response['UserProfiles'])

        while('NextToken' in response):
            response = self.sm_client.list_user_profiles(DomainIdEquals=domain_id, NextToken=response['NextToken'])
            user_profile_list.extend(response['UserProfiles'])
        
        return user_profile_list

    def delete_user_profiles_blocking(self,user_profile_list ) -> None:

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
                    result = self.sm_client.describe_user_profile(DomainId=domain_id, UserProfileName=up['UserProfileName'])
                    if result["Status"] != "Deleting":
                        break
                    time.sleep(30)
            except self.sm_client.exceptions.ResourceNotFound as ex:
                print(f"Resource not found {ex}")

    def delete_domain(self):
        try:
            print(f"Deleting domain {domain_id}")
            result = self.sm_client.delete_domain(DomainId=domain_id,  RetentionPolicy={'HomeEfsFileSystem':'Delete'})
        except (botocore.exceptions.ClientError) as ex:
            print(f'Caught error: [{ex}]')
    
    def delete_domain_with_dependencies(self):
        self.delete_apps_blocking(self.list_apps())
        self.delete_user_profiles_blocking(self.list_user_profiles())
        self.delete_domain()




smd = SageMakerDomainObliviator(domain_id, region)
smd.delete_domain_with_dependencies()