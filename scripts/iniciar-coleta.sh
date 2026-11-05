#!/bin/sh
set -eu
# These stores exist only inside the disposable container; host trust is untouched.
for path in /root/.pki/nssdb /root/.local/share/pki/nssdb; do
    mkdir -p "$path"
    certutil -N -d "sql:$path" --empty-password
    certutil -A -d "sql:$path" -n session-proxy -t 'C,,' -i /run/proxy-ca.crt
done
exec /workspace/venvs/scriptlattes/bin/python /app/scripts/navegar-lattes.py
