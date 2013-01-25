fetch-yandex-news
=================

``fetch-yandex-news`` is utility for fetching news titles from ``Yandex.News``.

Status
------

Development branch

Compiling for Microsoft Windows
-------------------------------

Using cx_Freeze like:

    $ cxfreeze \
            --base-name=Win32GUI \
            --target-name=fetch-yandex-news-gui.exe \
            start_fetch_yandex_news_gui_2013_01_24.py
    $ echo "VERSION: $(git rev-list HEAD^..)" > dist/VERSION.txt
