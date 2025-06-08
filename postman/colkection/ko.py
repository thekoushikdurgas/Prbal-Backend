import json

def name_item(subitem):
    subitem['request'] = {
                "method": "POST",
                "header": [
                    {
                        "key": "Authorization",
                        "value": "Bearer {{access_token}}",
                        "type": "text"
                    }
                ]
            }
    if 'event' in list(subitem.keys()):
        for event in subitem['event']:
                event['script'] = {
                    "type": "text/javascript",
                    "exec": [
                        "pm.variables.set('access_token', pm.response.json().access_token);"
                    ]
                }
    subitem['response'] = [
                {"name": "Success response "},
                {"name": "Error response "}
            ]
def clean_item(subitem):
     if 'item' in list(subitem.keys()):
          for item in subitem['item']:
               clean_item(item)
     else:
          name_item(subitem)

with open(r'postman\colkection\Products.postman_collection.json', 'r') as file:
    data = json.load(file)

# for item in data['item']:
#     if item['item'] is not None:
#         name_item(item)
#     else:
#         continue

for item in data['item']:
    clean_item(item)

with open(r'postman\colkection\Products.postman_collection.json', 'w') as file:
    json.dump(data, file, indent=4)