import datetime
import json
import logging
import os
import re
import sys
import time

import pandas as pd
import requests
from arcgis import GIS
from arcgis.features import FeatureLayer, FeatureSet, FeatureLayerCollection
from arcgis.geometry import project, Geometry
from arcgis.mapping import WebMap

# import scripts.portalmanager as pm

# Logging
SaveLogsTo = '../Logs'
logging.basicConfig(level=logging.INFO)
logging.getLogger('arcgis.gis._impl').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)
logFileName = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S')
fileHandler = logging.handlers.RotatingFileHandler('{}/{}.log'.format(SaveLogsTo, logFileName), maxBytes=100000,
                                                   backupCount=5)
formatter = logging.Formatter(
    '%(asctime)s %(levelname)s %(relativeCreated)d \n%(filename)s %(module)s %(funcName)s %(lineno)d \n%(message)s\n')
fileHandler.setFormatter(formatter)
logger.addHandler(fileHandler)
logger.info('Script Starting at {}'.format(str(datetime.datetime.now())))

# Connections details
portals_csv = r"C:\GIS\code\portalman\conf\portal_connect_deets.csv"

# '../Conf/portal_connect_deets.csv'

# Parameters
usr_args_from_gis_alias_name = 'ISP_OAUTH2'  # 'Geoportal_DEV'  # 'ISP_OAUTH2' #'Geoportal_DEV' #'ISP_OAUTH2'
usr_args_to_gis_alias_name = 'DIGITAL_DEV_UP'  # 'DIGITAL_DEV'  # 'Geoportal_DEV' #'DIGITAL_DEV'  # 'Geoportal_DEV'  #
migration_name = "ISP_to_DIGITAL_DEV"  # "portaldev_to_digital_dev" #"ISP_to_DIGITAL_DEV" #
# migrate_itemid = '96970af38ade49d4845671d442a9c1cc'
usr_args_process_username = ''  # 'Katleya.DelaCruz@aurecongroup.com'  # 'wilson.sahmet@aurecongroup.com'
migrate_item_type = 'Feature Layer'  # 'Feature Service'
# migrate_item_type = "Web Map"
# migrate_item_type = 'StoryMap'  # 'Dashboard'   #,'Web Mapping Application',

### from /lib
# def _deep_get(dictionary, *keys):
#     """Safely return a nested value from a dictionary. If at any point along the path the key doesn't exist the function will return None.
#     Keyword arguments:
#     dictionary - The dictionary to search for the value
#     *keys - The keys used to fetch the desired value"""
#
#     return reduce(lambda d, key: d.get(key) if d else None, keys, dictionary)

def get_dictionary_values_keys(dictionary, *keys):   # based upon _deep_get
    """Safely return a nested value from a dictionary. If at any point along the path the key doesn't exist the function will return None.
    Keyword arguments:
    dictionary - The dictionary to search for the value
    *keys - The keys used to fetch the desired value"""
    # return reduce(lambda d, key: d.get(key) if d else None, keys, dictionary)  # original line in _deep_get
    return (lambda d, key: d.get(key) if d else None, keys, dictionary)

def get_photo_encode(url, token):
    payload = {'token': token, 'f': 'json'}
    response = requests.get(url, params=payload)
    if response.status_code == 200:
        # print(response.json())
        return (response.json())
    else:
        print("Request failed with status code:", response.status_code)


def max_record_count(url, token):
    # Change user URL to Admin URL
    url = url.replace("rest/services", "admin/services")
    url = url.replace("/FeatureServer", ".FeatureServer")
    # Get the service defintion
    payload = {"token": token, 'f': 'json'}
    response = requests.post(url, data=payload)
    if response.status_code == 200:
        service_defn = response.json()
        print("Get the service defintion request succeeded")
    else:
        print("Get the service defintion request failed with status code:", response.status_code)
    # Grab the current deifntion of the layers dictionary
    layers = service_defn["jsonProperties"]["layers"]
    # Reset the maxRecordCount property
    service_defn["jsonProperties"]["maxRecordCount"] = 2000
    for layer in layers:
        print(layer)
        layers[layer]['maxRecordCount'] = 2000

    # Now update service via edit method
    payload = {'token': token, 'f': 'json', "service": json.dumps(service_defn)}
    response = requests.post(url + "/edit", data=payload)
    if response.status_code == 200:
        print("Edit layer maxRecordCount request succeeded")
    else:
        print("Edit layer maxRecordCount request failed with status code:", response.status_code)


def build_json_flc(feature_layer_collection):


    # temp_json={"hasViews": true}
    # turn PropertyMap type to list of dictionaries (PropertyMap is not JSON
    # serializable)
    # fields = []
    # for i in table:
    #     d = {}
    #     for k, v in i.items():
    #         d[k] = v
    #     fields.append(d)
    #
    # # assumes field OBJECTID is your objectIdField
    # temp_json = json.dumps({'layers':
    #                             [{'name': name,
    #                               'type': 'Table',
    #                               'objectIdField': 'OBJECTID',
    #                               'fields': fields}]})

    return {}#temp_json
def add_to_definition(target_gis, flc ,add_json):
    token = target_gis._con.token

    url = f'{flc.service.url}/AddToDefinition?token={token}' # build URL to POST to
    payload_add = {
            'addToDefinition': add_json,
            'async': 'true',
            'f': 'json',
            'token': token
    }
    session = requests.Session()
    result = session.post(url,data=payload_add)
    print(result)

def append_data_feature_layer_wtables(source_gis, target_gis, source_feature_layer_item_id,
                              target_feature_layer_item_id):
    try:
        source_item = source_gis.content.get(source_feature_layer_item_id)
        empty_service_item = target_gis.content.get(target_feature_layer_item_id)
        trg_flc = FeatureLayerCollection.fromitem(empty_service_item)

        # for layer_item in source_item.layers:
        #     src_url = layer_item.url
        #     src_fl_id = src_url.split("/")[-1]
        #     trg_fl_id = "/" + str(src_fl_id)
        #     print(src_url)
        #     json_str = json.loads(f'{layer_item.properties}')
        #     del json_str['serviceItemId']
        #     # del json_str['sourceSpatialReference']
        #     temp_json = {'layers': []}
        #     temp_json["layers"].append(json_str)
        #     print("adding definition")
        #     trg_flc.manager.add_to_definition(temp_json)
        #     # time.sleep(10)
        #     print("done definition")
        #
        #     src_fl = FeatureLayer(src_url, gis=source_gis)
        #     src_fl_feature_count = src_fl.query(where='1=1', return_count_only=True)
        #     print(f"Source feature count: {src_fl_feature_count}")
        #
        #     new_fl = FeatureLayer(trg_flc.url + trg_fl_id, gis=target_gis)
        #     new_fl_feature_count = new_fl.query(where='1=1', return_count_only=True)
        #     print(f"Target feature count: {new_fl_feature_count}")
        #
        #     has_attachments = layer_item.properties.hasAttachments
        #     new_fl_atts_count = ''
        #     src_fl_atts_count = ''
        #
        #     # if has_attachments:
        #     #     src_fl_atts_count = src_fl.attachments.count(where="1=1")
        #     #     new_fl_atts_count = new_fl.attachments.count(where="1=1")
        #     #
        #     #
        #     #     print(f"Source attachments count: {src_fl_atts_count}")
        #     #
        #     #     print(f"Target attachments count: {new_fl_atts_count}")
        #     #
        #     # if new_fl_feature_count == src_fl_feature_count and new_fl_atts_count == src_fl_atts_count:
        #     #     pass
        #
        #     src_fset = src_fl.query("1=1")
        #     src_fset_df = src_fset.sdf
        #     batch_size = 100
        #     batches = [group for _, group in src_fset_df.groupby(src_fset_df.index // batch_size)]
        #     start_time = datetime.datetime.now()
        #     print("Batching edits...")
        #     print(f"Starting at {str(start_time)}")
        #     for i, batch_df in enumerate(batches):
        #         token = source_gis._con.token
        #
        #         final_fs = FeatureSet.from_dataframe(batch_df)
        #         att_str = {"adds": [], "updates": [], "deletes": []}
        #
        #         for feat in final_fs.features:
        #             id_num = feat.attributes['objectid']
        #             global_id = feat.attributes['globalid']
        #             # print(global_id)
        #             if has_attachments:
        #                 att_list = src_fl.attachments.get_list(oid=id_num)
        #                 # att_list = src_fl.attachments.search(object_ids = str(id_num),return_url=True)
        #                 # print(att_list)
        #                 if len(att_list) > 0:
        #                     for att in att_list:
        #                     # # print(att)
        #                         # print("attid:"+str(att['attachmentid']))
        #                         if att['keywords']:
        #                             # print(att['keywords'])
        #                             url = src_url + "/" + str(id_num) + "/attachments/" + str(att['attachmentid'])
        #                             photo_encode = get_photo_encode(url, token)['Attachment']
        #                             # print(url)
        #                             att_json = {
        #                                 "parentGlobalId": global_id,
        #                                 "globalId": att['globalid'],
        #                                 "contentType": att['contentType'],
        #                                 "data": photo_encode,
        #                                 "name": att['name'],
        #                                 "keywords": att['keywords'],
        #                                 "attachmentid": att['attachmentid'],
        #                                 "att_name": att['att_name']
        #                             }
        #                             att_str['adds'].append(att_json)
        #                         else:
        #                             # print(att['keywords'])
        #                             url = src_url + "/" + str(id_num) + "/attachments/" + str(att['attachmentid'])
        #                             photo_encode = get_photo_encode(url, token)['Attachment']
        #                             # print(url)
        #                             att_json = {
        #                                 "parentGlobalId": global_id,
        #                                 "globalId": att['globalid'],
        #                                 "contentType": att['contentType'],
        #                                 "data": photo_encode,
        #                                 "name": att['name'],
        #                                 "keywords": None,
        #                                 "attachmentid": att['attachmentid'],
        #                                 "att_name": att['att_name']
        #                             }
        #                             att_str['adds'].append(att_json)
        #
        #         # print("attachment number in this batch: " + str(len(att_str['adds'])))
        #
        #         # print(final_fs)
        #         try:
        #             result = new_fl.edit_features(adds=final_fs, use_global_ids=True, rollback_on_failure=True,
        #                                           attachments=att_str)
        #         except Exception as ef :
        #             print(f"Exception (append_data_feature_layer.new_fl.edit_features): {ef.args}.")
        #
        #
        #         print(f"Added {str(len(att_str['adds']))} attachment in batch {i}" )
        #         print(f"Target feature count after batch {i}: ", new_fl.query(where='1=1', return_count_only=True))
        #
        #         end_time = datetime.datetime.now()
        for table_item in source_item.tables:  # todo
            src_url = table_item.url
            src_fl_id = src_url.split("/")[-1]
            trg_fl_id = "/" + str(src_fl_id)
            print(src_url)
            json_str = json.loads(f'{table_item.properties}')
            del json_str['serviceItemId']
            # del json_str['sourceSpatialReference']
            temp_json = {'tables': []}
            temp_json["tables"].append(json_str)
            print("adding tables definition")
            trg_flc.manager.add_to_definition(temp_json)
            # time.sleep(10)
            print("done definition")

            src_fl = Table(src_url, gis=source_gis)# FeatureLayer(src_url, gis=source_gis)
            src_fl_feature_count = src_fl.query(where='1=1', return_count_only=True)
            print(f"Source feature count: {src_fl_feature_count}")

            new_fl = FeatureLayer(trg_flc.url + trg_fl_id, gis=target_gis)
            new_fl_feature_count = new_fl.query(where='1=1', return_count_only=True)
            print(f"Target feature count: {new_fl_feature_count}")

            has_attachments = table_item.properties.hasAttachments
            new_fl_atts_count = ''
            src_fl_atts_count = ''

            # if has_attachments:
            #     src_fl_atts_count = src_fl.attachments.count(where="1=1")
            #     new_fl_atts_count = new_fl.attachments.count(where="1=1")
            #
            #
            #     print(f"Source attachments count: {src_fl_atts_count}")
            #
            #     print(f"Target attachments count: {new_fl_atts_count}")
            #
            # if new_fl_feature_count == src_fl_feature_count and new_fl_atts_count == src_fl_atts_count:
            #     pass

            src_fset = src_fl.query("1=1")
            src_fset_df = src_fset.sdf
            batch_size = 100
            batches = [group for _, group in src_fset_df.groupby(src_fset_df.index // batch_size)]
            start_time = datetime.datetime.now()
            print("Batching edits...")
            print(f"Starting at {str(start_time)}")
            for i, batch_df in enumerate(batches):
                token = source_gis._con.token

                final_fs = FeatureSet.from_dataframe(batch_df)
                att_str = {"adds": [], "updates": [], "deletes": []}

                for feat in final_fs.features:
                    id_num = feat.attributes['objectid']
                    global_id = feat.attributes['globalid']
                    # print(global_id)
                    if has_attachments:
                        att_list = src_fl.attachments.get_list(oid=id_num)
                        # att_list = src_fl.attachments.search(object_ids = str(id_num),return_url=True)
                        # print(att_list)
                        if len(att_list) > 0:
                            for att in att_list:
                                # # print(att)
                                # print("attid:"+str(att['attachmentid']))
                                if att['keywords']:
                                    # print(att['keywords'])
                                    url = src_url + "/" + str(id_num) + "/attachments/" + str(att['attachmentid'])
                                    photo_encode = get_photo_encode(url, token)['Attachment']
                                    # print(url)
                                    att_json = {
                                        "parentGlobalId": global_id,
                                        "globalId": att['globalid'],
                                        "contentType": att['contentType'],
                                        "data": photo_encode,
                                        "name": att['name'],
                                        "keywords": att['keywords'],
                                        "attachmentid": att['attachmentid'],
                                        "att_name": att['att_name']
                                    }
                                    att_str['adds'].append(att_json)
                                else:
                                    # print(att['keywords'])
                                    url = src_url + "/" + str(id_num) + "/attachments/" + str(att['attachmentid'])
                                    photo_encode = get_photo_encode(url, token)['Attachment']
                                    # print(url)
                                    att_json = {
                                        "parentGlobalId": global_id,
                                        "globalId": att['globalid'],
                                        "contentType": att['contentType'],
                                        "data": photo_encode,
                                        "name": att['name'],
                                        "keywords": None,
                                        "attachmentid": att['attachmentid'],
                                        "att_name": att['att_name']
                                    }
                                    att_str['adds'].append(att_json)

                # print("attachment number in this batch: " + str(len(att_str['adds'])))

                # print(final_fs)
                try:
                    result = new_fl.edit_features(adds=final_fs, use_global_ids=True, rollback_on_failure=True,
                                                  attachments=att_str)
                except Exception as ef:
                    print(f"Exception (append_data_feature_layer.new_fl.edit_features): {ef.args}.")

                print(f"Added {str(len(att_str['adds']))} attachment in batch {i}")
                print(f"Target feature count after batch {i}: ", new_fl.query(where='1=1', return_count_only=True))

                end_time = datetime.datetime.now()

        print('finished at {}'.format(str(end_time)))
        print('Duration: {}'.format(end_time - start_time))
        print(f"Target final feature count", new_fl.query(where='1=1', return_count_only=True))

    except Exception as append_data_e:
        print(f"Exception (append_data_feature_layer): {append_data_e.args}.")
def append_data_feature_layer(source_gis, target_gis, source_feature_layer_item_id,
                              target_feature_layer_item_id):
    try:
        source_item = source_gis.content.get(source_feature_layer_item_id)
        empty_service_item = target_gis.content.get(target_feature_layer_item_id)
        trg_flc = FeatureLayerCollection.fromitem(empty_service_item)

        for layer_item in source_item.layers:
            src_url = layer_item.url
            src_fl_id = src_url.split("/")[-1]
            trg_fl_id = "/" + str(src_fl_id)
            print(src_url)
            json_str = json.loads(f'{layer_item.properties}')
            del json_str['serviceItemId']
            # del json_str['sourceSpatialReference']
            temp_json = {'layers': []}
            temp_json["layers"].append(json_str)
            print("adding definition")
            trg_flc.manager.add_to_definition(temp_json)
            # time.sleep(10)
            print(f"Added definition from layer {src_fl_id} to {trg_flc.url} service definition")

            src_fl = FeatureLayer(src_url, gis=source_gis)
            src_fl_feature_count = src_fl.query(where='1=1', return_count_only=True)
            print(f"Source feature count: {src_fl_feature_count}")

            new_fl = FeatureLayer(trg_flc.url + trg_fl_id, gis=target_gis)
            new_fl_feature_count = new_fl.query(where='1=1', return_count_only=True)
            print(f"Target feature count: {new_fl_feature_count}")

            has_attachments = layer_item.properties.hasAttachments
            new_fl_atts_count = ''
            src_fl_atts_count = ''

            # if has_attachments:
            #     src_fl_atts_count = src_fl.attachments.count(where="1=1")
            #     new_fl_atts_count = new_fl.attachments.count(where="1=1")
            #
            #
            #     print(f"Source attachments count: {src_fl_atts_count}")
            #
            #     print(f"Target attachments count: {new_fl_atts_count}")
            #
            # if new_fl_feature_count == src_fl_feature_count and new_fl_atts_count == src_fl_atts_count:
            #     pass

            src_fset = src_fl.query("1=1")
            src_fset_df = src_fset.sdf
            batch_size = 100
            batches = [group for _, group in src_fset_df.groupby(src_fset_df.index // batch_size)]
            start_time = datetime.datetime.now()
            print("Batching edits...")
            print(f"Starting at {str(start_time)}")
            for i, batch_df in enumerate(batches):
                token = source_gis._con.token

                final_fs = FeatureSet.from_dataframe(batch_df)
                att_str = {"adds": [], "updates": [], "deletes": []}

                for feat in final_fs.features:
                    id_num = feat.attributes['objectid']
                    global_id = feat.attributes['globalid']
                    # print(global_id)
                    if has_attachments:
                        att_list = src_fl.attachments.get_list(oid=id_num)
                        # att_list = src_fl.attachments.search(object_ids = str(id_num),return_url=True)
                        # print(att_list)
                        if len(att_list) > 0:
                            for att in att_list:
                            # # print(att)
                                # print("attid:"+str(att['attachmentid']))
                                if att['keywords']:
                                    # print(att['keywords'])
                                    url = src_url + "/" + str(id_num) + "/attachments/" + str(att['attachmentid'])
                                    photo_encode = get_photo_encode(url, token)['Attachment']
                                    # print(url)
                                    att_json = {
                                        "parentGlobalId": global_id,
                                        "globalId": att['globalid'],
                                        "contentType": att['contentType'],
                                        "data": photo_encode,
                                        "name": att['name'],
                                        "keywords": att['keywords'],
                                        "attachmentid": att['attachmentid'],
                                        "att_name": att['att_name']
                                    }
                                    att_str['adds'].append(att_json)
                                else:
                                    # print(att['keywords'])
                                    url = src_url + "/" + str(id_num) + "/attachments/" + str(att['attachmentid'])
                                    photo_encode = get_photo_encode(url, token)['Attachment']
                                    # print(url)
                                    att_json = {
                                        "parentGlobalId": global_id,
                                        "globalId": att['globalid'],
                                        "contentType": att['contentType'],
                                        "data": photo_encode,
                                        "name": att['name'],
                                        "keywords": None,
                                        "attachmentid": att['attachmentid'],
                                        "att_name": att['att_name']
                                    }
                                    att_str['adds'].append(att_json)

                # print("attachment number in this batch: " + str(len(att_str['adds'])))

                # print(final_fs)
                try:
                    result = new_fl.edit_features(adds=final_fs, use_global_ids=True, rollback_on_failure=True,
                                                  attachments=att_str)
                except Exception as ef :
                    print(f"Exception (append_data_feature_layer.new_fl.edit_features): {ef.args}.")


                print(f"Added {str(len(att_str['adds']))} attachment in batch {i}" )
                print(f"Target feature count after batch {i}: ", new_fl.query(where='1=1', return_count_only=True))

                end_time = datetime.datetime.now()
        print('finished at {}'.format(str(end_time)))
        print('Duration: {}'.format(end_time - start_time))
        print(f"Target final feature count", new_fl.query(where='1=1', return_count_only=True))

    except Exception as append_data_e:
        print(f"Exception (append_data_feature_layer): {append_data_e.args}.")


def create_hosted_layer_views(source_gis, target_gis, source_feature_layer_item_id,
                              target_feature_layer_item_id):
    try:
        start_time = datetime.datetime.now()
        source_item = source_gis.content.get(source_feature_layer_item_id)
        empty_service_item = target_gis.content.get(target_feature_layer_item_id)
        trg_flc = FeatureLayerCollection.fromitem(empty_service_item)

        for layer_item in source_item.layers:
            src_url = layer_item.url
            src_fl_id = src_url.split("/")[-1]
            trg_fl_id = "/" + str(src_fl_id)
            print(src_url)
            json_str = json.loads(f'{layer_item.properties}')
            del json_str['serviceItemId']
            # del json_str['sourceSpatialReference']
            temp_json = {'layers': []}
            temp_json["layers"].append(json_str)
            print("adding definition")
            trg_flc.manager.add_to_definition(temp_json)
            time.sleep(10)
            print("done definition")
            new_fl = FeatureLayer(trg_flc.url + trg_fl_id, gis=target_gis)
            src_fl = FeatureLayer(src_url, gis=source_gis)
            src_fset = src_fl.query("1=1")
            src_fset_df = src_fset.sdf

            print("Source feature count: ", src_fl.query(where='1=1', return_count_only=True))


        end_time = datetime.datetime.now()
        print('finished at {}'.format(str(end_time)))
        print('Duration: {}'.format(end_time - start_time))
        print(f"Target final feature count", new_fl.query(where='1=1', return_count_only=True))

    except Exception as append_data_e:
        print(f"Exception (append_data_feature_layer): {append_data_e.args}.")


        # source_item = source_gis.content.get(source_feature_layer_item_id)
        #
        # if 'View Service' in source_item.typeKeywords:
        #     print("Layer is a hosted view, not appending data...")
        #     return None
        # target_service_item = target_gis.content.get(target_feature_layer_item_id)
        #
        # # print("Start updating capability...")
        # # # todo check if capabilities have come trhorugh with cloning
        # # # if update is not enabled, enable temporarily, to append
        # # # pm.update_capabilities(target_service_item.url, target_gis._con.token)
        # max_record_count(target_service_item.url, target_gis._con.token)
        #
        # print("Start to appending layers...")
        # ids_from = []
        # ids_to = []
        # rec = -1
        # for sublayer in source_item.layers:
        #     rec += 1
        #     # ids_from, ids_to = pm.layer_json_prepare(source_gis, target_gis, sublayer, trg_flc, rec, ids_from, ids_to)
        #
        #     ids_from, ids_to = layer_json_prepare(source_gis, target_gis, sublayer, target_service_item, rec,
        #                                           ids_from, ids_to)
        #
        #     print("data appended")
        #
        # # make target capabilities as per source
        #
        # # print(ids_from)
        # # print(ids_to)
        #
        # print("Appending layers done...")
        # return ids_from, ids_to





def clone_webmap(map_itemid, source_gis, target_gis):
    try:

        print('Processing Webmap...')
        wm_map = {}
        wm = source_gis.content.get(map_itemid)
        wm_obj = WebMap(wm)

        print(f"...cloning {wm_obj.item.title}")
        cloned_wm = target_gis.content.clone_items(items=[wm_obj.item],
                                                   copy_global_ids=True,
                                                   search_existing_items=True,
                                                   copy_data=False,
                                                   preserve_item_id=True
                                                   )
        if cloned_wm:
            wm_map[wm.id] = cloned_wm[0].id
            print(f"...completed")
            return wm_map
        else:
            return None

    except Exception as clone_wm_e:
        print(f"....failed to clone webmap {map_itemid}: {clone_wm_e.args}")


def clone_webapp(webapp, source_gis, target_gis):
    try:

        print(f'Processing item {webapp.id}...')

        print(f'App {webapp.title} (webapp.type: {webapp.type})...')

        # source_webapp_map_itemid = get_webapp_wm(source_gis, webapp) #[0]
        #
        # target_webmap = target_gis.content.get(source_webapp_map_itemid)
        # if not target_webmap:
        #     clone_webmap(migration_name, source_webapp_map_itemid, source_gis, target_gis)

        # wm_item_mapping = {src_wm: trg_wm for src_wm, trg_wm in wm_map.items()
        #                    if target_webmap.id == source_webapp_map_itemid}

        cloned_webapp = target_gis.content.clone_items(items=[webapp],
                                                       copy_global_ids=True,
                                                       search_existing_items=True,
                                                       copy_data=False,
                                                       preserve_item_id=False)  # ,
        # item_mapping=wm_item_mapping)
        if cloned_webapp:
            print(f"...completed")
            print(f"\n")

            return cloned_webapp
        else:
            print(f"{webapp.title} not cloned.")
            return None

    except Exception as e:
        print(f"....failed to clone web App {webapp.id}")
        print(str(e))
        print(f"\n")



def migration_connects(deets_csv, from_gis_alias, to_gis_alias):
    try:

        source_gis = portal_connect(deets_csv, from_gis_alias, username=None, auth_type='Pro',
                                    use_gentoken=True)
        logger.info(f'Connected to {source_gis} at {str(time.time())}')
        target_gis = portal_connect(deets_csv, to_gis_alias, username='ppgeospatial',
                                    auth_type='UP', use_gentoken=False)
        start_connected_time = time.time()
        logger.info(f'Connected to {target_gis} at {str(start_connected_time)}')
        if source_gis and target_gis:
            return source_gis, target_gis
        else:
            return None
    except Exception as e:
        print(e.args)


        # source_gis = portal_connect(deets_csv, from_gis_alias, username=None, auth_type='Pro',
        #                             use_gentoken=True)
        # logger.info(f'Connected to {source_gis} at {str(time.time())}')
        # target_gis = portal_connect(deets_csv, to_gis_alias, username='ppgeospatial',
        #                             auth_type='UP', use_gentoken=False)
        # start_connected_time = time.time()
        # logger.info(f'Connected to {target_gis} at {str(start_connected_time)}')
        # if source_gis and target_gis:
        #     return source_gis, target_gis
        # else:
        #     return None
    except Exception as e:
        print(e.args)


def get_items_list_itemids(source, hosted_fsvc):
    try:
        items_list = []
        if len(hosted_fsvc) > 0:
            for item in hosted_fsvc:
                items_list.append(item.itemid)

        else:
            return False
        # print(str(items_list))
        return items_list
    except Exception as e:
        print(e.args)


def portal_connect(csv, gis_alias, username=None, auth_type=None, use_gentoken=None):
    try:
        if username and gis_alias and auth_type == 'UP':
            df = pd.read_csv(csv)
            filtered_df = df[(df['portal_alias'] == gis_alias)]

            if len(filtered_df) > 0:
                gis_url = filtered_df.iloc[0]['url']
                u = filtered_df.iloc[0]['usr']
                p = filtered_df.iloc[0]['pwd']
                gis = GIS(gis_url, username=u, password=p, verify_cert=True, use_gen_token=use_gentoken)
                # print(username)


        elif gis_alias and auth_type == 'Pro':
            gis = GIS('Pro',verify_cert = False)
        elif gis_alias and auth_type == 'OAuth 2.0':
            df = pd.read_csv(csv)
            filtered_df = df[(df['portal_alias'] == gis_alias)]

            if len(filtered_df) > 0:
                gis_url = filtered_df.iloc[0]['url']
                app_id = filtered_df.iloc[0]['app_id']
                gis = GIS(gis_url, client_id=app_id, verify_cert=True, use_gen_token=use_gentoken)

        print(f"Connected to {gis.url} as {gis.properties.user.username} (role: {gis.properties.user.role})")

        return gis

    except Exception as e:
        print(e.args)


def migration_get_item_ids(gis, items_type, typeKeyword_filter, username, excludes=None):
    try:
        # Get content
        if username:
            items_list = gis.content.search(query=f"* AND owner:{username}",
                                            item_type=items_type, max_items=1000)
        else:
            items_list = gis.content.search('', item_type=items_type, max_items=1000)

        if items_list:
            if typeKeyword_filter:
                sorted_list = sorted([fs for fs in items_list
                                      if typeKeyword_filter in fs.typeKeywords  # 'Hosted Service'
                                      and fs.id not in excludes], key=lambda fs: fs.size, reverse=False)
            else:
                sorted_list = sorted([fs for fs in items_list
                                      if fs.id not in excludes], key=lambda fs: fs.size, reverse=False)

            itemids_list = get_items_list_itemids(gis, sorted_list)

            return itemids_list
        else:
            return None

    except Exception as e:
        print(e.args)
        logger.error(f'{e.args}')


# def process_hosted_view(process_item, source, target):
#     try:
#         pass
#         # parent_service = process_item.service
#         # if target.content.get(process_item.id):
#         #     create_hosted_view(process_item, source, target)
#         # else:
#         #     clone_item_feature_layer(process_item, source, target)
#         #     append_data_feature_layer(source, target, item_id, item_id)
#         #     item = ''
#
#         return None
#     except Exception as e:
#         print(f"Exception (create_hosted_view_def): {e.args}")
#
def create_empty_service(source_item,target_gis,out_sr, is_view):


    create_parameters = {
        "name": source_item.name,
        "description": source_item.description,
        "capabilities": "Create,Query,Editing,Update,Delete,Sync",#need to turn off the editing, update, Delete as final publication function
        "spatialReference": {"wkid": out_sr},
        "zDefault": 0,
        "properties": {
            "path": "",
            "description": "",
            "copyright": ""
        }
    }
    print(create_parameters)
    service_item = target_gis.content.create_service(name = source_item.name,
                                                     service_type = 'featureService',
                                                     create_params = create_parameters,
                                                     tags = source_item.tags,
                                                     snippet = source_item.snippet,
                                                     item_properties = {'title':source_item.title,'typeKeywords':"source-"+source_item.id},
                                                     item_id = source_item.id,
                                                     is_view = is_view
                                                     )
    return service_item


def compare_url(key, original_feature_service):
    pass


def update_view_layer_properties(vw_service, layer, original_drawing_infos=None, original_templates=None,
                                 original_types=None):   # todo: check if self here is actually the new service flc, or its flc.properties


        url = vw_service.view_sources[layer["id"]][0]
        original_feature_service = os.path.dirname(url)
        original_id = os.path.basename(url)

        if len(vw_service.view_sources[layer["id"]]) > 1:
            new_service = None
            for key, value in vw_service._clone_mapping["Services"].items():
                if compare_url(key, original_feature_service):
                    new_service = value
                    break

            # validate admin_layer_info
            if (
                    new_service is not None
                    and "adminLayerInfo" in layer
                    and "viewLayerDefinition" in layer["adminLayerInfo"]
            ):
                layer["adminLayerInfo"]["viewLayerDefinition"]["table"][
                    "sourceServiceName"
                ] = os.path.basename(
                    os.path.dirname(new_service["url"])
                )
                layer["adminLayerInfo"]["viewLayerDefinition"]["table"][
                    "sourceLayerId"
                ] = new_service["layer_id_mapping"][int(original_id)]
                if (
                        "relatedTables"
                        in layer["adminLayerInfo"]["viewLayerDefinition"][
                    "table"
                ]
                ):
                    # Update the name of the related table to use the new items name
                    for related_table in layer["adminLayerInfo"][
                        "viewLayerDefinition"
                    ]["table"]["relatedTables"]:
                        name = related_table["sourceServiceName"]
                        for k, v in vw_service.clone_mapping[
                            "Services"
                        ].items():
                            if (
                                    os.path.basename(os.path.dirname(k))
                                    == name
                            ):
                                related_table[
                                    "sourceServiceName"
                                ] = os.path.basename(
                                    os.path.dirname(v["url"])
                                )
                                if (
                                        "sourceLayerId" in related_table
                                        and "layer_id_mapping" in v
                                        and int(
                                    related_table["sourceLayerId"]
                                )
                                        in v["layer_id_mapping"]
                                ):
                                    related_table["sourceLayerId"] = v[
                                        "layer_id_mapping"
                                    ][
                                        int(
                                            related_table[
                                                "sourceLayerId"
                                            ]
                                        )
                                    ]

                admin_layer_info = layer["adminLayerInfo"]
                if (
                        _deep_get(
                            admin_layer_info, "viewLayerDefinition", "table"
                        )
                        is not None
                        and "isMultiServicesView" in layer
                        and layer["isMultiServicesView"]
                        and "geometryType" in layer
                ):
                    admin_layer_info["geometryField"]["name"] = (
                            admin_layer_info["viewLayerDefinition"][
                                "table"
                            ]["name"]
                            + "."
                            + admin_layer_info["geometryField"]["name"]
                    )

                if "tableName" in admin_layer_info:
                    del admin_layer_info["tableName"]
                if "xssTrustedFields" in admin_layer_info:
                    del admin_layer_info["xssTrustedFields"]
                if (
                        "viewLayerDefinition" in admin_layer_info
                        and "table"
                        in admin_layer_info["viewLayerDefinition"]
                ):
                    if (
                            "sourceId"
                            in admin_layer_info["viewLayerDefinition"][
                        "table"
                    ]
                    ):
                        del admin_layer_info["viewLayerDefinition"][
                            "table"
                        ]["sourceId"]
                    if (
                            "relatedTables"
                            in admin_layer_info["viewLayerDefinition"][
                        "table"
                    ]
                            and len(
                        admin_layer_info["viewLayerDefinition"][
                            "table"
                        ]["relatedTables"]
                    )
                            > 0
                    ):
                        for related_table in admin_layer_info[
                            "viewLayerDefinition"
                        ]["table"]["relatedTables"]:
                            if "sourceId" in related_table:
                                del related_table["sourceId"]

        else:
            for key, value in vw_service.clone_mapping["Services"].items():
                if compare_url(key, original_feature_service):
                    new_service = value
                    # retain this previous logic when admin_layer_info is not already avalible
                    admin_layer_info = {}
                    view_layer_definition = {}
                    view_layer_definition[
                        "sourceServiceName"
                    ] = os.path.basename(
                        os.path.dirname(new_service["url"])
                    )
                    view_layer_definition[
                        "sourceLayerId"
                    ] = new_service["layer_id_mapping"][
                        int(original_id)
                    ]
                    view_layer_definition["sourceLayerFields"] = "*"
                    admin_layer_info[
                        "viewLayerDefinition"
                    ] = view_layer_definition
                    layer["adminLayerInfo"] = admin_layer_info
                    break

        if vw_service.target.properties.isPortal:
            # Store the original drawingInfo to be updated later
            if (
                    "drawingInfo" in layer
                    and layer["drawingInfo"] is not None
            ):
                original_drawing_infos[layer["id"]] = layer[
                    "drawingInfo"
                ]

            # Store the original templates to be updated later
            if "templates" in layer and layer["templates"] is not None:
                original_templates[layer["id"]] = layer["templates"]

            # Store the original types to be updated later
            if "types" in layer and layer["types"] is not None:
                original_types[layer["id"]] = layer["types"]


def update_layer_definition(layer_def, relationships, time_infos, original_drawing_infos, original_templates, original_types,
                            _layers, _tables, _x, chunk_size, layers_and_tables, total_size, initial_extent=None):
    # Need to remove relationships first and add them back individually
    # after all layers and tables have been added to the definition
    if (
            "relationships" in layer_def
            and layer_def["relationships"] is not None
            and len(layer_def["relationships"]) != 0
    ):
        relationships[layer_def["id"]] = layer_def["relationships"]
        layer_def["relationships"] = []

    # Remove time settings first and add them back after the layer has been created
    if "timeInfo" in layer_def and layer_def["timeInfo"] is not None:
        time_infos[layer_def["id"]] = layer_def["timeInfo"]
        del layer_def["timeInfo"]

    # Need to remove all indexes duplicated for fields.
    # Services get into this state due to a bug in 10.4 and 1.2
    field_names = [f["name"].lower() for f in layer_def["fields"]]

    unique_fields = []
    if "indexes" in layer_def:
        for index in list(layer_def["indexes"]):
            fields = index["fields"].lower()
            if fields in unique_fields or fields not in field_names:
                layer_def["indexes"].remove(index)
            else:
                unique_fields.append(fields)

    # Due to a bug at 10.5.1 any domains for a double field must explicitly have a float code rather than int    # @line 2902 from original
    for field in layer_def["fields"]:
        field_type = field["type"]  # formerly _deep_get
        if field_type in ["esriFieldTypeDouble", "esriFieldTypeSingle"]:
            coded_values = get_dictionary_values_keys(field, "domain", "codedValues")  # formerly _deep_get
            if coded_values is not None:
                for coded_value in coded_values:
                    code = get_dictionary_values_keys(coded_value, "code")  # formerly _deep_get
                    if code is not None:
                        coded_value["code"] = float(code)

    # Set the extent of the feature layer to the specified default extent
    if layer_def["type"] == "Feature Layer":
        layer_def["extent"] = initial_extent

    # Remove hasViews property if exists
    if "hasViews" in layer_def:
        del layer_def["hasViews"]


def copy_hosted_featurelayer(item_id, source_gis,target_gis): #featurelayer_datasource_item=None):
    try:
        if target_gis.content.get(item_id):
            print(f"Item exists on target! Deleting...")
            target_gis.content.delete_items([item_id])

        append_data = False
        source_item = source_gis.content.get(item_id)
        print(f"Itemid {item_id}")
        print(f"typeKeywords: {source_item.typeKeywords}")
        kw = source_item.typeKeywords

        if migrate_item_type == 'Feature Layer':

            if 'Hosted Service' in kw and 'View Service' not in kw:

                src_fl = FeatureLayer(source_item.url, gis=source_gis)
                service_name = os.path.basename(os.path.dirname(source_item["url"])) #  source_item.url.split('/')[-2]  # process_item.name

                out_sr = src_fl.properties.spatialReference['wkid']

                name_available = target_gis.content.is_service_name_available(
                    service_name=service_name, service_type='featureService')

                print(f"name {service_name} is available.")
                src_flc = FeatureLayerCollection.fromitem(source_item)
                if name_available:

                    create_parameters = {
                                            "name": service_name,
                                            "description": source_item.description,
                                            "capabilities": "Create,Query,Editing,Update,Delete,Sync",
                                            # need to turn off the editing, update, Delete as final publication function
                                            "spatialReference": {"wkid": f"{out_sr}"},
                                            "zDefault": 0,
                                            "properties": {
                                                "path": "",
                                                "description": "",
                                                "copyright": ""
                                            }
                                        }

                    service_item = target_gis.content.create_service(name=service_name,
                                                                     # "service_ad7a1ce394334565bf82e26ed68ba10b",
                                                                     service_type='featureService',
                                                                     create_params=create_parameters,
                                                                     tags=[source_item.tags],
                                                                     # ['XForm', 'XForms']
                                                                     snippet="",
                                                                     item_properties={
                                                                         'title': f'{source_item.title}',
                                                                         'typeKeywords': f"source-{item_id}"},
                                                                     item_id=item_id
                                                                     )



                    # --------Begin of _clone_items
                    # --------edits to esri source, which is located: scratch/current_esrienv_clone.py

                    # # Get the definition of the original feature service
                    # src_flc = FeatureLayerCollection.fromitem(source_item)
                    # src_service_definition_copy = src_flc.properties #  self.service_definition  #
                    #
                    # # Modify the definition before passing to create the new service
                    # # name
                    # if service_name is None:
                    #     service_name = os.path.basename(os.path.dirname(source_item["url"]))
                    # # replace non-alphanumeric characters with underscore                       # commented out from original
                    # # service_name = re.sub("\W+", "_", service_name)                           # commented out from original
                    # # service_name = self._get_unique_name(target_gis, service_name)            # commented out from original
                    # src_service_definition_copy["name"] = service_name
                    #
                    # for key in ["layers", "tables", "fullExtent", "hasViews"]:
                    #     if key in src_service_definition_copy:
                    #         del src_service_definition_copy[key]
                    #
                    # # Determine if service allows schema changes
                    # source_schema_changes_allowed = True
                    # if "sourceSchemaChangesAllowed" in src_service_definition_copy:
                    #     source_schema_changes_allowed = src_service_definition_copy[
                    #         "sourceSchemaChangesAllowed"
                    #     ]
                    #
                    # # Set the spatial reference of the service
                    # if "spatialReference" in src_service_definition_copy:
                    #     out_sr = src_service_definition_copy.spatialReference['wkid']
                    #
                    # # Set the extent  of the service
                    # if "initialExtent" in src_service_definition_copy:
                    #     initial_extent = src_service_definition_copy.properties["initialExtent"]
                    #
                    #
                    # # Remove any unsupported capabilities from layer for Portal
                    # supported_capabilities = [
                    #     "Create",
                    #     "Query",
                    #     "Editing",
                    #     "Update",
                    #     "Delete",
                    #     "Uploads",
                    #     "Sync",
                    #     "Extract",
                    # ]
                    # # if target_gis.properties.isPortal: # commented out from original - not used, assuming target_gis is not None at this stage
                    # capabilities = src_service_definition_copy["capabilities"] # formerly using: _deep_get
                    # if capabilities is not None:
                    #     src_service_definition_copy["capabilities"] = ",".join(
                    #         [
                    #             x
                    #             for x in capabilities.split(",")
                    #             if x in supported_capabilities
                    #         ]
                    #     )
                    #
                    # # Preserve layer IDs from the source definition
                    # src_service_definition_copy["preserveLayerIds"] = True
                    #
                    # # Create a new feature service
                    # # In some cases isServiceNameAvailable returns true but fails to create the service with error that a service with the name already exists.
                    # #  In these cases catch the error and try again with a unique name.
                    # # In some cases create_service fails silently and returns None as the new_item.
                    # #  In these cases rasie an exception that will be caught and then try again with a unique name.
                    #
                    # create_parameters = {
                    #                             "name": service_name,
                    #                             "description": source_item.description,
                    #                             "capabilities": "Create,Query,Editing,Update,Delete,Sync",
                    #                             # need to turn off the editing, update, Delete as final publication function
                    #                             "spatialReference": {"wkid": f"{out_sr}"},
                    #                             "zDefault": 0,
                    #                             "properties": {
                    #                                 "path": "",
                    #                                 "description": "",
                    #                                 "copyright": ""
                    #                             }
                    #                         }
                    #
                    # try:
                    #     service_item = target_gis.content.create_service(name=service_name,
                    #                                                  service_type="featureService",
                    #                                                  create_params=src_service_definition_copy,
                    #                                                  tags=[source_item.tags],
                    #                                                  snippet="",
                    #                                                  item_properties={
                    #                                                      'title': f'{source_item.title}',
                    #                                                      'typeKeywords': f"source-{item_id}"},
                    #                                                  is_view=source_item.is_view,
                    #                                                  # folder=source_item.folder,           # not using folders
                    #                                                  # owner=source_item.owner,             # not assigning to a different owner
                    #                                                  item_id=item_id,
                    #                                                  )

                        # old:--------
                        # service_item = target_gis.content.create_service(name=service_name,
                        #                                                  # "service_ad7a1ce394334565bf82e26ed68ba10b",
                        #                                                  service_type='featureService',
                        #                                                  create_params=create_parameters,
                        #                                                  tags=[source_item.tags],
                        #                                                  # ['XForm', 'XForms']
                        #                                                  snippet="",
                        #                                                  item_properties={
                        #                                                      'title': f'{source_item.title}',
                        #                                                      'typeKeywords': f"source-{item_id}"},
                        #                                                  item_id=item_id
                        #                                                  )
                        # ------------------ end of old


                        # if service_item is None:
                        #     raise RuntimeError(f"New service {service_name} could not be created.")

                # except RuntimeError as ex:
                #     if "already exists" in str(ex):
                #         print(f"{service_name} already exists")

                            # Removed: rename to some unique name and create -- Not doing this
                            # name = self._get_unique_name(self.target, name, True)
                            # service_definition["name"] = name
                            # new_item = self.target.content.create_service(
                            #     name,
                            #     service_type="featureService",
                            #     create_params=service_definition,
                            #     folder=self.folder,
                            #     owner=self.owner,
                            #     item_id=item_id,
                            # )


                    print(f'Service created:{service_item.url}')

                else:
                    print(f'Service {service_name} already exists.')

                    service_item = target_gis.content.get(item_id)

                    print(f"Item on target is {service_item.itemid} ")

                    print(f"Item url {service_item.url} ")




                # Begin of _esri--------------------------
                # # Get the layer and table definitions from the original service and prepare them for the new service
                # layers_definition = src_service_definition_copy["layers"]   # .layers_definition
                # relationships = {}
                # time_infos = {}
                # original_drawing_infos = {}
                # original_templates = {}
                # original_types = {}
                # _layers = []
                # _tables = []
                # _x = 0
                # chunk_size = 20
                # layers_and_tables = []
                # total_size = len(
                #     layers_definition["layers"] + layers_definition["tables"]
                # )
                # for layer in layers_definition["layers"] + layers_definition["tables"]:
                #     update_layer_definition(layer,
                #                             relationships,
                #                             time_infos,
                #                             original_drawing_infos,
                #                             original_templates ,
                #                             original_types ,
                #                             _layers,
                #                             _tables ,
                #                             _x ,
                #                             chunk_size,
                #                             layers_and_tables,
                #                             total_size )
                #
                #     if service_item.is_view:
                #         update_view_layer_properties(vw_service, layer)

                    # Remove any unsupported capabilities from layer for Portal
                    # supported_capabilities = [
                    #     "Create",
                    #     "Query",
                    #     "Editing",
                    #     "Update",
                    #     "Delete",
                    #     "Uploads",
                    #     "Sync",
                    #     "Extract",
                    # ]

                    # if vw_service.target.properties.isPortal:    ### up to here...!!!
                    #     # Remove any unsupported capabilities from layer for Portal
                    #     capabilities = get_dictionary_values_keys(layer, "capabilities")
                    #     if capabilities is not None:
                    #         layer["capabilities"] = ",".join(
                    #             [
                    #                 x
                    #                 for x in capabilities.split(",")
                    #                 if x in supported_capabilities
                    #             ]
                    #         )
                    #
                    # if layer["type"] == "Feature Layer":
                    #     _layers.append(layer)
                    # if layer["type"] == "Table":
                    #     _tables.append(layer)
                    #
                    # if (_x + 1) % chunk_size == 0 or (_x + 1) == total_size:
                    #     layers_tables = {}
                    #     layers = copy.deepcopy(_layers) if len(_layers) > 0 else []
                    #     if self.is_view:
                    #         for layer in layers:
                    #             del layer["fields"]
                    #     layers_tables["layers"] = layers
                    #
                    #     tables = copy.deepcopy(_tables) if len(_tables) > 0 else []
                    #     if self.is_view:
                    #         for table in tables:
                    #             del table["fields"]
                    #     layers_tables["tables"] = tables
                    #
                    #     layers_and_tables.append(layers_tables)
                    #     _layers = []
                    #     _tables = []
                    # _x += 1


                    # # Need to remove relationships first and add them back individually
                    # # after all layers and tables have been added to the definition
                    # if (
                    #         "relationships" in layer
                    #         and layer["relationships"] is not None
                    #         and len(layer["relationships"]) != 0
                    # ):
                    #     relationships[layer["id"]] = layer["relationships"]
                    #     layer["relationships"] = []
                    #
                    # # Remove time settings first and add them back after the layer has been created
                    # if "timeInfo" in layer and layer["timeInfo"] is not None:
                    #     time_infos[layer["id"]] = layer["timeInfo"]
                    #     del layer["timeInfo"]
                    #
                    # # Need to remove all indexes duplicated for fields.
                    # # Services get into this state due to a bug in 10.4 and 1.2
                    # field_names = [f["name"].lower() for f in layer["fields"]]
                    #
                    # unique_fields = []
                    # if "indexes" in layer:
                    #     for index in list(layer["indexes"]):
                    #         fields = index["fields"].lower()
                    #         if fields in unique_fields or fields not in field_names:
                    #             layer["indexes"].remove(index)
                    #         else:
                    #             unique_fields.append(fields)
                    #
                    # # Due to a bug at 10.5.1 any domains for a double field must explicitly have a float code rather than int    # @line 2902 from original
                    # for field in layer["fields"]:
                    #     field_type = field["type"]   # formerly _deep_get
                    #     if field_type in ["esriFieldTypeDouble", "esriFieldTypeSingle"]:
                    #         coded_values = get_dictionary_values_keys(field, "domain", "codedValues")   # formerly _deep_get
                    #         if coded_values is not None:
                    #             for coded_value in coded_values:
                    #                 code = _deep_get(coded_value, "code")
                    #                 if code is not None:
                    #                     coded_value["code"] = float(code)
                    #
                    # # Set the extent of the feature layer to the specified default extent
                    # if layer["type"] == "Feature Layer":
                    #     layer["extent"] = initial_extent
                    #
                    # # Remove hasViews property if exists
                    # if "hasViews" in layer:
                    #     del layer["hasViews"]
                    #
                    # # Update the view layer source properties
                    # def update_view_layer_properties(vw_service, layer_def):
                    #     if service_item.is_view:  # todo: check if self here is actually the new service flc, or its flc.properties
                    #
                    #         update_view_layer_properties(vw_service, layer_def)
                    #         url = self.view_sources[layer["id"]][0]
                    #         original_feature_service = os.path.dirname(url)
                    #         original_id = os.path.basename(url)
                    #
                    #         if len(self.view_sources[layer["id"]]) > 1:
                    #             new_service = None
                    #             for key, value in self._clone_mapping["Services"].items():
                    #                 if _compare_url(key, original_feature_service):
                    #                     new_service = value
                    #                     break
                    #
                    #             # validate admin_layer_info
                    #             if (
                    #                     new_service is not None
                    #                     and "adminLayerInfo" in layer
                    #                     and "viewLayerDefinition" in layer["adminLayerInfo"]
                    #             ):
                    #                 layer["adminLayerInfo"]["viewLayerDefinition"]["table"][
                    #                     "sourceServiceName"
                    #                 ] = os.path.basename(
                    #                     os.path.dirname(new_service["url"])
                    #                 )
                    #                 layer["adminLayerInfo"]["viewLayerDefinition"]["table"][
                    #                     "sourceLayerId"
                    #                 ] = new_service["layer_id_mapping"][int(original_id)]
                    #                 if (
                    #                         "relatedTables"
                    #                         in layer["adminLayerInfo"]["viewLayerDefinition"][
                    #                     "table"
                    #                 ]
                    #                 ):
                    #                     # Update the name of the related table to use the new items name
                    #                     for related_table in layer["adminLayerInfo"][
                    #                         "viewLayerDefinition"
                    #                     ]["table"]["relatedTables"]:
                    #                         name = related_table["sourceServiceName"]
                    #                         for k, v in self._clone_mapping[
                    #                             "Services"
                    #                         ].items():
                    #                             if (
                    #                                     os.path.basename(os.path.dirname(k))
                    #                                     == name
                    #                             ):
                    #                                 related_table[
                    #                                     "sourceServiceName"
                    #                                 ] = os.path.basename(
                    #                                     os.path.dirname(v["url"])
                    #                                 )
                    #                                 if (
                    #                                         "sourceLayerId" in related_table
                    #                                         and "layer_id_mapping" in v
                    #                                         and int(
                    #                                     related_table["sourceLayerId"]
                    #                                 )
                    #                                         in v["layer_id_mapping"]
                    #                                 ):
                    #                                     related_table["sourceLayerId"] = v[
                    #                                         "layer_id_mapping"
                    #                                     ][
                    #                                         int(
                    #                                             related_table[
                    #                                                 "sourceLayerId"
                    #                                             ]
                    #                                         )
                    #                                     ]
                    #
                    #                 admin_layer_info = layer["adminLayerInfo"]
                    #                 if (
                    #                         _deep_get(
                    #                             admin_layer_info, "viewLayerDefinition", "table"
                    #                         )
                    #                         is not None
                    #                         and "isMultiServicesView" in layer
                    #                         and layer["isMultiServicesView"]
                    #                         and "geometryType" in layer
                    #                 ):
                    #                     admin_layer_info["geometryField"]["name"] = (
                    #                             admin_layer_info["viewLayerDefinition"][
                    #                                 "table"
                    #                             ]["name"]
                    #                             + "."
                    #                             + admin_layer_info["geometryField"]["name"]
                    #                     )
                    #
                    #                 if "tableName" in admin_layer_info:
                    #                     del admin_layer_info["tableName"]
                    #                 if "xssTrustedFields" in admin_layer_info:
                    #                     del admin_layer_info["xssTrustedFields"]
                    #                 if (
                    #                         "viewLayerDefinition" in admin_layer_info
                    #                         and "table"
                    #                         in admin_layer_info["viewLayerDefinition"]
                    #                 ):
                    #                     if (
                    #                             "sourceId"
                    #                             in admin_layer_info["viewLayerDefinition"][
                    #                         "table"
                    #                     ]
                    #                     ):
                    #                         del admin_layer_info["viewLayerDefinition"][
                    #                             "table"
                    #                         ]["sourceId"]
                    #                     if (
                    #                             "relatedTables"
                    #                             in admin_layer_info["viewLayerDefinition"][
                    #                         "table"
                    #                     ]
                    #                             and len(
                    #                         admin_layer_info["viewLayerDefinition"][
                    #                             "table"
                    #                         ]["relatedTables"]
                    #                     )
                    #                             > 0
                    #                     ):
                    #                         for related_table in admin_layer_info[
                    #                             "viewLayerDefinition"
                    #                         ]["table"]["relatedTables"]:
                    #                             if "sourceId" in related_table:
                    #                                 del related_table["sourceId"]
                    #
                    #         else:
                    #             for key, value in self._clone_mapping["Services"].items():
                    #                 if _compare_url(key, original_feature_service):
                    #                     new_service = value
                    #                     # retain this previous logic when admin_layer_info is not already avalible
                    #                     admin_layer_info = {}
                    #                     view_layer_definition = {}
                    #                     view_layer_definition[
                    #                         "sourceServiceName"
                    #                     ] = os.path.basename(
                    #                         os.path.dirname(new_service["url"])
                    #                     )
                    #                     view_layer_definition[
                    #                         "sourceLayerId"
                    #                     ] = new_service["layer_id_mapping"][
                    #                         int(original_id)
                    #                     ]
                    #                     view_layer_definition["sourceLayerFields"] = "*"
                    #                     admin_layer_info[
                    #                         "viewLayerDefinition"
                    #                     ] = view_layer_definition
                    #                     layer["adminLayerInfo"] = admin_layer_info
                    #                     break
                    #
                    #         if self.target.properties.isPortal:
                    #             # Store the original drawingInfo to be updated later
                    #             if (
                    #                     "drawingInfo" in layer
                    #                     and layer["drawingInfo"] is not None
                    #             ):
                    #                 original_drawing_infos[layer["id"]] = layer[
                    #                     "drawingInfo"
                    #                 ]
                    #
                    #             # Store the original templates to be updated later
                    #             if "templates" in layer and layer["templates"] is not None:
                    #                 original_templates[layer["id"]] = layer["templates"]
                    #
                    #             # Store the original types to be updated later
                    #             if "types" in layer and layer["types"] is not None:
                    #                 original_types[layer["id"]] = layer["types"]
                    #
                    # if service_item.is_view:
                    #     update_view_layer_properties(vw_service, layer)
                    #
                    # if self.target.properties.isPortal:
                    #     # Remove any unsupported capabilities from layer for Portal
                    #     capabilities = _deep_get(layer, "capabilities")
                    #     if capabilities is not None:
                    #         layer["capabilities"] = ",".join(
                    #             [
                    #                 x
                    #                 for x in capabilities.split(",")
                    #                 if x in supported_capabilities
                    #             ]
                    #         )
                    #
                    # if layer["type"] == "Feature Layer":
                    #     _layers.append(layer)
                    # if layer["type"] == "Table":
                    #     _tables.append(layer)
                    #
                    # if (_x + 1) % chunk_size == 0 or (_x + 1) == total_size:
                    #     layers_tables = {}
                    #     layers = copy.deepcopy(_layers) if len(_layers) > 0 else []
                    #     if self.is_view:
                    #         for layer in layers:
                    #             del layer["fields"]
                    #     layers_tables["layers"] = layers
                    #
                    #     tables = copy.deepcopy(_tables) if len(_tables) > 0 else []
                    #     if self.is_view:
                    #         for table in tables:
                    #             del table["fields"]
                    #     layers_tables["tables"] = tables
                    #
                    #     layers_and_tables.append(layers_tables)
                    #     _layers = []
                    #     _tables = []
                    # _x += 1












                # insert feature data and attachments
                # if append_data:
                append_data_feature_layer(source_gis, target_gis, item_id, item_id)

                # src_flc = FeatureLayerCollection.fromitem(source_item)
                # target_flc = FeatureLayerCollection.fromitem(service_item)



                if src_flc.properties["hasViews"] == True:
                    views_items = source_item.related_items(rel_type="Service2Service", direction="forward")
                    for hv_item in views_items:

                        # ----from esri:
                        # if self.is_view:
                        #     properties = [
                        #         "name",
                        #         "isView",
                        #         "sourceSchemaChangesAllowed",
                        #         "isUpdatableView",
                        #         "capabilities",
                        #         "isMultiServicesView",
                        #     ]
                        #     service_definition_copy = copy.deepcopy(service_definition)
                        #     for key, value in service_definition_copy.items():
                        #         if key not in properties:
                        #             del service_definition[key]

                        # --------

                        source_item_flc = FeatureLayerCollection.fromitem(hv_item)

                        print(source_item.name)

                        name_available = target_gis.content.is_service_name_available(service_name=hv_item.name,
                                                                                      service_type='featureService')
                        print(name_available)
                        is_view = source_item_flc.properties['isView']
                        print(is_view)

                        if not name_available:
                            print('view service is existing! Deleting...')
                            target_gis.content.delete_items([hv_item.itemid])

                        trg_vw_item = create_empty_service(hv_item, target_gis, out_sr, is_view)

                        trg_flc = FeatureLayerCollection.fromitem(trg_vw_item)

                        for layer_item in hv_item.layers:

                            src_url = layer_item.url
                            src_fl_id = src_url.split("/")[-1]
                            trg_fl_id = "/" + str(src_fl_id)
                            print(src_url)


                            # View definition
                            json_str = json.loads(f'{layer_item.properties}')
                            # print(json_str)

                            trg_url = trg_flc.url + trg_fl_id
                            vw_svc_name = src_flc.url.split('/')[-2]

                            del json_str['serviceItemId']
                            if layer_item.properties['isView'] is True:
                                update_str = {"url": trg_url,
                                              "adminLayerInfo": {
                                    "viewLayerDefinition": {"sourceServiceName": vw_svc_name,
                                                            "sourceLayerId": int(src_fl_id), "sourceLayerFields": "*"}}}
                                print(update_str)
                                json_str.update(update_str)
                            # del json_str['sourceSpatialReference']
                            temp_json = {"layers": []}
                            temp_json["layers"].append(json_str)

                            # print(temp_json)
                            trg_flc.manager.add_to_definition(temp_json)
                            trg_flc.manager.refresh()

                            if layer_item.properties['isView'] is True:

                                trg_flc_fields = [field['name'] for field in
                                                  trg_flc.layers[int(src_fl_id)].properties.fields]
                                source_view_fields = [field['name'] for field in layer_item.properties.fields]
                                print(trg_flc_fields)
                                print(source_view_fields)
                                update_str = {"fields": []}
                                for fields in trg_flc_fields:
                                    if fields in source_view_fields:
                                        json_str = {"name": fields, "visible": True}
                                        update_str["fields"].append(json_str)
                                    else:
                                        json_str = {"name": fields, "visible": False}
                                        update_str["fields"].append(json_str)

                                # print(update_str)
                                trg_flc.layers[int(src_fl_id)].manager.update_definition(update_str)
                        print('all done')

        return service_item
        # else:
        #     pass  # code for other item types

    except Exception as e:
        print(f"Exception (copy_hosted_featurelayer): {e.args}")
        print(f"Exception Type: {sys.exc_info()[0]}")
        print(f"Exception Value: {sys.exc_info()[1]}")
        print(f"Exception Traceback line: {sys.exc_info()[2].tb_lineno}")
        print(f"Exception Traceback instruction: {sys.exc_info()[2].tb_lasti}")

        # logger.error(f"Running time cloning feature layers: {round(time.time() - start_hfs_processing_time, 2)} s")
        # logger.error(f"Exception Type: {sys.exc_info()[0]}")
        # logger.error(f"Exception Value: {sys.exc_info()[1]}")
        # logger.error(f"Exception Traceback line: {sys.exc_info()[2].tb_lineno}")
        # logger.error(f"Exception Traceback instruction: {sys.exc_info()[2].tb_lasti}")


if __name__ == '__main__':
    try:
        start_time = str(datetime.datetime.now().strftime('%d%m%Y'))
        logger.info(f'Migration {migration_name} started at {start_time}')
    
        # connect
        source_gis, target_gis = migration_connects(portals_csv, usr_args_from_gis_alias_name, usr_args_to_gis_alias_name)

        # get content itemids
        exclude_list = ['bb2e4ed52cad420dbd8d4bfa9f699209', 'a01c570fb99a4520a8124c99fb2ca8a0',
                        '38c1e4ebb8b74743a20de3901a298fa6', '0ff35c341c344defbe088b291a6c948d',
                        '2c0c277614994e7891d2ba1cf7f77a70',
                        '417993ccc4824174899d66586b286a8c', 'ade65c8326d24b63b65df84330b8e63d',
                        '0ff35c341c344defbe088b291a6c948d',
                        '0ff35c341c344defbe088b291a6c948d', '794793d6b2834897bf6c85c0a2106327',
                        'af51c6c82b7446c59cd44e54dd819055',
                        'ade65c8326d24b63b65df84330b8e63d', '8650d9d1cb06444ea87651b66e757864',
                        '417993ccc4824174899d66586b286a8c','b650e8cd342f4cdbb5fca7f966f8224d']#,
                        #]



        migrate_itemids = [
                           'b650e8cd342f4cdbb5fca7f966f8224d', '2c0c277614994e7891d2ba1cf7f77a70',
                           '23c2d75e6ac64705958b9da3abb63d75',
                           'a8a254a81118470db2bed70de274240d'] # todo: delete , with related view if any,retry 8650d9d1cb06444ea87651b66e757864

        process_itemids_list = [x for x in migrate_itemids if x not in exclude_list]


        # if migrate_item_type == 'Feature Layer':
        #     item_ids_to_migrate = migration_get_item_ids(source_gis, migrate_item_type, 'Hosted Service',
        #                                                  usr_args_process_username,
        #                                                  excludes=exclude_list)
        #     migrate_itemids.extend(item_ids_to_migrate)
        #
        # elif migrate_item_type in ['Web Map', 'Dashboard', 'Web Mapping Application', 'StoryMap']:
        #     item_ids_to_migrate = migration_get_item_ids(source_gis, migrate_item_type, '', usr_args_process_username,
        #                                                  excludes=exclude_list)
        #     migrate_itemids.extend(item_ids_to_migrate)


        #sorted #todo
        # items_list = get_items_list_itemids(source_gis, migrate_itemids)
        #
        # sorted_list = sorted([fs for fs in items_list
        #                       if fs.itemid not in exclude_list], key=lambda fs: fs.size, reverse=False)
        #
        # for item in sorted_list:
        #     item_id = item.itemid
        print(f"Items to process: {len(process_itemids_list)}")
        print(f"Items : {process_itemids_list}")
        for item_id in process_itemids_list:  # ['38c1e4ebb8b74743a20de3901a298fa6']: #migrate_itemids: ## ['375ccef512c64a599c3e3a8d260aa7c5']:  # ['d0cd7a294b3a43f0b37cce851e7ca6df'] ['d0cd7a294b3a43f0b37cce851e7ca6df']: migrate_itemid

            copy_hosted_featurelayer(item_id, source_gis,target_gis)

    except Exception as e:
        print(f"Exception: {e.args}. Continuing with next {migrate_item_type}...")
        #continue
# elif migrate_item_type == 'Web Map':
# if web_map_has_hosted_only(process_item, source):
#     print("Web Map contains hosted layers only. Cloning...")
#     clone_webmap(process_item, source, target)
# else:
#     continue
# elif migrate_item_type in ['Dashboard', 'StoryMap', 'Web Mapping Application']:
# clone_webapp(process_item, source, target)
