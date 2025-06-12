#!/usr/bin/env python3
"""
REST API Server

FastAPI server for Mock SNMP Agent control and monitoring.
"""

import asyncio
import logging
import threading
import time
from typing import Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .controllers import MockSNMPAgentController
from .export_import import setup_export_import_endpoints
from .models import (
    AgentStatusResponse,
    ConfigurationResponse,
    ConfigurationUpdate,
    ErrorResponse,
    HealthResponse,
    MetricsResponse,
    OIDListResponse,
    RestartRequest,
    RestartResponse,
)
from .query_endpoints import setup_query_endpoints
from .simulation_control import setup_simulation_endpoints
from .websocket import MetricsCollector
from .websocket import manager as ws_manager
from .websocket import setup_websocket_routes


class SNMPAgentAPIServer:
    """REST API server for Mock SNMP Agent."""

    def __init__(
        self,
        agent_process=None,
        config=None,
        data_dir=None,
        snmp_endpoint=None,
        api_host="127.0.0.1",
        api_port=8080,
        cors_enabled=True,
        cors_origins=None,
    ):
        """Initialize the API server.

        Args:
            agent_process: Reference to the SNMP agent process
            config: Current configuration object
            data_dir: Data directory path
            snmp_endpoint: SNMP endpoint (host:port)
            api_host: API server host
            api_port: API server port
            cors_enabled: Enable CORS middleware
            cors_origins: Allowed CORS origins
        """
        self.agent_process = agent_process
        self.config = config
        self.data_dir = data_dir
        self.snmp_endpoint = snmp_endpoint
        self.api_host = api_host
        self.api_port = api_port

        # Initialize controller
        self.controller = MockSNMPAgentController(
            agent_process=agent_process,
            config=config,
            data_dir=data_dir,
            snmp_endpoint=snmp_endpoint,
        )

        # Create FastAPI app
        self.app = FastAPI(
            title="Mock SNMP Agent API",
            description="REST API for controlling and monitoring Mock SNMP Agent",
            version="1.0.0",
            docs_url="/docs",
            redoc_url="/redoc",
            openapi_url="/openapi.json",
        )

        # Configure CORS
        if cors_enabled:
            origins = cors_origins or ["*"]
            self.app.add_middleware(
                CORSMiddleware,
                allow_origins=origins,
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )

        # Configure logging
        self.logger = logging.getLogger(__name__)

        # Server state
        self.server_thread = None
        self.is_running = False
        self.metrics_collector = None

        # Setup routes
        self._setup_routes()

        # Setup additional endpoints
        self._setup_extended_endpoints()

    def _setup_routes(self):
        """Setup API routes."""

        @self.app.get("/health", response_model=HealthResponse, tags=["Health"])
        async def get_health():
            """Get agent health status."""
            try:
                return self.controller.get_health()
            except Exception as e:
                self.logger.error("Health check failed: %s", str(e))
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/metrics", response_model=MetricsResponse, tags=["Monitoring"])
        async def get_metrics():
            """Get agent performance metrics."""
            try:
                return self.controller.get_metrics()
            except Exception as e:
                self.logger.error("Metrics collection failed: %s", str(e))
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get(
            "/config", response_model=ConfigurationResponse, tags=["Configuration"]
        )
        async def get_configuration():
            """Get current agent configuration."""
            try:
                return self.controller.get_configuration()
            except Exception as e:
                self.logger.error("Configuration retrieval failed: %s", str(e))
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.put(
            "/config", response_model=ConfigurationResponse, tags=["Configuration"]
        )
        async def update_configuration(config_update: ConfigurationUpdate):
            """Update agent configuration."""
            try:
                return self.controller.update_configuration(
                    config_update.dict(exclude_unset=True)
                )
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                self.logger.error("Configuration update failed: %s", str(e))
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get(
            "/agent/status", response_model=AgentStatusResponse, tags=["Agent"]
        )
        async def get_agent_status():
            """Get detailed agent status."""
            try:
                return self.controller.get_agent_status()
            except Exception as e:
                self.logger.error("Status retrieval failed: %s", str(e))
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/agent/restart", response_model=RestartResponse, tags=["Agent"])
        async def restart_agent(restart_request: RestartRequest):
            """Restart the SNMP agent."""
            try:
                return self.controller.restart_agent(
                    force=restart_request.force,
                    timeout_seconds=restart_request.timeout_seconds,
                )
            except Exception as e:
                self.logger.error("Agent restart failed: %s", str(e))
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/oids/available", response_model=OIDListResponse, tags=["OIDs"])
        async def get_available_oids():
            """Get list of available OIDs for retrieval."""
            try:
                return self.controller.get_available_oids()
            except Exception as e:
                self.logger.error("OID list retrieval failed: %s", str(e))
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/", tags=["Info"])
        async def root():
            """API root endpoint."""
            return {
                "name": "Mock SNMP Agent API",
                "version": "1.0.0",
                "description": "REST API for controlling and monitoring Mock SNMP Agent",
                "endpoints": {
                    "health": "/health",
                    "metrics": "/metrics",
                    "configuration": "/config",
                    "agent_status": "/agent/status",
                    "restart": "/agent/restart",
                    "available_oids": "/oids/available",
                    "documentation": "/docs",
                },
            }

        # Exception handlers
        @self.app.exception_handler(HTTPException)
        async def http_exception_handler(request, exc):
            return JSONResponse(
                status_code=exc.status_code,
                content=ErrorResponse(
                    error="HTTPException",
                    message=str(exc.detail),
                    timestamp=time.time(),
                ).dict(),
            )

        @self.app.exception_handler(Exception)
        async def general_exception_handler(request, exc):
            self.logger.error("Unhandled exception: %s", str(exc))
            return JSONResponse(
                status_code=500,
                content=ErrorResponse(
                    error="InternalServerError",
                    message="An unexpected error occurred",
                    timestamp=time.time(),
                ).dict(),
            )

    def _setup_extended_endpoints(self):
        """Setup extended API endpoints."""
        # Setup WebSocket routes
        setup_websocket_routes(self.app)

        # Setup query endpoints
        history_manager = setup_query_endpoints(
            self.app, self.controller, self.data_dir
        )

        # Setup simulation control endpoints
        scenario_manager = setup_simulation_endpoints(self.app, self.controller)

        # Setup export/import endpoints
        setup_export_import_endpoints(
            self.app, self.controller, scenario_manager, history_manager
        )

        # Store managers for later use
        self.app.state.history_manager = history_manager
        self.app.state.scenario_manager = scenario_manager

        # Setup metrics collector for WebSocket broadcasting
        self.metrics_collector = MetricsCollector(self.controller, interval_seconds=5)

    def start(self):
        """Start the API server in a background thread."""
        if self.is_running:
            self.logger.warning("API server is already running")
            return

        def run_server():
            """Run the server."""
            try:
                import uvicorn

                self.logger.info(
                    "Starting API server on %s:%s", self.api_host, self.api_port
                )

                # Create event loop for async operations
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                # Start metrics collector
                if self.metrics_collector:
                    loop.create_task(self.metrics_collector.start())

                uvicorn.run(
                    self.app,
                    host=self.api_host,
                    port=self.api_port,
                    log_level="info",
                    loop="asyncio",
                )
            except Exception as e:
                self.logger.error("API server failed to start: %s", str(e))

        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        self.is_running = True

        self.logger.info(
            f"API server started on http://{self.api_host}:{self.api_port}"
        )
        self.logger.info(
            f"API documentation available at http://{self.api_host}:{self.api_port}/docs"
        )
        self.logger.info(
            f"WebSocket endpoints available at ws://{self.api_host}:{self.api_port}/ws/*"
        )

    def stop(self):
        """Stop the API server."""
        if not self.is_running:
            return

        # Stop metrics collector
        if self.metrics_collector:
            asyncio.create_task(self.metrics_collector.stop())

        self.is_running = False
        self.logger.info("API server stopped")

    def update_agent_reference(self, agent_process):
        """Update the agent process reference.

        Args:
            agent_process: New agent process reference
        """
        self.agent_process = agent_process
        self.controller.agent_process = agent_process

    def update_config_reference(self, config):
        """Update the configuration reference.

        Args:
            config: New configuration object
        """
        self.config = config
        self.controller.config = config


def create_api_server(
    agent_process=None,
    config=None,
    data_dir=None,
    snmp_endpoint=None,
    api_host="127.0.0.1",
    api_port=8080,
    cors_enabled=True,
    cors_origins=None,
) -> SNMPAgentAPIServer:
    """Create and configure an API server instance.

    Args:
        agent_process: Reference to the SNMP agent process
        config: Current configuration object
        data_dir: Data directory path
        snmp_endpoint: SNMP endpoint (host:port)
        api_host: API server host
        api_port: API server port
        cors_enabled: Enable CORS middleware
        cors_origins: Allowed CORS origins

    Returns:
        Configured API server instance
    """
    return SNMPAgentAPIServer(
        agent_process=agent_process,
        config=config,
        data_dir=data_dir,
        snmp_endpoint=snmp_endpoint,
        api_host=api_host,
        api_port=api_port,
        cors_enabled=cors_enabled,
        cors_origins=cors_origins,
    )


# Create a default app instance for uvicorn
_default_server = create_api_server()
app = _default_server.app
