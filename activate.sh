# Source in Bash from the project directory.
source .venv/bin/activate
export XDG_CACHE_HOME="$PWD/.cache"
export MPLBACKEND=Agg
export CPATH="$PWD/.native/usr/include${CPATH:+:$CPATH}"
export LIBRARY_PATH="$PWD/.native/usr/lib/x86_64-linux-gnu${LIBRARY_PATH:+:$LIBRARY_PATH}"
export LD_LIBRARY_PATH="$PWD/.native/usr/lib/x86_64-linux-gnu${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export PKG_CONFIG_PATH="$PWD/.native/usr/lib/x86_64-linux-gnu/pkgconfig${PKG_CONFIG_PATH:+:$PKG_CONFIG_PATH}"
