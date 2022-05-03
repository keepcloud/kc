#!/usr/bin/env bash
# -------------------------------------------------------------------------
# Keepcloud support script
# -------------------------------------------------------------------------
# Website:       https://wordops.net
# GitHub:        https://github.com/WordOps/WordOps
# Copyright (c) 2019 - WordOps
# This script is licensed under M.I.T
# -------------------------------------------------------------------------
# curl -sL git.io/fjAp3 | sudo -E bash -
# -------------------------------------------------------------------------
# Version 3.9.8.4 - 2019-08-28
# -------------------------------------------------------------------------

if [ -f /var/log/kc/keepcloud.log ]; then
    cd /var/log/kc/ || exit 1
    kc_link=$(curl -sL --upload-file keepcloud.log https://transfer.vtbox.net/keepcloud.txt)
    echo
    echo "Here the link to provide in your github issue : $kc_link"
    echo
    cd || exit 1
fi
