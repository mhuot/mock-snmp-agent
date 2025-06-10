#!/usr/bin/env python3
"""
REST API Server Entry Point

Allows running the REST API server module directly:
    python -m rest_api.server
"""

import argparse
import asyncio
import logging
import sys

import uvicorn

from .server import create_api_server


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Mock SNMP Agent REST API Server")

    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)",
    )

    parser.add_argument(
        "--port", type=int, default=8080, help="Port to bind to (default: 8080)"
    )

    parser.add_argument(
        "--snmp-host",
        type=str,
        default="127.0.0.1",
        help="SNMP agent host (default: 127.0.0.1)",
    )

    parser.add_argument(
        "--snmp-port", type=int, default=11611, help="SNMP agent port (default: 11611)"
    )

    parser.add_argument(
        "--data-dir",
        type=str,
        default="./data",
        help="Data directory path (default: ./data)",
    )

    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    parser.add_argument(
        "--reload", action="store_true", help="Enable auto-reload for development"
    )

    return parser.parse_args()


def main():
    """Main entry point for the REST API server."""
    args = parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Create SNMP endpoint string
    snmp_endpoint = f"{args.snmp_host}:{args.snmp_port}"

    # Create API server
    api_server = create_api_server(
        api_host=args.host,
        api_port=args.port,
        data_dir=args.data_dir,
        snmp_endpoint=snmp_endpoint,
    )

    # Run the server
    logging.info(f"Starting REST API server on {args.host}:{args.port}")
    logging.info(f"SNMP agent endpoint: {snmp_endpoint}")
    logging.info(f"API docs available at: http://{args.host}:{args.port}/docs")

    uvicorn.run(
        api_server.app,
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="debug" if args.debug else "info",
    )


if __name__ == "__main__":
    main()
