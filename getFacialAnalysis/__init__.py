import logging
import azure.functions as func
import json
from azure.storage.table import TableService, Entity
import os
import time
import datetime

# Configurar, no painel das Functions, General Settings > Configurations > Application Settings
# Inclua as variáveis de ambiente baixo para a conta do Storage

ACCOUNT_NAME = os.environ["STORAGE_ACCOUNT_NAME"]
ACCOUNT_KEY = os.environ["STORAGE_ACCOUNT_KEY"]

# Headers para lidar com CORS pois as configurações do Azure não tem efeito no engine Python, pelo menos por enquanto :(
headers = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET,OPTIONS"
}


def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        logging.info("Trigger started")

        ret = {}

        if "code" not in req.params:
            logging.info("Invalid code")

            ret["message"] = "The parameter code is no present in the request."
            ret["status"] = False

            return func.HttpResponse(json.dumps(ret), headers=headers)
        else:
            code = req.params.get('code')

            logging.info("Processing "+str(code) + "...")

            table_service = TableService(
                account_name=ACCOUNT_NAME, account_key=ACCOUNT_KEY)
            records = table_service.query_entities(
                'reactionTracking', filter="PartitionKey eq 'tracking-analysis' and RowKey eq '"+code+"'")

            if len(records.items) == 0:
                ret["message"] = "Meeting coding not found"
                ret["status"] = False

                logging.info("Code not found.")

                return func.HttpResponse(json.dumps(ret), headers=headers)
            else:
                record = records.items[0]
                facial_time_analysis = json.loads(
                    record["EmotionTimeAnalysis"])

                time_analysis = []

                for item in facial_time_analysis:
                    entry = {}
                    timestamp = time.mktime(datetime.datetime.strptime(
                        item["time"], "%d/%m/%Y %H:%M").timetuple())
                    timestamp = round(timestamp)
                    entry["timestamp"] = timestamp
                    entry["value"] = item["value"]
                    entry["persons"] = item["persons"]
                    entry["emotion"] = item["emotion"]

                    time_analysis.append(entry)

                ret["message"] = "Code found at the database"
                ret["status"] = True
                ret["facialTimeAnalysis"] = time_analysis

                logging.info("Code successfully processed.")

                return func.HttpResponse(json.dumps(ret), headers=headers)

    except Exception as error:
        logging.error(error)
        return func.HttpResponse(error, status_code=400, headers=headers)
