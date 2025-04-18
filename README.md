# Chat with Capri

AI assistant packaged with love.



# Steps

> python3 -m venv venv

> source venv/bin/activate

> pip3 install -r requirements.txt



## Generate the .deb file (Linux)

> pyinstaller --onefile --windowed capri.py

> mkdir -p capri-1.0/usr/local/bin/

> cp -f dist/capri capri-1.0/usr/local/bin/Capri

> dpkg-deb --build capri-1.0



### One liner:
> pyinstaller --onefile --windowed capri.py && mkdir -p capri-1.0/usr/local/bin/ && cp -f dist/capri capri-1.0/usr/local/bin/Capri && dpkg-deb --build capri-1.0



## Install (Linux)

> Install: capri-1.0.deb by double clicking on it.

> Uninstall: sudo apt remove capri 
