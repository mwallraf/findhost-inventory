import json

class SQLParameters:

    def __init__(self, *args, **kwargs):
        self.global_account = kwargs.get("global_account", None)
        self.frontix_server = kwargs.get("frontix_server", None)
        self.frontix_port = kwargs.get("frontix_port", None)
        self.frontix_service = kwargs.get("frontix_service", None)
        self.frontix_query = kwargs.get("frontix_query", None)
        self.frontix_query_description = kwargs.get("frontix_query_description", None)
        self.post_processor_script = kwargs.get("post_processor_script", None)
        self.query_limit = kwargs.get("query_limit", 0)
        self.is_demo = kwargs.get("is_demo", False)

    def tojson(self):
        j = {
                "global_account": self.global_account,
                "frontix_server": self.frontix_server,
                "frontix_port": self.frontix_port,
                "frontix_service": self.frontix_service,
                "frontix_query": self.frontix_query,
                "frontix_query_description": self.frontix_query_description,
                "post_processor_script": self.post_processor_script,
                "query_limit": self.query_limit
            }
        return json.dumps(j, indent=4)

