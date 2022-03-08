import logging
import azure.functions as func
import os

import googleapiclient.discovery
import json
import re
from google.oauth2 import service_account

VIEW_ID = "234917719"
MAX_PAGES = 10
SCOPES = ["https://www.googleapis.com/auth/analytics.readonly"]
SCRIPT_DIR = os.path.dirname(__file__)
SERVICE_ACCOUNT_FILE = "service_account.json"
BLOG_REGEX = re.compile(r"^\/blog\/[\w\-]*\/$")
JSON_FILE = os.path.join(SCRIPT_DIR, SERVICE_ACCOUNT_FILE)

credentials = service_account.Credentials.from_service_account_file(
    JSON_FILE, scopes=SCOPES
)

analytics = googleapiclient.discovery.build(
    serviceName="analyticsreporting", version="v4", credentials=credentials,
)

def get_report():
    body = {
        "reportRequests": [
            {
                "viewId": VIEW_ID,
                "dateRanges": [{"startDate": "28daysAgo", "endDate": "today"}],
                "metrics": [{"expression": "ga:users"}],
                "dimensions": [{"name": "ga:pagePath"}],
                "orderBys": [{"fieldName": "ga:users", "sortOrder": "DESCENDING"}],
            }
        ]
    }
    return analytics.reports().batchGet(body=body).execute()


def get_popular_pages(response):
    popular_pages = []
    reports = response.get("reports", [])
    if reports:
        report = reports[0]
        for row in report.get("data", {}).get("rows", []):
            popular_pages.append(row["dimensions"][0])
    filtered = [page for page in popular_pages if BLOG_REGEX.match(page)]
    if len(filtered) > MAX_PAGES:
        filtered = filtered[:MAX_PAGES]
    return filtered

def main(req: func.HttpRequest) -> func.HttpResponse:
    
    logging.info('Python HTTP trigger function processed a request.')

    response = get_report()
    pages = get_popular_pages(response)
    
    return func.HttpResponse(json.dumps(pages), mimetype="application/json")


if __name__ == "__main__":
    main()

    
