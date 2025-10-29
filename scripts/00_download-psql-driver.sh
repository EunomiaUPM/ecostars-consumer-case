#!/bin/bash

VERSION=42.7.8
URL=https://jdbc.postgresql.org/download/postgresql-$VERSION.jar

curl -L -o ./lib/postgresql-$VERSION.jar $URL