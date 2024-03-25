import arcpy, json, os, shutil
from arcgis.gis import GIS


# Variables
sourcePortal = arcpy.GetParameterAsText(0)
sourceIWA = arcpy.GetParameterAsText(1)
sourceUsername = arcpy.GetParameterAsText(2)
sourcePassword = arcpy.GetParameterAsText(3)
sourceUser = arcpy.GetParameterAsText(4)
content = arcpy.GetParameterAsText(5)
operationalLayers = arcpy.GetParameterAsText(6)
targetPortal = arcpy.GetParameterAsText(7)
targetIWA = arcpy.GetParameterAsText(8)
targetUsername = arcpy.GetParameterAsText(9)
targetPassword = arcpy.GetParameterAsText(10)
targetOwner = arcpy.GetParameterAsText(11)
targetFolder = arcpy.GetParameterAsText(12)
scratchFolder = arcpy.env.scratchFolder

# Function to update thumbnail
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

# Sign into source portal
arcpy.AddMessage("Signing into source portal")
source = GIS(sourcePortal, sourceUsername, sourcePassword, verify_cert=False)

# Sign into target portal
arcpy.AddMessage("Signing into target portal")
target = GIS(targetPortal, targetUsername, targetPassword, verify_cert=False)

# Create scratch Directory
scratchFolder = os.path.join(arcpy.env.scratchFolder, 'Thumbnails')
if not os.path.exists(scratchFolder):
    os.mkdir(scratchFolder)

# Get Web Map ID & Title
arcpy.AddMessage("Getting Web Map ID")
webMapID = content.split(' - ')[-1]
webMapTitle = source.content.get(webMapID).title

# Get Web Map JSON
arcpy.AddMessage("Getting Web Map JSON")
webMap = source.content.get(webMapID)
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
        result1 = source.content.search(lyr1[0:-2])
        result2 = target.content.search(lyr2[0:-2])
    else:
        result1 = source.content.search(lyr1)
        result2 = target.content.search(lyr2)
    if len(result1) > 0 and len(result2) > 0:
        webMapJSON = webMapJSON.replace(result1[0].id, result2[0].id)
    x += 1

# Check if web map exists
exists = False
for result in target.content.search(f"title:{webMapTitle} AND owner:{targetOwner}", item_type='Web Map'):
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
        webMapItem = target.content.add(item_properties=webmap_properties, owner=targetOwner)
    else:
        webMapItem = target.content.add(item_properties=webmap_properties, owner=targetOwner, folder=targetFolder)
elif exists == True:
    arcpy.AddMessage(f"Updating existing web map {webMap2.title}")
    webMap2.update(item_properties=webmap_properties)
    webMapItem = webMap2

# Update Thumbnail
arcpy.AddMessage("Updating thumbnail")
updateThumbnail(webMap, webMapItem)

# Call function to clear scratch workspace
clearScratchWorkspace()