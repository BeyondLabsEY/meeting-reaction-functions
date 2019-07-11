import logging
import azure.functions as func
from azure.storage.blob.blockblobservice import BlockBlobService
from azure.storage.table import TableService, Entity
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import os
import json
import requests
import base64
import traceback

nltk.data.path.append(os.path.dirname(os.path.abspath(__file__)))

ACCOUNT_NAME = os.environ["STORAGE_ACCOUNT_NAME"]
ACCOUNT_KEY = os.environ["STORAGE_ACCOUNT_KEY"]
SPEECH2TEXT_API_KEY = os.environ["SPEECH2TEXT_API_KEY"]

CONTAINER_NAME = "meeting-word-cloud"


def processar_palavra_chave(lista_frase):
    stopwords = nltk.corpus.stopwords.words("portuguese")
    lista_palavras = []

    for frase in lista_frase:
        palavras = word_tokenize(frase)
        for palavra in palavras:
            if palavra.isalpha() and len(palavra) > 1:
                lista_palavras.append(palavra.lower())

    lista_palavras = [
        palavra for palavra in lista_palavras if palavra not in stopwords]
    fdist = nltk.FreqDist(lista_palavras)
    json_data = json.dumps(fdist)

    print(json_data)

    return json_data


def main(msg: func.QueueMessage) -> None:

    logging.info("Processing audio analysis queue...")

    stopwords = nltk.corpus.stopwords.words("portuguese")

    input_message = msg.get_body().decode('utf-8')
    input_message = json.loads(input_message)

    logging.info("Processing file " + input_message["blob"] + "...")

    table_service = TableService(
        account_name=ACCOUNT_NAME, account_key=ACCOUNT_KEY)
    records = table_service.query_entities("reactionTextToSpeechAPI", filter="PartitionKey eq 'recording' and RowKey eq '" +
                                           input_message["meeting-code"] + "' and RecognitionStatus eq 'Success'")

    if len(records.items) == 0:
        blob_service = BlockBlobService(
            account_name=ACCOUNT_NAME, account_key=ACCOUNT_KEY)
        blob_entry = blob_service.get_blob_to_bytes(
            CONTAINER_NAME, input_message["blob"], timeout=60)
        audio_bytes = blob_entry.content

        url_token_api = "https://westus.api.cognitive.microsoft.com/sts/v1.0/issueToken"
        api_key = SPEECH2TEXT_API_KEY

        headers = {"Content-Length": "0", "Ocp-Apim-Subscription-Key": api_key}

        api_response = requests.post(url_token_api, headers=headers)
        access_token = str(api_response.content.decode('utf-8'))

        url_stt_api = "https://westus.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1?language=pt-BR"

        headers = {"Authorization": "Bearer {0}".format(access_token),
                   "Content-Length": str(len(audio_bytes)),
                   "Content-type": "audio/wav",
                   "codec": "audio/pcm",
                   "samplerate": "16000"}

        record = {}
        api_response = None
        res_json = None

        try:
            api_response = requests.post(
                url_stt_api, headers=headers, params=None, data=audio_bytes)
            res_json = json.loads(api_response.content.decode('utf-8'))
            record["RecognitionStatus"] = res_json["RecognitionStatus"]
            record["TextConverted"] = res_json["DisplayText"]
            record["ApiResponse"] = json.dumps(res_json)

            logging.info("Speech to text processed.")

        except Exception as error:
            record["RecognitionStatus"] = "Request Fail"
            record["Exception"] = traceback.format_exc()

            logging.error(error)

        finally:
            record["PartitionKey"] = input_message["meeting-code"]
            record["RowKey"] = input_message["file-name"]
            table_service.insert_or_replace_entity(
                "reactionTextToSpeechAPI", record)

            logging.info("Result persisted.")

        logging.info("Result:" + str(res_json))

        if res_json is not None and "Message" in res_json:
            raise Exception(res_json["Message"])

        if res_json is not None and res_json["RecognitionStatus"] == "Success":
            logging.info("Decoded speech: "+str(res_json["DisplayText"]))

            records = table_service.query_entities(
                "reactionTracking", filter="PartitionKey eq 'tracking-analysis' and RowKey eq '"+input_message["meeting-code"]+"'")
            texts_converted = []

            if len(records.items) > 0:
                record = records.items[0]
                if "TextConverted" in records.items[0]:
                    texts_converted = json.loads(record["TextConverted"])
                    text_converted = {
                        "file-name": input_message["file-name"], "text": res_json["DisplayText"]}

                    if text_converted not in texts_converted:
                        texts_converted.append(text_converted)

                    record["TextConverted"] = json.dumps(texts_converted)
                else:
                    text_converted = {
                        "file-name": input_message["file-name"], "text": res_json["DisplayText"]}
                    texts_converted.append(text_converted)

                    record["TextConverted"] = json.dumps(texts_converted)
            else:
                text_converted = {
                    "file-name": input_message["file-name"], "text": res_json["DisplayText"]}
                texts_converted.append(text_converted)
                record = {"PartitionKey": "tracking-analysis",
                          "RowKey": input_message["meeting-code"], "TextConverted": json.dumps(texts_converted)}

            text_list = []

            for text_converted in texts_converted:
                text_list.append(text_converted["text"])

            logging.info("Text List: " + str(text_list))

            text_list = set(text_list)
            freq_dist = processar_palavra_chave(text_list)

            record["FreqDist"] = freq_dist

            table_service.insert_or_replace_entity("reactionTracking", record)

            logging.info("Message processed successfully:" +
                         str(res_json["DisplayText"]))

        else:
            print("Descartado por falha no reconhecimento de voz.")
            logging.info(
                "Item discarded. Bad quality or audio file corrupted.")
    else:
        logging.info("Item already processed.")
