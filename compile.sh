#!/bin/bash
cd server/src
g++ -Wall -Wextra -o server server.cpp modules/Group.cpp modules/Game.cpp