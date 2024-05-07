#!/usr/bin/expect -f

# Set timeout for waiting for prompts (in seconds)
set timeout 30

# Run the ewc command MAKE SURE YOU ADD YOUR MNEMNONIC OF THE WALLET THAT HOLDS THE TOKENS TO BE DISTRIBUTED
spawn ewc nw -n alien -m "<ADD_YOUR_MNEMONIC_HERE>"

# Expect the prompt for the spending password SET A PASSWORD FOR THE WAL:LET
expect "Enter the spending password of the wallet"
send "<CREATE_A_PASSWORD>\r"

# Expect the confirmation prompt for the spending password
expect "Confirm the spending password of the wallet"
send "<SAME_PASSWORD>\r"

# Wait for the command to finish
expect eof
