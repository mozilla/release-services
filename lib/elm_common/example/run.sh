#!/bin/bash

rm -f bundle.js
touch bundle.js
for i in ../*.js; do
  cat $i >> bundle.js
done
cat index.js >> bundle.js
for i in ../*.elm; do
  rm -f $(basename $i)
  ln -s $i .
done

elm-make Main.elm
if [[ $? != 0 ]]; then
  exit 1
fi

sed -i -e "s,>Elm.Main.fullscreen(), src=\"/bundle.js\">$LIBS,g" index.html

python -m SimpleHTTPServer
