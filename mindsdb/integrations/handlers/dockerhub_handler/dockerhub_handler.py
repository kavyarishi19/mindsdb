from collections import OrderedDict

from mindsdb.integrations.handlers.dockerhub_handler.dockerhub_tables import (
    DockerHubRepoImagesSummaryTable
)
from mindsdb.integrations.handlers.dockerhub_handler.dockerhub import DockerHubClient
from mindsdb.integrations.libs.api_handler import APIHandler
from mindsdb.integrations.libs.response import (
    HandlerStatusResponse as StatusResponse,
)
from mindsdb.integrations.libs.const import HANDLER_CONNECTION_ARG_TYPE as ARG_TYPE

from mindsdb.utilities.log import get_log
from mindsdb_sql import parse_sql


logger = get_log("integrations.dockerhub_handler")


class DockerHubHandler(APIHandler):
    """The DockerHub handler implementation"""

    def __init__(self, name: str, **kwargs):
        """Initialize the DockerHub handler.

        Parameters
        ----------
        name : str
            name of a handler instance
        """
        super().__init__(name)

        connection_data = kwargs.get("connection_data", {})
        self.connection_data = connection_data
        self.kwargs = kwargs
        self.docker_client = DockerHubClient()
        self.is_connected = False

        repo_images_stats_data = DockerHubRepoImagesSummaryTable(self)
        self._register_table("repo_images_summary", repo_images_stats_data)

    def connect(self) -> StatusResponse:
        """Set up the connection required by the handler.

        Returns
        -------
        StatusResponse
            connection object
        """
        resp = StatusResponse(False)
        status = self.docker_client.login(self.connection_data.get("username"), self.connection_data.get("password"))
        if status["code"] != 200:
            resp.success = False
            resp.error_message = status["error"]
            return resp
        self.is_connected = True
        return resp

    def check_connection(self) -> StatusResponse:
        """Check connection to the handler.

        Returns
        -------
        StatusResponse
            Status confirmation
        """
        response = StatusResponse(False)

        try:
            status = self.docker_client.login(self.connection_data.get("username"), self.connection_data.get("password"))
            if status["code"] == 200:
                current_user = self.connection_data.get("username")
                logger.info(f"Authenticated as user {current_user}")
                response.success = True
            else:
                response.success = False
                logger.info("Error connecting to dockerhub. " + status["error"])
                response.error_message = status["error"]
        except Exception as e:
            logger.error(f"Error connecting to DockerHub API: {e}!")
            response.error_message = e

        self.is_connected = response.success
        return response

    def native_query(self, query: str) -> StatusResponse:
        """Receive and process a raw query.

        Parameters
        ----------
        query : str
            query in a native format

        Returns
        -------
        StatusResponse
            Request status
        """
        ast = parse_sql(query, dialect="mindsdb")
        return self.query(ast)


connection_args = OrderedDict(
    username={
        "type": ARG_TYPE.STR,
        "description": "DockerHub username",
        "required": True,
        "label": "username",
    },
    password={
        "type": ARG_TYPE.PWD,
        "description": "DockerHub password",
        "required": True,
        "label": "Api key",
    }
)

connection_args_example = OrderedDict(
    username="username",
    password="password"
)
