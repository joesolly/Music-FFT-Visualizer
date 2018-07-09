#!/bin/bash

if [ -f .env ]; then
  source .env
fi

while true
do
  python3 main.py
  ret=$?
  if [ $ret -eq 0 ]; then
    break  # stop if ending intentionally
  fi
  sleep 1  # sleep after failure before going again
done
