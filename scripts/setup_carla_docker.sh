#!/bin/bash
set -e

CARLA_VERSION="${1:-0.9.14}"

echo "Pulling CARLA ${CARLA_VERSION} docker image..."
docker pull carlasim/carla:${CARLA_VERSION}

echo "Starting CARLA server..."
docker run --privileged --gpus all --net=host \
    -e DISPLAY=$DISPLAY \
    carlasim/carla:${CARLA_VERSION} \
    /bin/bash ./CarlaUE4.sh -RenderOffScreen
