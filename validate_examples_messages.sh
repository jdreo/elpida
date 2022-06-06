#!/bin/sh

if [ ! -f message_validator.sif ] ; then
    apptainer build message_validator.sif message_validator.apptainer.def
fi

for m in ./examples/messages/query*.json ; do
    echo $m
    apptainer run message_validator.sif elpida-query.schema.yaml $m
done

for m in ./examples/messages/reply*.json ; do
    echo $m
    apptainer run message_validator.sif elpida-reply.schema.yaml $m
done
