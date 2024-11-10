**🧙‍♂️ 1Fichier-dl Project**

(This is a fork version of the 1Fichier-dl project, which is no longer being maintained.)

<p align="left">
  <img src="https://github.com/leinad4mind/1fichier-dl/blob/main/screenshots/ico.png?raw=true"></img>
</p>

# 😺 1Fichier Downloader

This is the `1Fichier Download Manager` program that can be simply run as an `exe` file without installation on Windows.
We help you download at the fastest possible speed without having to wait for each download.

<p align="center">
  <img src="https://raw.githubusercontent.com/leinad4mind/1fichier-dl/main/screenshots/preview-1fichier-site.png"></img>
</p>
<p align="center">
  <b>You can copy and enter the 1fichier.com download link (URL) in your browser.</b>
</p>
<br/>
<br/>
<p align="center">
  <img src="https://raw.githubusercontent.com/leinad4mind/1fichier-dl/main/screenshots/preview-ouo-shortlink.png"></img>
</p>
<p align="center">
  <b>If you directly copy and enter the ouo.io shortened link (URL) in the browser, reCAPTCHA is automatically bypassed</b>
</p>
<br/>
<br/>
<p align="center">
  <img src="https://raw.githubusercontent.com/leinad4mind/1fichier-dl/main/screenshots/preview0.png"></img>
</p>

<p align="center">
  <b>Simple operation by entering the 1fichier link address in the 1fichier downloader program.</b>
</p>
<br/>
<br/>

<p align="center">
  <img src="https://raw.githubusercontent.com/leinad4mind/1fichier-dl/main/screenshots/preview_settings0.png"></img>
</p>

<p align="center">
  <b>Copy from clipboard or automatically download to bypass latency through multiple proxy servers.</b>
</p>
<br/>
<br/>

## 😼 Introduction to key features

⭐ You can manage your download list just by entering the download ‘link’ address, so you can hang it up and sleep to your heart’s content.

⭐ ‘Bypass’ the inconvenience of waiting time during continuous downloads for free users.

⭐ Users can directly enter the proxy list via URL in the Settings > Connections menu. (replaces default proxy)

⭐ In addition to the `1ficher` link, when you directly enter a shortened `URL` such as `ouo.io`, an automatic link that bypasses `reCAPTCHA` is added.

⭐ The default download folder path is the Windows ‘Download’ folder.

_Your life is short. Don't wait any longer._

<br/>
<br/>
<p align="center">
  <img src="https://raw.githubusercontent.com/leinad4mind/1fichier-dl/main/screenshots/Screenshot_Light.png"></img>
</p>

<p align="center">
  <b>Light Theme</b>
</p>
<br/>
<br/>

<p align="center">
  <img src="https://raw.githubusercontent.com/leinad4mind/1fichier-dl/main/screenshots/Screenshot_Dark.png"></img>
</p>

<p align="center">
  <b>Dark Theme</b>
</p>
<br/>
<br/>

## 😻 Improvements

- Readability of ‘GUI’ icon colors improved
- Change in the ‘default proxy list’ provided by default in the program.
- Easier build with `exe` for Windows using `PyInstaller` (`onefile` build applied)
- In case of proxy bypass, the proxy server currently being attempted is indicated as `Protocol://IP:PORT` in the `Status` item.
- Added `Progress %` decimal notation so that users can easily see the current progress.
- Applying `reCAPTCHA` bypass to the cumbersome `ouo.io` shortened `URL` when copying the link.
- Improvement of `UX` that worked awkwardly when adding a download link (prevention of loading screen and duplicate input)
- Added ‘Add from Clipboard’ function to allow immediate download of ‘URL’ copied to ‘Clipboard’
- Supports simultaneous proxy bypass downloads using `multi-thread` (default `3`, can be changed in settings, experimental)
  <br/>
  <br/>

## 😹 Things to improve in the future

- Improved speed slowdown due to repeated `requests` using `https` proxy (applied and testing `sock5` proxy)
- If you are connected to a proxy server with a slow download speed such as `100kb`, you need to automatically change to another proxy.
- Added exception handling when adding duplicate downloads with the same file name (processing required after actual 1fichier URL parsing)
- Supports asynchronous download using `Asyncio` instead of `Threading`, which is slow when downloading simultaneously (increases speed)
- In addition to the basic specification ‘1ficher’, it is necessary to check whether programs from other similar download sites are supported.
- Supports simultaneous proxy downloads using `Threading`
  <br/>
  <br/>

## 🙀 Run in a non-Windows environment

For development purposes, or when running the GUI directly through Python on Linux or Mac, you can run it from the project folder as follows.
There are currently only a few dependencies, but there will be no problem if you proceed based on Python 3.11 version.

```
pip install -r requirements.txt
python 1fichier-dl.py
```

<br/>
<br/>

## 😾 Building Windows exe using PyInstaller

We used `Python v3.11` version to build the `Legacy` project as a Windows program.
You can also install `requirements.txt` from the project folder and build it directly. (`pip install -r requirements.txt`)

```
pyinstaller --windowed --noconsole --onefile --noconfirm --clean --hiddenimport=_cffi_backend --additional-hooks-dir=. --icon=core/gui/res/ico.ico --paths "[Python_Lib_Path]" --add-data "core/gui/res/*.*;res/" ./1fichier-dl.py
```

Modified to `onefile` build for cleaner folder structure.
Since it is Windows-based, if there is a problem with the default file storage path, you must `build` in the folder structure rather than `onefile`.

When building a Windows program in `exe` format using `PyInstaller`, refer to the example of the command above.
The Python `Lib` path in the `paths` item will be a child of the `env` path when using conada.

Strangely, due to the chronic virus misdiagnosis problem of `PyInstaller`, I downloaded the `PyInstaller` source directly, initialized the existing build environment with `python ./waf distclean all`, and then installed `setup.py` in the folder with `pip install .`. You must install it yourself.

<br/>
<br/>

## 😽 Thank you so much.

- The button icons in the program use [Feather](https://feathericons.com/), which provides great free icons.
- The icon for the Windows program is a free icon from [svgrepo](https://www.svgrepo.com/).
- The program's loading overlay icon uses the free `svg` icon from [loading.io](https://loading.io).
- The free `https` proxy server list is provided by [FREE_PROXIES_LIST](https: //github.com/Zaeem20/FREE_PROXIES_LIST) project and many other uses
- The creator of the 1Fichier-dl project is `manuGMG`, branching from the version project of [jshsakura](https://github.com/jshsakura/1fichier-dl), which created an improved version from mine and I am forking to mine again.
- To reduce inconvenience when copying a link, use [xcscxr](https://github.com/xcscxr) to bypass `reCAPTCHA` for `ouo.io` shortened `URL`.
