#!/bin/sh
logreopen=${VARPATH}/nucleus.logreopen
if [ ! -e "$logreopen" ]; then
  touch $logreopen
fi

/siq/env/python/bin/python /siq/env/python/bin/bake -m spire.tasks \
  spire.schema.deploy schema=nucleus config=/siq/svc/nucleus/nucleus.yaml
ln -sf ${SVCPATH}/nucleus/nucleus.yaml ${CONFPATH}/uwsgi/nucleus.yaml
