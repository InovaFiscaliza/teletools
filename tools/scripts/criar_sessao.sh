#!/bin/sh

# Check if current user is lx.svc.ficdr.pd and exit if so
if [ "$(whoami)" = "lx.svc.ficdr.pd" ]; then
    echo "Error: This script cannot be executed by user lx.svc.ficdr.pd"
    exit 1
fi

# Set Session Name
SESSION="VSCODE"
SESSIONEXISTS=$(tmux list-sessions | grep $SESSION)

# Only create tmux session if it doesn't already exist
if [ "$SESSIONEXISTS" = "" ]
then
    # Change the current folder to the user's Home
    cd
    # Start New Session with our name
    tmux new-session -d -s $SESSION

    # Name first Pane and clear terminal
    tmux rename-window -t 0 'Editor'

    # Define the list of VSCode extensions to install
    EXTENSIONS="
        ms-python.python
        mechatroner.rainbow-csv
        janisdd.vscode-edit-csv
        ms-toolsai.jupyter
        github.copilot
        github.copilot-chat
        gera2ld.markmap-vscode
        yzhang.markdown-all-in-one
        mutantdino.resourcemonitor
        ms-vsliveshare.vsliveshare
        ms-ceintl.vscode-language-pack-pt-br
        charliermarsh.ruff
    "

    # Build the install-extension arguments
    EXT_ARGS=""
    for ext in $EXTENSIONS; do
        EXT_ARGS="$EXT_ARGS --install-extension $ext"
    done

    # Send the VSCode command to the tmux pane
    tmux send-keys -t 'Editor' "/usr/local/bin/code -a \$HOME tunnel --name \$USER --cli-data-dir=/home/\$USER/.vscode \$EXT_ARGS" C-m
    # Split the window vertically to create a second pane
    tmux split-window -h -t $SESSION:0

    # # Setup the bottom pane for vscode server
    # tmux send-keys -t $SESSION:0.1 'clear' C-m

    # # Optional: Adjust pane sizes (make top pane larger)
    # tmux resize-pane -t $SESSION:0.1 -U 10

    # Focus on the top pane (Main)
    tmux select-pane -t $SESSION:0.0
    
fi

# Attach Session, on the Main window
tmux attach-session -t $SESSION:0
