from flask import current_app as app
from utils.mangaupdates import get_id as get_id_mu
from utils.line import get_id as get_id_line
from utils.bato_worker import worker
from utils.detect_language import detect_language
from utils.common_code import author_type_merger
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from typing import Dict, Any
import requests
import random
import re
from typing import Tuple, List

mirrors = ('dto.to', 'fto.to', 'hto.to', 'jto.to', 'mto.to', 'wto.to', 'batocomic.com', 'batocomic.net',
          'batocomic.org', 'batotoo.com', 'batotwo.com', 'battwo.com', 'comiko.net', 'comiko.org', 'readtoto.com',
          'readtoto.net', 'readtoto.org', 'xbato.com', 'xbato.net', 'xbato.org', 'zbato.com', 'zbato.net',
          'zbato.org', 'bato.to', 'mangatoto.com', 'mangatoto.net', 'mangatoto.org')

def get_id(url: str) -> int:
    mirrors_ = set(mirrors)
    url = urlparse(url)
    if url.hostname not in mirrors_:
        return 0
    try:
        id_bato = re.search(r'/(title|series)/(\d+)', url.path)[2]
    except:
        app.logger.warning(f"Invalid URL format: {url}")
        return 0
    return id_bato

def series(id_bato: int) -> Tuple[Dict[str, str], int]:
    mirrors_ = list(mirrors)

    for attempt in range(26):
        try:
            r = random.choice(mirrors_)
            url = f"https://{r}/series/{id_bato}"
            mirrors_.remove(r)

            response = requests.get(url, timeout=10)
            if response.text == "404 Page Not Found (1)":
                return {"result": "KO", "error": "Series not found"}, 404
            response.raise_for_status()
            break

        except (requests.RequestException, requests.exceptions.Timeout) as e:
            if attempt == 26:
                app.logger.error(f"Fetching data for ID:{id_bato}: {e}")
                return {"result": "KO", "error": "Cannot connect to any mirror."}, 502
            continue

    soup = BeautifulSoup(response.text, "html.parser")
    info = soup.select_one("div#mainer div.container-fluid")

    title = info.select_one("h3").get_text(strip=True)
    title = re.sub(
        r"\([^()]*\)|\{[^{}]*\}|\[(?:(?!]).)*\]|«[^»]*»|〘[^〙]*〙|「[^」]*」|『[^』]*』|≪[^≫]*≫|﹛[^﹜]*﹜|〖[^〖〗]*〗|𖤍.+?𖤍|《[^》]*》|⌜.+?⌝|⟨[^⟩]*⟩|/Official|/ Official",
        '', title, flags=re.IGNORECASE).strip()

    author = ""
    artist = ""
    genres_ = ""
    original_language = ""
    for attr in info.select("div.attr-item"):
        label = attr.get_text(strip=True).lower()
        if "author" in label:
            span = attr.find("span")
            author_links = span.find_all('a')
            author = [link.get_text(strip=True) for link in author_links]
        elif "artist" in label:
            span = attr.find("span")
            artist_links = span.find_all("a")
            artist = [link.get_text(strip=True) for link in artist_links]
        elif "genres" in label:
            span = attr.find_all("span")[0].find_all(["span", "u", "b"])
            genres_ = [x.get_text(strip=True) for x in span]
        elif "original language" in label:
            span = attr.find("span")
            original_language = span.get_text(strip=True)

    description = info.select_one("div.limit-html")
    description = description.get_text(strip=True) if description else ""
    description = description.replace("\n\n", "\n")

    authors= []
    for i in author:
        authors.append({"name": i, "type": "author"})
    for i in artist:
        authors.append({"name": i, "type": "artist"})
    authors = author_type_merger(authors)

    genres, type_, os_a, accepted_languages = worker(genres_, original_language)
    accepted_languages.extend(app.config["TITLE_LANGUAGES"])

    alt_titles = []
    alt_titles_all = []
    alt_titles_ = soup.select_one("div.pb-2.alias-set.line-b-f")
    if alt_titles_ and alt_titles_.get_text(strip=True):
        alt_titles_all = [t.strip() for t in alt_titles_.get_text().split('/')]
    for t in alt_titles_all:
        lang, confidence = detect_language(t)
        if confidence and lang in accepted_languages:
            alt_titles.append(t)

    thumbnail_ = soup.select_one("div.attr-cover img")
    thumbnail = thumbnail_["src"] if thumbnail_ else ""


    extra_info_links = []
    h5_extra = soup.find("h5", class_="mt-3 text-muted", string="Extra Info:")
    if h5_extra:
        div_extra = h5_extra.find_next("div")
        if div_extra:
            extra_info_links: List[str] = re.findall(r"https?://\S+", div_extra.get_text())

    ids: Dict[str, Any] = {"bato": id_bato}
    for i in extra_info_links:
        i_ = urlparse(i)
        if i_.hostname == "www.mangaupdates.com":
            ids['mu'] = get_id_mu(i)
        elif i_.hostname == "www.webtoons.com":
            ids['line'] = get_id_line(i)
        else:
            continue

    return {
        "ids": ids,
        "title": title,
        "alt_titles": alt_titles,
        "type": type_,
        "description": description,
        "is_md": False,
        "genres": genres,
        "authors": authors,
        "os_a": os_a,
        "thumbnail": thumbnail,
    }, 200

if __name__ == "__main__":
    pass
