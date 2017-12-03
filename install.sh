#!/bin/sh

if [ $# -ne 2 ]; then
    echo "Usage: $0 <config> <destination>" >&2
    exit 1
fi

CONFFILE="$1"
DIR="${2%/}"
[ -f "$CONFFILE" ] || { echo "Config gile '$CONFFILE' not found." >&2; exit 1; }
[ -d "$DIR" ] || { echo "Directory '$DIR' not found." >&2; exit 1; }
cat "$(( cat "$CONFFILE"; echo install_files ) | m4 -)" | while read FNAME
do
    SUBDIR="`dirname "$FNAME"`"
    [ -d "$DIR/$SUBDIR" ] || mkdir -p "$DIR/$SUBDIR" || {
        echo "Creation of directory '$DIR/$SUBDIR' failed." >&2
        exit 2;
    }
    if [ "$FNAME" = "js/main.js" -o "$FNAME" = "index.html" ]; then
        FNAMEIN="${FNAME}.result"
        cat "$CONFFILE" "$FNAME" | m4 - >"$FNAMEIN"
    else
        FNAMEIN="$FNAME"
    fi
    diff -q "$DIR/$FNAME" "$FNAMEIN" 2>/dev/null || cp -v "$FNAMEIN" "$DIR/$FNAME" || {
        echo "Copy of file '$FNAME' to directory '$DIR' failed." >&2
        exit 3;
    }
done

exit 0
