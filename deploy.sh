#!/usr/bin/env bash

# Add simple DB for converting zip codes to time zones
# SQLite3 which typically comes with Python 3 is not loaded on Lambda
pip install pytz -t ./dist
ask-amy-cli deploy_lambda --deploy-json-file cli_config.json
