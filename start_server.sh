#!/bin/bash
docker run --rm -it -p 443:443 -p 80:80  \
  --mount "type=bind,source=$PWD/conf,destination=/conf" \
  --mount "type=bind,source=$PWD/working-data,destination=/working-data" \
  --mount "type=bind,source=$PWD/nucapt_certs,destination=/etc/nginx/ssl" \
  materialsdatafacility/nucaptdms:develop
