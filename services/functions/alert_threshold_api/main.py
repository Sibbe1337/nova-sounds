# Placeholder for Alert Threshold API Cloud Function

import functions_framework


@functions_framework.http
def alert_threshold_handler(request):
    request_json = request.get_json(silent=True)

    if not request_json or "metric" not in request_json or "value" not in request_json:
        return 'Missing "metric" or "value" in request body.', 400

    metric = request_json["metric"]
    value = request_json["value"]

    # TODO: Implement logic to store/update alert rule
    # (e.g., in Firestore, Cloud SQL, or maybe trigger external service)

    return {"status": "success", "rule_created_for": metric, "threshold": value}
