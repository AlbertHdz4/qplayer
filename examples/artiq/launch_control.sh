#!/bin/bash
gnome-terminal --tab -- bash -c "source /home/ocr/miniconda3/etc/profile.d/conda.sh; conda activate artiq6; cd ~/repos/ocr/control_system; artiq_master"
gnome-terminal --tab -- bash -c "source /home/ocr/miniconda3/etc/profile.d/conda.sh; conda activate artiq6; artiq_dashboard"
gnome-terminal --tab -- bash -c "source /home/ocr/miniconda3/etc/profile.d/conda.sh; conda activate artiq6; cd ~/repos/qplayer/notify; python server.py --address 192.168.52.2"
gnome-terminal --tab -- bash -c "source /home/ocr/miniconda3/etc/profile.d/conda.sh; conda activate artiq6; cd ~/repos/qplayer; python main.py ~/repos/ocr/control_system/config_artiq.json"
