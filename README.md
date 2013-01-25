get-yandex-news
===============

``get-yandex-news`` is utility for getting news titles from ``Yandex.News``.

Status
------

Development branch

Compiling for Microsoft Windows
-------------------------------

Using cx_Freeze like:

    $ cxfreeze \
            --base-name=Win32GUI \
            --target-name=get-yandex-news-gui.exe \
            start_get_yandex_news_2013_01_24.py
    $ echo "VERSION: $(git rev-list HEAD^..)" > dist/VERSION.txt
    $ git status >> dist/VERSION.txt
