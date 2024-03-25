import os

import arcpy
import pandas as pd

import scratch.dev.portalmanager as pm


class GisMigration:
    def __init__(self, migration_date, usr_args_migration_name, from_gis, to_gis,root_data_folder,
                 migrate_usernames=None, migrate_item_ids=None, migrate_item_types=None):
        self.date = migration_date
        self.name = usr_args_migration_name
        self.migrate_from = from_gis
        self.migrate_to = to_gis
        self.data_folder = self.make_migration_folders(root_data_folder)
        self.users = self.get_migrate_users(migrate_usernames)
        self.item_ids = migrate_item_ids
        self.item_types = migrate_item_types

    def __str__(self):
        return f"{self.name}"

    def make_migration_folders(self, root_data_folder):
        try:
            from_base_folder_name = self.migrate_from.url.lstrip('https://').replace('/', '_').rstrip('_').lower()
            from_output_path = os.path.join(root_data_folder, from_base_folder_name)
            if not os.path.exists(from_output_path):
                os.makedirs(from_output_path)

            from_users_path = os.path.join(root_data_folder, from_base_folder_name, 'users')
            if not os.path.exists(from_users_path):
                os.makedirs(from_users_path)

            from_csv_path = os.path.join(from_users_path, 'csv')
            if not os.path.exists(from_csv_path):
                os.makedirs(from_csv_path)

            return from_output_path
        except Exception as e:
            print(e.args)

    def get_migrate_users(self, usernames=None):
        """returns a list of users in a gis that are in a search list

          Parameters:
          gis (int): an instance of the GIS class

          Returns:
          users_list (str): list of users

         """
        try:
            print(f"Connected to {self.migrate_from}")
            users = []
            for username in usernames:

                user_search = self.migrate_from.users.search(query=f"username:{username}",
                                                             sort_field='username',
                                                             sort_order='asc',
                                                             max_users=10000,
                                                             outside_org=False,
                                                             exclude_system=True)
                if user_search:
                    users.append(user_search[0])

            return users
        except Exception as e:
            print(e.args)
            return None


class MigrateUser:
    def __init__(self, from_gis, user):
        self.user = user
        # self.migration = gis_migration
        self.migrate_from = from_gis
        # self.migrate_items = None

    def __str__(self):
        return f"{self.user.username}"

    def get_migrate_user_items_list(self, itemids_list=None, item_types=None):
        try:
            items = []
            # items_list = self.migration.migrate_items_list
            # for user in self.migrate_users_list:
            if itemids_list:
                for item_id in itemids_list:
                    # Search for each item by ID
                    item_search = self.migrate_from.content.search(
                        query=f"owner:{self.user.username}, id:{item_id}", max_items=1000)
                    if item_search:
                        items.append(item_search[0])

                # return items
            elif not itemids_list and item_types is not None:
                for item_type in item_types:
                    item_search = self.migrate_from.content.search(
                        query=f"owner:{self.user.username}, type:{item_type}", max_items=1000)
                    if item_search:
                        items.append(item_search[0])
            else:
                owner = self.user.username
                search_query = f"owner:{owner}"
                item_search = self.migrate_from.content.search(query=search_query, max_items=1000)
                if item_search:
                    items.append(item_search[0])

            return items
        except Exception as e:
            print(e.args)

    def make_migrate_items_df(self):
        """Returns a pandas dataframe with all content items and their dependencies for a user of a gis

          Parameters:
          Returns:
          dataframe with user content references

         """

        try:
            num_items = 0
            num_folders = 0
            arcpy.AddMessage(f"Collecting item ids for {self.user.username}")
            # print(f"Collecting item ids for {}".format(self.user.username))
            # user = self.migrate_from.users.search(query=f"username:{user.username}")[0]
            user_content = self.migrate_items
            folders = self.user.folders
            # source_items_by_id = {}
            output_df = pd.DataFrame(columns=['username',
                                              'item_id',
                                              'item_url',
                                              'item_title',
                                              'item_type',
                                              'dependentupon_id',
                                              'dependentupon_item_url',
                                              'dependentupon_item_title',
                                              'dependentupon_item_type'  # ,
                                              # 'dependentto_id',  #todo: dependentto items
                                              # 'dependentto_item_url',
                                              # 'dependentto_item_title',
                                              # 'dependentto_item_type'
                                              ])

            if len(user_content) > 0:
                for item in user_content:
                    # print(item.itemid)
                    pm.item_dependents_df(self.migration.migrate_from, self.user, item, output_df)

                for folder in folders:
                    num_folders += 1
                    folder_items = self.user.items(folder=folder['title'])
                    for item in folder_items:
                        num_items += 1
                        pm.item_dependents_df(self.migration.migrate_from, self.user, item, output_df)

            output_df = output_df.set_index(['username', 'item_id', 'dependentupon_id'])
            return output_df

        except Exception as e:
            print(e.args)

    # def get_migrate_user_items(self, gis_migration):
    #     try:
    #         items_list = itemslist


    def user_item_report_csv(self, output_csv_path):
        try:
            user_content_df = self.content_df
            user_content_df.to_csv(output_csv_path)
        except Exception as e:
            print(e.args)

    # def user_content_migrate(self):
    #     try:
    #         print(f'Migrating content for user {self.user.username}')
    #         for itemid in self.content_df.iterrows():
    #             print(itemid)
    #
    #     except Exception as e:
    #         print(e.args)
    #
    # def get_items_migration(self):
    #     try:
    #         print(f'Fetching items for user {self.user.username} for migration {self.migration.name}')
    #         # search items, use migration.items list to filter items
    #
    #     except Exception as e:
    #         print(e.args)
