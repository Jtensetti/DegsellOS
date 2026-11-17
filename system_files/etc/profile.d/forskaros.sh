# ForskarOS: dagens princip när en ny terminal öppnas.
case $- in
  *i*)
    if [ -z "${FORSKAROS_PRINCIP_VISAD:-}" ] && command -v forskaros-princip >/dev/null 2>&1; then
      forskaros-princip 2>/dev/null
      export FORSKAROS_PRINCIP_VISAD=1
    fi ;;
esac
