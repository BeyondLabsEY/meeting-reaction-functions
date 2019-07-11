import json
import logging
import os
import azure.functions as func
from datetime import datetime, timedelta
import requests
from azure.storage.table import TableService, Entity
from azure.storage.blob import BlockBlobService, BlobPermissions, PublicAccess

ACCOUNT_NAME = os.environ["STORAGE_ACCOUNT_NAME"]
ACCOUNT_KEY = os.environ["STORAGE_ACCOUNT_KEY"]
SUBSCRIPTION_KEY = os.environ["FACE_ANALYSIS_SUBSCRIPTION_KEY"]
CONTAINER_NAME = "meeting-word-cloud"
POSITIVE_EMOTIONS = ["happiness", "surprise"]
NEGATIVE_EMOTIONS = ["anger", "fear", "sadness", "contempt", "disgust"]


def main(msg: func.QueueMessage) -> None:
    logging.info("Processing image analysis queue...")

    input_message = msg.get_body().decode('utf-8')
    input_message = json.loads(input_message)

    block_blob_service = BlockBlobService(
        account_name=ACCOUNT_NAME, account_key=ACCOUNT_KEY)

    blob = input_message["blob"]
    meetingCode = input_message["meeting-code"]
    fileName = input_message["file-name"]
    dateTime = input_message["date-time"]

    #{"blob" : "AT81CB/image_files/AT81CB_9G9C.jpg", "meeting-code" : "AT81CB","file-name":  "AT81CB_9G9C.jpg","date-time": "13/06/2019 10:00"}

    table_service = TableService(
        account_name=ACCOUNT_NAME, account_key=ACCOUNT_KEY)

    records = table_service.query_entities("reactionFaceDetectionAPI", filter="PartitionKey eq '" + meetingCode + "' and RowKey eq '" +
                                           fileName + "' and ApiStatus eq 200")

    if len(records.items) == 0:

        logging.info("File not processed yet. Starting processing...")

        sas_minutes = 10

        sas_url = block_blob_service.generate_blob_shared_access_signature(
            CONTAINER_NAME,
            blob,
            BlobPermissions.READ,
            datetime.utcnow() + timedelta(minutes=sas_minutes),
        )

        logging.info(
            "Publicity of file using shared signature created for "+str(sas_minutes))

        image_url = "https://meetingwordcloud.blob.core.windows.net/" + \
            CONTAINER_NAME + "/" + blob + "?" + sas_url

        logging.info("Public url generated: " + image_url)

        face_api_url = 'https://brazilsouth.api.cognitive.microsoft.com/face/v1.0/detect'

        # perception = {"time": "08:00", "emotion":
        # {"anger": 0.0, "contempt": 0.001, "disgust": 0.0, "fear": 0.0,
        #    "happiness": 0.97, "neutral": 0.029, "sadness": 0.0, "surprise": 0.0}

        headers = {'Ocp-Apim-Subscription-Key': SUBSCRIPTION_KEY}

        params = {
            'returnFaceId': 'false',
            'returnFaceLandmarks': 'false',
            'returnFaceAttributes': 'emotion',
        }

        logging.info("Starting facial API analysis...")
        logging.info("Processing file " + fileName + "...")

        response = requests.post(face_api_url, params=params,
                                 headers=headers, json={"url": image_url})

        logging.info("Face analysis successfully processed.")

        api_response = {"statusCode": response.status_code,
                        "reason": response.reason}

        api_record = {"PartitionKey": meetingCode,
                      "RowKey": fileName,
                      "ApiStatus": response.status_code,
                      "ApiResponse": json.dumps(api_response),
                      "TextResponse": json.dumps(response.json())}

        table_service.insert_or_replace_entity(
            "reactionFaceDetectionAPI", api_record)

        logging.info("Response: " + str(api_response))
        logging.info("Response result: " + str(response.json()))

        faces = response.json()
        qtde_person = len(faces)

        logging.info("Records found " + str(qtde_person))

        if response.status_code == 200 and qtde_person > 0:

            positive = 0
            negative = 0
            neutral = 0
            file_processed = []

            for face in faces:
                file_processed.append(
                    {"file-name": fileName, "emotion-analysis": face["faceAttributes"]["emotion"]})

                max_key = sorted(face["faceAttributes"]["emotion"], key=(
                    lambda key: face["faceAttributes"]["emotion"][key]), reverse=True)

                logging.info("Max key " + str(max_key[0]))

                if max_key[0] in POSITIVE_EMOTIONS:
                    positive = positive + \
                        face["faceAttributes"]["emotion"][max_key[0]]
                elif max_key[0] in NEGATIVE_EMOTIONS:
                    negative = negative + \
                        face["faceAttributes"]["emotion"][max_key[0]]
                else:
                    neutral = neutral + \
                        face["faceAttributes"]["emotion"][max_key[0]]

            logging.info("Positives points " + str(positive))
            logging.info("Negatives points " + str(negative))
            logging.info("Neutral points " + str(neutral))

            total = positive + negative + neutral

            if total > 0:
                positive_norm = round(positive/total, 3)
                negative_norm = round(negative/total, 3)
                neutral_norm = round(neutral/total, 3)
            else:
                positive_norm = 0
                negative_norm = 0
                neutral_norm = 1

            logging.info("Positives points normed " + str(positive_norm))
            logging.info("Negatives points normed " + str(negative_norm))
            logging.info("Neutral points normed " + str(neutral_norm))

            values = {"positive": positive_norm,
                      "neutral": neutral_norm, "negative": negative_norm}

            logging.info("Value points: " + str(values))

            values_max_key = sorted(values, key=(
                lambda key: values[key]), reverse=True)

            logging.info("Value max key: " + values_max_key[0])

            if values_max_key[0] == "negative":
                value = - values[values_max_key[0]]
            elif values_max_key[0] == "neutral":
                value = 0
            else:
                value = values[values_max_key[0]]

            logging.info("Value: " + str(value))

            final_report = {"time": dateTime, "value": value, "file-name": fileName,
                            "persons": qtde_person, "emotion": values}

            records = table_service.query_entities(
                "reactionTracking", filter="PartitionKey eq 'tracking-analysis' and RowKey eq '"+meetingCode+"'")
            texts_converted = []

            if len(records.items) > 0:
                record = records.items[0]
                if "EmotionTimeAnalysis" in records.items[0]:
                    data_points = json.loads(record["EmotionTimeAnalysis"])
                    data_points.append(final_report)

                    file_processeds = json.loads(record["FacialAnalysis"])
                    file_processeds.append(file_processed)
                else:
                    data_points = [final_report]
                    file_processeds = [file_processed]

                    record["FacialAnalysis"] = json.dumps(file_processeds)
                    record["EmotionTimeAnalysis"] = json.dumps(data_points)
            else:
                record = {"PartitionKey": "tracking-analysis",
                          "RowKey": meetingCode}
                data_points = [final_report]
                file_processeds = [file_processed]

            logging.info("Data points: " + str(data_points))

            record["FacialAnalysis"] = json.dumps(file_processeds)
            record["EmotionTimeAnalysis"] = json.dumps(data_points)

            table_service.insert_or_replace_entity("reactionTracking", record)
    else:
        logging.info("Item already processed.")
