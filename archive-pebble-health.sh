ARCHIVE="/path/to/archive/pebblecsv.tar"
PEBBLE_HEALTH="/var/www/localhost/htdocs/pebble-health/uploads/health.csv"
DATE=`date --iso-8601=seconds`
cp ${PEBBLE_HEALTH} "/tmp/${DATE}-hr.csv"
if [[ -f "${ARCHIVE}.zstd" ]]; then
  zstd -d "${ARCHIVE}.zstd" -o "${ARCHIVE}" --rm
  tar -rf "${ARCHIVE}" "/tmp/${DATE}-hr.csv"
  zstd "${ARCHIVE}" -o "${ARCHIVE}.zstd" --rm -f
else
  tar -cvf "${ARCHIVE}.zstd" "/tmp/${DATE}-hr.csv" --zstd
fi
echo "" > "${PEBBLE_HEALTH}
