<div align="center">
  <img src="images/logo_meeting_reaction.png" alt="Meeting Reaction logo" width="370" height="57" />

  ---
  An application for viewing instant feedback during a meeting.

  This feedback can be based on people’s speech or live reactions captured through facial recongition.
</div>


## Meeting Reaction Functions

These functions are used to be the back-end (API) for processing request from front-end and IoT device (Raspberry Pi).

## Solution components

- [x] Back-end Azure Functions 2 (this)
- [x] Front-end React ([repo](https://github.com/BeyondLabsEY/meeting-reaction-web))
- [x] Desktop Raspberry Pi Python 3 app ([repo](https://github.com/BeyondLabsEY/meeting-reaction-rasp))

## Infrastructure Requirements

- [x] Azure account
- [x] Region availability to use Azure Functions 2.0
- [x] Azure Blob storage
- [x] Azure Table
- [x] Azure Queue
- [x] Azure Face Recognition
- [x] Azure Text to Speech (aka _Bing Search_)
  
## Development Requirements

- [x] VisualStudio Code aka [_VSCode_](https://code.visualstudio.com/)
- [x] [Python extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python)
- [x] Python compiler _for debugging_
- [x] [Azure Functions extension](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-azurefunctions)

## How to use

### Configuration

In development environment, you need to add a ```local.settings.json``` file using the following boilerplate. The keys of environmental variables will be used to each function in order to access storage services.

```
{
  "IsEncrypted": false,
  "Values": {
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "FUNCTIONS_EXTENSION_VERSION": "~2",
    "WEBSITE_NODE_DEFAULT_VERSION": "10.14.1",
    "STORAGE_ACCOUNT_NAME": "",
    "STORAGE_ACCOUNT_KEY": "",
    "STORAGE_ACCOUNT_PROCESSING": "",
    "CONTAINER_NAME_RECORDING": "",
    "AI_API_KEY": "",
    "AI_API_REGION" : "",
    "TABLE_NAME_API_FACE": "",
    "TABLE_NAME_API_T2S": "",
    "TABLE_NAME_TRACKING": "",
    "TABLE_NAME_PARAMETERS": "",
    "APPINSIGHTS_INSTRUMENTATIONKEY" = "",

  },
  "Host": {
    "CORS": "*"
  },
  "ConnectionStrings": {}
}
```

Replace the following keys for each value:

- ```STORAGE_ACCOUNT_NAME```: Azure Blob account name
- ```STORAGE_ACCOUNT_KEY```: Azure Blob account key from previous account name
- ```CONTAINER_NAME_RECORDING```: container name from previous account name responsible to receive audio and image files from IoT Device (Raspberry Pi)
- ```AI_API_KEY```: API key of AI Cognitive Services to Text service and Face Emotion.
- ```AI_API_REGION```: API region, e.g. _brazilsouth_.
- ```TABLE_NAME_API_FACE```: Azure Table name for API face emotion logs.
- ```TABLE_NAME_API_T2S```: Azure Table name for speech to text logs.
- ```TABLE_NAME_TRACKING```: Azure Table name for summaring all information.
- ```TABLE_NAME_PARAMETERS```: Azure Table name for parametrization, specially to add stopwords.
- ```APPINSIGHTS_INSTRUMENTATIONKEY``` _optional_: API key of Application Insights service (helps a lot for debugging 😝)

You have to create the tables, they will be filled automatically, except the _parameters table_. For that one, create the following entry:

```
PartitionKey: "stopwords",
RowKey: "general",
Value: {"stopwords": ["cara", "muita", "daqui", "sai", "ali", "para", "enfim", "pode", "algo", "nessa", "é"]}
```

### Functions

Each function has different ways to access, some are triggerd by queue item other simple by get requests.

* *getWordCloud*: get the most spoken words of the meeting by giving a meeting code. 

Request example using Postman

```
https://localhost:port/api/getWordCloud?code=6IVACO
```

Request example using cURL (_simplest_)

```
curl --request GET \
  --url 'localhost:port/api/getWordCloud?code=6IVACO' \
  --header 'Accept: */*' \
  --header 'Cache-Control: no-cache' \
  --header 'Connection: keep-alive' \
  --header 'Content-Type: application/json' \
  --header 'Host: meeting-reaction.azurewebsites.net' \
  --header 'Postman-Token: b9f3ee0a-c0e2-42fd-b409-69bd92b9d41c,a04fd484-2917-4e00-9fd9-62a2e23e06c2' \
  --header 'User-Agent: PostmanRuntime/7.15.0' \
  --header 'accept-encoding: gzip, deflate' \
  --header 'cache-control: no-cache'
```

Request output (truncated)

```json
{"message": "Code found at the database", "status": true, "words": 
[{"name": "periferia", "weight": 2}, 
{"name": "gente", "weight": 57}, 
{"name": "assim", "weight": 26}, 
{"name": "regi\u00e3o", "weight": 3}, 
{"name": "bras\u00edlia", "weight": 7}, 
{"name": "ent\u00e3o", "weight": 18}, 
{"name": "computa\u00e7\u00e3o", "weight": 2}, 
{"name": "comecei", "weight": 11}, 
{"name": "pessoal", "weight": 15}, 
{"name": "ligando", "weight": 2}, 
{"name": "maria", "weight": 10}, 
{"name": "jesus", "weight": 3}, 
{"name": "ajudar", "weight": 2}, 
{"name": "tal", "weight": 9}, 
{"name": "vou", "weight": 22}, 
{"name": "conhecer", "weight": 4}, 
{"name": "realidade", "weight": 6}, 
{"name": "forma", "weight": 6}, 
{"name": "sim", "weight": 3}, 
{"name": "hoje", "weight": 7}, 
{"name": "tava", "weight": 11}, 
{"name": "nenhuma", "weight": 3}, 
{"name": "fam\u00edlia", "weight": 3}, 
{"name": "fez", "weight": 3}, 
{"name": "sa\u00edda", "weight": 2}, 
{"name": "neg\u00f3cio", "weight": 9}, 
{"name": "sabe", "weight": 11}, 
{"name": "fica", "weight": 9}]}
```

* *getFacialAnalysis*: get the emotions of the meeting accross the time. 

Request example using Postman

```
https://localhost:port/api/getFacialAnalysis?code=6IVACO
```

Request example using cURL (_simplest_)

```
curl --request GET \
  --url 'https://localhost:port/api/getFacialAnalysis?code=6IVACO' \
  --header 'Accept: */*' \
  --header 'Cache-Control: no-cache' \
  --header 'Connection: keep-alive' \
  --header 'Content-Type: application/json' \
  --header 'Host: meeting-reaction.azurewebsites.net' \
  --header 'Postman-Token: b9f3ee0a-c0e2-42fd-b409-69bd92b9d41c,a04fd484-2917-4e00-9fd9-62a2e23e06c2' \
  --header 'User-Agent: PostmanRuntime/7.15.0' \
  --header 'accept-encoding: gzip, deflate' \
  --header 'cache-control: no-cache'
```

Request output (truncated)

```json
{"message": "Code found at the database", "status": true, 
"facialTimeAnalysis": [
    {"timestamp": 1560850260, "value": 0, "persons": 1, "emotion": 
    {"positive": 0.0, "neutral": 1.0, "negative": 0.0}}, 
    {"timestamp": 1560850320, "value": 0, "persons": 1, 
    "emotion": {"positive": 0.0, "neutral": 1.0, "negative": 0.0}}, 
    {"timestamp": 1560850380, "value": 0, "persons": 1, 
    "emotion": {"positive": 0.0, "neutral": 1.0, "negative": 0.0}}, 
    {"timestamp": 1560850380, "value": 0, "persons": 1, 
    "emotion": {"positive": 0.0, "neutral": 1.0, "negative": 0.0}}, 
    {"timestamp": 1560850740, "value": 1.0, "persons": 1, 
    "emotion": {"positive": 1.0, "neutral": 0.0, "negative": 0.0}}, 
    {"timestamp": 1560852180, "value": 0, "persons": 1, 
    "emotion": {"positive": 0.0, "neutral": 1.0, "negative": 0.0}}, 
    {"timestamp": 1560852480, "value": 0, "persons": 1, 
    "emotion": {"positive": 0.0, "neutral": 1.0, "negative": 0.0}}, 
    {"timestamp": 1560852540, "value": 0, "persons": 1, 
    "emotion": {"positive": 0.0, "neutral": 1.0, "negative": 0.0}}, 
    {"timestamp": 1560852780, "value": 0, "persons": 1, 
    "emotion": {"positive": 0.0, "neutral": 1.0, "negative": 0.0}}, 
    {"timestamp": 1560852840, "value": 0, "persons": 1, 
    "emotion": {"positive": 0.0, "neutral": 1.0, "negative": 0.0}}, 
    {"timestamp": 1560852840, "value": 0, "persons": 2, 
    "emotion": {"positive": 0.443, "neutral": 0.557, "negative": 0.0}}, 
    {"timestamp": 1560852900, "value": 0, "persons": 1, 
    "emotion": {"positive": 0.0, "neutral": 1.0, "negative": 0.0}}, 
    {"timestamp": 1560852960, "value": 0, "persons": 1, 
    "emotion": {"positive": 0.0, "neutral": 1.0, "negative": 0.0}}, 
    {"timestamp": 1560853020, "value": 0, "persons": 1, 
    "emotion": {"positive": 0.0, "neutral": 1.0, "negative": 0.0}}, 
    {"timestamp": 1560853020, "value": 0, "persons": 1, 
    "emotion": {"positive": 0.0, "neutral": 1.0, "negative": 0.0}}, 
    {"timestamp": 1560853080, "value": 1.0, "persons": 1, 
    "emotion": {"positive": 1.0, "neutral": 0.0, "negative": 0.0}}]}
```

* *queueImaging*: is triggered by ```images``` queue. Each entry of the queue has the file details in order to download and process to face analysis API.

* *queueRecording*: is triggered by ```voices``` queue. Each entry of the queue has the file details in order to download and process to speech to text API.

### Core SDK

For manual tasks, such initialization, testing an deployemtn, the [Core Tools SDK](https://docs.microsoft.com/pt-br/azure/azure-functions/functions-run-local).

### Testing

Locally is only possible (in my MacOS environment) test the functions with http endpoints. In Windows environments is possible to simulate the queue service.

To start the local tests (not unit tests or related, just doing some API calls), you can start the debugging in VSCode or execute manually in the command line.

Manually:
```
func host start
```

### Deployment

The Azure Functions plugin is able to do all process to deploy just using the user interface.

Manually:
```
func deploy
```
