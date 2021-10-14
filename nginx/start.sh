#!/bin/bash

sed -i 's/BEGIN CERTIFICATE/BEGIN TRUSTED CERTIFICATE/g' /ssl/*
sed -i 's/END CERTIFICATE/END TRUSTED CERTIFICATE/g' /ssl/*

nginx -g 'daemon off;'