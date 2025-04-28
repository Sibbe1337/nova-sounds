# Placeholder for Pitch Score API Cloud Function

import functions_framework


@functions_framework.http
def pitch_score_handler(request):
    """HTTP Cloud Function.
    Args:
        request (flask.Request): The request object.
        <https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data>
    Returns:
        The response text, or any set of values compatible with
        `make_response`
        <https://flask.palletsprojects.com/en/1.1.x/api/#flask.make_response>.
    """
    request_json = request.get_json(silent=True)
    request_args = request.args

    if request_json and "isrc" in request_json:
        isrc = request_json["isrc"]
    elif request_args and "isrc" in request_args:
        isrc = request_args["isrc"]
    else:
        return 'Missing "isrc" in request body or query parameters.', 400

    # TODO: Implement logic to fetch features from BQ
    # TODO: Load or call BQ ML model to predict score
    # TODO: Return score

    mock_score = 0.88  # Placeholder
    return {"isrc": isrc, "score": mock_score}
