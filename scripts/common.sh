function log {
    date=`/bin/date +%Y%m%d-%H%M%S`
    echo "${date} $1"
}

function endsWithSlash() {
    if [[ "$1" =~ .*/$ ]]; then
        return 0
    fi
    return 1
}
