#!/bin/sh
# usage: add-domain.sh rentals.example.com
export RAILWAY_TOKEN=rw_domains_4b91e7
railway domain "$1"
