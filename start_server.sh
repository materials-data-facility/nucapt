#!/bin/bash
docker run -d -it -p 6543:443 \
  --mount "type=bind,source=$PWD/conf,destination=/conf" \
  --mount "type=bind,source=/volume1/nucapt-data/working-data,destination=/working-data" \
  --mount "type=bind,source=$PWD/certs,destination=/etc/nginx/ssl" \
  --name nucaptdms \
	materialsdatafacility/nucaptdms:develop