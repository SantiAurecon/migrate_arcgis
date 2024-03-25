import arcpy, json, os, shutil
import pandas as pd
from arcgis.gis import GIS
import logging
import datetime

from arcgis.mapping import WebMap

# Variables
# sourcePortal = arcpy.GetParameterAsText(0)
# sourceIWA = arcpy.GetParameterAsText(1)
# sourceUsername = arcpy.GetParameterAsText(2)
# sourcePassword = arcpy.GetParameterAsText(3)
# sourceUser = arcpy.GetParameterAsText(4)
# content = arcpy.GetParameterAsText(5)
# operationalLayers = arcpy.GetParameterAsText(6)
# targetPortal = arcpy.GetParameterAsText(7)
# targetIWA = arcpy.GetParameterAsText(8)
# targetUsername = arcpy.GetParameterAsText(9)
# targetPassword = arcpy.GetParameterAsText(10)
# targetOwner = arcpy.GetParameterAsText(11)
# targetFolder = arcpy.GetParameterAsText(12)
arcpy.env.scratchFolder = '' #todo
scratchFolder = arcpy.env.scratchFolder
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

# Parameters
usr_args_from_gis_alias_name = 'ISP_OAUTH2'  # 'Geoportal_DEV'  # 'ISP_OAUTH2' #'Geoportal_DEV' #'ISP_OAUTH2'
usr_args_to_gis_alias_name = 'DIGITAL_DEV_UP'  # 'DIGITAL_DEV'  # 'Geoportal_DEV' #'DIGITAL_DEV'  # 'Geoportal_DEV'  #
migration_name = "ISP_to_DIGITAL_DEV"  # "portaldev_to_digital_dev" #"ISP_to_DIGITAL_DEV" #
# migrate_itemid = '96970af38ade49d4845671d442a9c1cc'
usr_args_process_username = ''  # 'Katleya.DelaCruz@aurecongroup.com'  # 'wilson.sahmet@aurecongroup.com'
migrate_item_type = "Web Map"
# migrate_item_type = 'StoryMap'  # 'Dashboard'   #,'Web Mapping Application',


def updateThumbnail(previousItem, newItem):
    '''Function to update the web map/apps thumbnail'''
    thumbNail = previousItem.download_thumbnail(scratchFolder)
    if thumbNail:
        newItem.update(thumbnail=thumbNail)
        os.remove(thumbNail)

# Funtion to clear scratch workspace
def clearScratchWorkspace():
    '''Function will remove all contents from scratch workspace'''

    arcpy.AddMessage("Cleaning up scratch workspace")
    shutil.rmtree(scratchFolder)


def update_urls_webmap_json(content, source_gis, operationalLayers, target_gis):
    try:

        # Get Web Map ID & Title
        arcpy.AddMessage("Getting Web Map ID")
        webMapID = content.split(' - ')[-1]
        webMapTitle = source_gis.content.get(webMapID).title

        # Get Web Map JSON
        arcpy.AddMessage("Getting Web Map JSON")
        webMap = source_gis.content.get(webMapID)
        webMapDict = webMap.get_data(try_json=True)

        # Convert dict to JSON
        arcpy.AddMessage("Converting dict to JSON")
        webMapJSON = json.dumps(webMapDict)

        # Replace service URLs
        arcpy.AddMessage("Replacing service URLs")
        x = 0
        layers = operationalLayers.split(';')
        while x < len(layers):
            lyr1 = layers[x].split(" ")[0]
            lyr2 = layers[x].split(" ")[1]
            webMapJSON = webMapJSON.replace(lyr1, lyr2)

            # Replace item IDs
            if lyr1[-2] == '/':
                result1 = source_gis.content.search(lyr1[0:-2])
                result2 = target_gis.content.search(lyr2[0:-2])
            else:
                result1 = source_gis.content.search(lyr1)
                result2 = target_gis.content.search(lyr2)
            if len(result1) > 0 and len(result2) > 0:
                webMapJSON = webMapJSON.replace(result1[0].id, result2[0].id)
            x += 1
            return webMapJSON
    except Exception as e:
        print(f"Exception (update_urls_webmap_json): {e.args}")
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


def web_map_hosted_only(wm_item_id, source_gis):
    try:
        wm = WebMap(wm_item)
        for web_map_layer in wm.layers:
            # print(f"Layer: {web_map_layer}")
            if web_map_layer.itemId:
                layer_item = source_gis.content.get(web_map_layer.itemId)
                if web_map_layer.get(
                        'layerType') != 'ArcGISFeatureLayer' and 'Hosted Service' not in layer_item.typeKeywords:
                    print(f"Non-hosted service found! ({web_map_layer.url})")
                    return False
            else:
                return False
            return wm

    except Exception as ewm_hostedonly_e:
        print(f"Exception - web_map_has_hosted_only: {ewm_hostedonly_e.args} when analysing {wm_item.id}.")

def main(webMapID, operationalLayers=None, targetOwner=None, targetFolder=None):
    try:
        start_time = str(datetime.datetime.now().strftime('%d%m%Y'))
        logger.info(f'Migration {migration_name} started at {start_time}')

        # connect
        source_gis, target_gis = migration_connects(portals_csv, usr_args_from_gis_alias_name,
                                                    usr_args_to_gis_alias_name)
        # Create scratch Directory
        scratchFolder = os.path.join(arcpy.env.scratchFolder, 'Thumbnails')
        if not os.path.exists(scratchFolder):
            os.mkdir(scratchFolder)

        # Get Web Map ID & Title
        arcpy.AddMessage("Getting Web Map ID")
        #webMapID = web_map.split(' - ')[-1]   # todo , or pass mapid insted to the main function

        webMapTitle = source_gis.content.get(webMapID).title

        # Get Web Map JSON
        arcpy.AddMessage("Getting Web Map JSON")
        webMap = source_gis.content.get(webMapID)
        webMapDict = webMap.get_data(try_json=True)

        # Convert dict to JSON
        arcpy.AddMessage("Converting dict to JSON")
        webMapJSON = json.dumps(webMapDict)

        # Replace service URLs
        arcpy.AddMessage("Replacing service URLs")
        x = 0
        layers = operationalLayers.split(';')
        while x < len(layers):
            lyr1 = layers[x].split(" ")[0]
            lyr2 = layers[x].split(" ")[1]
            webMapJSON = webMapJSON.replace(lyr1, lyr2)

            # Replace item IDs
            if lyr1[-2] == '/':
                result1 = source_gis.content.search(lyr1[0:-2])
                result2 = target_gis.content.search(lyr2[0:-2])
            else:
                result1 = source_gis.content.search(lyr1)
                result2 = target_gis.content.search(lyr2)
            if len(result1) > 0 and len(result2) > 0:
                webMapJSON = webMapJSON.replace(result1[0].id, result2[0].id)
            x += 1

        # Check if web map exists
        exists = False
        for result in target_gis.content.search(f"title:{webMapTitle} AND owner:{targetOwner}", item_type='Web Map'):
            if result['title'] == webMapTitle:
                webMap2 = result
                exists = True

        # Create a copy of web map/update existing web map
        webmap_properties = {'title': webMap.title,
                             'type': 'Web Map',
                             'snippet': webMap.snippet,
                             'description': webMap.description,
                             'tags': webMap.tags,
                             'text': webMapJSON}

        if exists == False:
            arcpy.AddMessage("Creating a copy of the web map")
            if targetFolder == 'ROOT':
                webMapItem = target_gis.content.add(item_properties=webmap_properties, owner=targetOwner)
            else:
                webMapItem = target_gis.content.add(item_properties=webmap_properties, owner=targetOwner,
                                                folder=targetFolder)
        elif exists == True:
            arcpy.AddMessage(f"Updating existing web map {webMap2.title}")
            webMap2.update(item_properties=webmap_properties)
            webMapItem = webMap2

        # Update Thumbnail
        arcpy.AddMessage("Updating thumbnail")
        updateThumbnail(webMap, webMapItem)

        # Call function to clear scratch workspace
        clearScratchWorkspace()
    except Exception as e:
        print(e.args)


if __name__ == '__main__':
    try:
        #map_itemid='476b7a011eb34f1dad03ae5e76a2dc90'
        operational_Layers=''
        target_Owner=''
        target_Folder=''
        time_start = str(datetime.datetime.now().strftime('%d%m%Y'))
        logger.info(f'Migration {migration_name} started at {time_start}')

        # connect
        source, target = migration_connects(portals_csv, usr_args_from_gis_alias_name, usr_args_to_gis_alias_name)

        # get content itemids
        exclude_list = []

        migrate_itemids = ['476b7a011eb34f1dad03ae5e76a2dc90']

        process_itemids_list = [x for x in migrate_itemids if x not in exclude_list]

        # migrate
        for item_id in process_itemids_list:

            try:
                start_processing_time = datetime.datetime.now()
                current_formatted_time = start_processing_time.strftime('%H:%M:%S')
                wm_item = source.content.get(item_id)
                wm = web_map_hosted_only(wm_item, source)
                if wm:
                    print("Web Map contains hosted layers only. Copying...")
                    operationalLayers = wm.layers
                    main(wm, operational_Layers, target_Owner, target_Folder)
                else:
                    continue

            except Exception as e:
                print(f"Exception: {e.args}. Continuing with next WebMap...")
                continue


        # main(item_id, operational_Layers, target_Owner, target_Folder)



    except Exception as e:
        print(e.args)




