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
    tmux send-keys -t 'Editor' '/usr/local/bin/code -a $HOME tunnel --name $USER --cli-data-dir=/home/$USER/.vscode --install-extension ms-python.python --install-extension mechatroner.rainbow-csv --install-extension janisdd.vscode-edit-csv --install-extension ms-toolsai.jupyter --install-extension github.copilot --install-extension github.copilot-chat --install-extension gera2ld.markmap-vscode --install-extension yzhang.markdown-all-in-one --install-extension mutantdino.resourcemonitor --install-extension ms-vsliveshare.vsliveshare --install-extension ms-ceintl.vscode-language-pack-pt-br --install-extension charliermarsh.ruff' C-m

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
