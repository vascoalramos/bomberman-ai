#!/bin/bash

gnome-terminal --title="Server" -e "python3 server.py"

sleep 1

gnome-terminal --title="Viewer" -e "python3 viewer.py"

sleep 1

gnome-terminal --title="Student" -e "python3 student.py"