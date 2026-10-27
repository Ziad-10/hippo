# Terminal demo recorded with vhs (https://github.com/charmbracelet/vhs).
# Runs moodle_sync.py against moodle-sync/demo/fake_moodle.py and a copy of vault-template.
# Usage: DEMO=<demo folder with sync/ and "Demo Vault/"> vhs docs/demo.tape

Output docs/screenshots/demo.gif
Set Shell bash
Set FontSize 18
Set Width 1200
Set Height 640
Set Padding 24
Set Theme "Catppuccin Mocha"
Set TypingSpeed 45ms

Hide
Type 'export PS1="\[\e[1;35m\]moodle-sync\[\e[0m\] $ " MOODLE_SYNC_TOKEN_FILE="$DEMO/sync/token"; cd "$DEMO/sync"; clear' Enter
Show

Type "# Which Moodle courses map to which vault module?" Enter
Sleep 400ms
Type "python3 moodle_sync.py courses" Enter
Sleep 2s

Type "# Twice a day launchd runs this. New files land in the vault:" Enter
Sleep 400ms
Type "python3 moodle_sync.py sync" Enter
Sleep 2s

Type "ls ../To\ GoodNotes      # new PDFs, ready for the iPad" Enter
Sleep 2s

Type "cd '../Demo Vault/mindAssistant/Modules' && find . -name '*.pdf'  # by module" Enter
Sleep 4s
