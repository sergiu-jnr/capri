# Chat with Capri

AI assistant packaged with love.


## Example to update the build and generate the .dev file

> pyinstaller --onefile --windowed --icon=logo.png aio-pyqt.py && cp -f dist/aio-pyqt capri-1.0/usr/local/bin/Capri && dpkg-deb --build capri-1.0