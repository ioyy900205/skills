#!/usr/bin/env bash
# Serve a report directory as read-only static files, so it can be read over a link.
#
#   serve_report.sh start <dir> [--port 8845] [--host 10.0.0.5] [--name mytag]
#   serve_report.sh status [--name mytag]
#   serve_report.sh stop   [--name mytag]
#   serve_report.sh list
#
# Design notes worth keeping if you rewrite this:
#
#   * Binds ONE interface, never 0.0.0.0. A lab host usually also sits on an
#     InfiniBand fabric and a few docker bridges; publishing to all of them to
#     reach one colleague is a much bigger exposure than intended.
#   * Serves a directory, not the repo. Point it at the report directory so
#     weights, raw data and checkpoints are not reachable by path traversal.
#   * Read-only: python's http.server has no upload path. Do not swap in
#     something with write support to "make it easier".
#
# The page itself is self-contained, so this is a convenience for sharing a
# link, not a dependency. Anyone can also just be sent the .html file.
set -euo pipefail

STATE_DIR="${XDG_RUNTIME_DIR:-/tmp}/serve_report"
mkdir -p "$STATE_DIR"

NAME=""; PORT=""; HOST=""; DIR=""
CMD="${1:-}"; shift || true
while [[ $# -gt 0 ]]; do
  case "$1" in
    --port) PORT="$2"; shift 2 ;;
    --host) HOST="$2"; shift 2 ;;
    --name) NAME="$2"; shift 2 ;;
    --port=*) PORT="${1#*=}"; shift ;;
    --host=*) HOST="${1#*=}"; shift ;;
    --name=*) NAME="${1#*=}"; shift ;;
    -*) echo "unknown option: $1" >&2; exit 2 ;;
    *) DIR="$1"; shift ;;
  esac
done

# Default host: the address of the route to the outside, i.e. the interface a
# colleague on the lab network can actually reach. Falls back to loopback.
default_host() {
  local ip=""
  if command -v ip >/dev/null 2>&1; then
    ip="$(ip route get 1.1.1.1 2>/dev/null | awk '{for(i=1;i<=NF;i++) if ($i=="src") {print $(i+1); exit}}' || true)"
  fi
  echo "${ip:-127.0.0.1}"
}

python_bin() {
  for candidate in "${SERVE_PYTHON:-}" ./.venv/bin/python ../.venv/bin/python python3 python; do
    [[ -n "$candidate" ]] && command -v "$candidate" >/dev/null 2>&1 && { echo "$candidate"; return; }
  done
  echo "no python found" >&2; exit 1
}

slug() { echo "$1" | tr -c 'A-Za-z0-9._-' '_' | cut -c1-60; }

pid_file() { echo "$STATE_DIR/$1.pid"; }
meta_file() { echo "$STATE_DIR/$1.meta"; }

running() { [[ -f "$(pid_file "$1")" ]] && kill -0 "$(cat "$(pid_file "$1")")" 2>/dev/null; }

start() {
  [[ -n "$DIR" ]] || { echo "usage: $0 start <dir> [--port N] [--host IP] [--name TAG]" >&2; exit 2; }
  [[ -d "$DIR" ]] || { echo "not a directory: $DIR" >&2; exit 1; }
  DIR="$(cd "$DIR" && pwd)"
  [[ -f "$DIR/index.html" ]] || echo "note: no index.html in $DIR; the URL will show a file listing" >&2

  [[ -n "$NAME" ]] || NAME="$(slug "$(basename "$DIR")")"
  [[ -n "$HOST" ]] || HOST="$(default_host)"
  [[ -n "$PORT" ]] || PORT=8845

  case "$HOST" in
    0.0.0.0|::|"[::]")
      echo "refusing wildcard bind $HOST; choose one explicit interface address" >&2
      exit 2 ;;
  esac
  [[ "$PORT" =~ ^[0-9]+$ ]] && (( PORT >= 1 && PORT <= 65535 )) || {
    echo "invalid port: $PORT" >&2; exit 2;
  }

  if running "$NAME"; then
    echo "already running (pid $(cat "$(pid_file "$NAME")"))"
    cat "$(meta_file "$NAME")"
    return 0
  fi

  # Fail loudly on a taken port rather than silently serving the wrong thing.
  if command -v ss >/dev/null 2>&1 && ss -tln 2>/dev/null | grep -q "[^0-9]$PORT "; then
    echo "port $PORT is already in use; pass --port with a free one" >&2
    exit 1
  fi

  local py log
  py="$(python_bin)"
  log="$STATE_DIR/$NAME.log"
  nohup "$py" -m http.server "$PORT" --bind "$HOST" --directory "$DIR" >>"$log" 2>&1 &
  echo $! >"$(pid_file "$NAME")"
  sleep 1
  if running "$NAME"; then
    printf '  报告  http://%s:%s/\n  目录  %s\n' "$HOST" "$PORT" "$DIR" >"$(meta_file "$NAME")"
    echo "started (pid $(cat "$(pid_file "$NAME")"), name $NAME)"
    cat "$(meta_file "$NAME")"
  else
    rm -f "$(pid_file "$NAME")"
    echo "failed to start; see $log" >&2
    tail -5 "$log" >&2 || true
    exit 1
  fi
}

stop() {
  [[ -n "$NAME" ]] || { [[ -n "$DIR" ]] && NAME="$(slug "$(basename "$DIR")")"; }
  [[ -n "$NAME" ]] || { echo "pass --name or the directory" >&2; exit 2; }
  if running "$NAME"; then
    kill "$(cat "$(pid_file "$NAME")")"
    rm -f "$(pid_file "$NAME")" "$(meta_file "$NAME")"
    echo "stopped $NAME"
  else
    rm -f "$(pid_file "$NAME")" "$(meta_file "$NAME")"
    echo "not running"
  fi
}

status() {
  [[ -n "$NAME" ]] || { [[ -n "$DIR" ]] && NAME="$(slug "$(basename "$DIR")")"; }
  [[ -n "$NAME" ]] || { list; return; }
  if running "$NAME"; then
    echo "running (pid $(cat "$(pid_file "$NAME")"))"
    cat "$(meta_file "$NAME")"
  else
    echo "not running"; return 1
  fi
}

list() {
  local any=0
  for f in "$STATE_DIR"/*.pid; do
    [[ -e "$f" ]] || continue
    local n; n="$(basename "$f" .pid)"
    if running "$n"; then any=1; echo "$n (pid $(cat "$f"))"; sed 's/^/  /' "$(meta_file "$n")"; fi
  done
  [[ $any -eq 1 ]] || echo "nothing running"
}

case "$CMD" in
  start)   start ;;
  stop)    stop ;;
  restart) stop || true; start ;;
  status)  status ;;
  list)    list ;;
  *) echo "usage: $0 {start <dir>|stop|status|restart|list} [--port N] [--host IP] [--name TAG]" >&2; exit 2 ;;
esac
