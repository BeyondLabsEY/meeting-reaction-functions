import logging
import azure.functions as func
import json
from azure.storage.table import TableService, Entity
import os

# Configurar, no painel das Functions, General Settings > Configurations > Application Settings
# Inclua as variáveis de ambiente baixo para a conta do Storage

ACCOUNT_NAME = os.environ["STORAGE_ACCOUNT_NAME"]
ACCOUNT_KEY = os.environ["STORAGE_ACCOUNT_KEY"]
TABLE_NAME_TRACKING = os.environ["TABLE_NAME_TRACKING"]

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
                TABLE_NAME_TRACKING, filter="PartitionKey eq 'tracking-analysis' and RowKey eq '"+code+"'")

            if len(records.items) == 0:
                ret["message"] = "Meeting coding not found"
                ret["status"] = False
                logging.info("Code not found.")
            else:
                ret["message"] = "Code has been found"
                ret["status"] = True
                logging.info("Code has been found.")

            return func.HttpResponse(json.dumps(ret), headers=headers)

    except Exception as error:
        logging.error(error)
        return func.HttpResponse(
            error, status_code=400, headers=headers
        )
