#!/bin/bash
# Run docker tests on your local machine

xhost +

PLUGIN_NAME="geoserverexplorer"
export QGIS_VERSION_TAG="master_2"

docker-compose down -v
docker-compose up -d
sleep 10

DOCKER_RUN_COMMAND="docker-compose exec qgis-testing-environment sh -c"

# Setup
$DOCKER_RUN_COMMAND "qgis_setup.sh $PLUGIN_NAME"
$DOCKER_RUN_COMMAND "pip install paver"
$DOCKER_RUN_COMMAND "cd /tests_directory && paver setup"

# Run the tests
$DOCKER_RUN_COMMAND "DISPLAY=:0 qgis_testrunner.sh geoserverexplorer.test.catalogtests"
$DOCKER_RUN_COMMAND "qgis_testrunner.sh geoserverexplorer.test.deletetests"
$DOCKER_RUN_COMMAND "qgis_testrunner.sh geoserverexplorer.test.guitests"
$DOCKER_RUN_COMMAND "qgis_testrunner.sh geoserverexplorer.test.dragdroptests"
$DOCKER_RUN_COMMAND "qgis_testrunner.sh geoserverexplorer.test.pkicatalogtests"
$DOCKER_RUN_COMMAND "qgis_testrunner.sh geoserverexplorer.test.pkideletetests"
$DOCKER_RUN_COMMAND "qgis_testrunner.sh geoserverexplorer.test.pkiguitests"
$DOCKER_RUN_COMMAND "qgis_testrunner.sh geoserverexplorer.test.pkidragdroptests"
$DOCKER_RUN_COMMAND "qgis_testrunner.sh geoserverexplorer.test.pkiowstests"
