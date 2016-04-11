# -*- coding: utf8 -*-

# Copyright (C) 2015 - Philipp Temminghoff <phil65@kodi.tv>
# This program is Free Software see LICENSE file for details

import urllib

import xbmc

import Utils

from kodi65 import addon
from kodi65.localdb import local_db
from kodi65.listitem import ListItem


AUDIO_DB_KEY = '58353d43204d68753987fl'
BASE_URL = 'http://www.theaudiodb.com/api/v1/json/%s/' % (AUDIO_DB_KEY)


def handle_albums(results):
    albums = []
    if not results.get('album'):
        return None
    local_desc = 'strDescription' + xbmc.getLanguage(xbmc.ISO_639_1).upper()
    for item in results['album']:
        desc = ""
        if local_desc in item and item[local_desc]:
            desc = item.get(local_desc, "")
        elif item.get('strDescriptionEN'):
            desc = item['strDescriptionEN']
        elif item.get('strDescription'):
            desc = item['strDescription']
        if item.get('strReview'):
            desc += "[CR][CR][B]%s:[/B][CR][CR]%s" % (addon.LANG(185), item['strReview'])
        album = ListItem(label=item['strAlbum'],
                         path="")
        album.set_infos({'artist': [item['strArtist']],
                         'mediatype': "album",
                         'genre': item['strGenre'],
                         'year': item['intYearReleased']})
        album.set_properties({'mbid': item['strMusicBrainzID'],
                              'id': item['idAlbum'],
                              'audiodb_id': item['idAlbum'],
                              'album_description': desc,
                              'album_mood': item['strMood'],
                              'album_style': item['strStyle'],
                              'speed': item['strSpeed'],
                              'album_Theme': item['strTheme'],
                              'type': item['strReleaseFormat'],
                              'loved': item['intLoved'],
                              'location': item['strLocation'],
                              'itunes_id': item['strItunesID'],
                              'amazon_id': item['strAmazonID'],
                              'sales': item['intSales']})
        album.set_artwork({'thumb': item['strAlbumThumb'],
                           'spine': item['strAlbumSpine'],
                           'cdart': item['strAlbumCDart'],
                           'thumbback': item['strAlbumThumbBack']})
        albums.append(album)
    return local_db.compare_album_with_library(albums)


def handle_tracks(results):
    tracks = []
    if not results.get('track'):
        return None
    for item in results['track']:
        youtube_id = Utils.extract_youtube_id(item.get('strMusicVid', ''))
        track = ListItem(label=item['strTrack'],
                         path=Utils.convert_youtube_url(item['strMusicVid']))
        track.set_infos({'title': item['strTrack'],
                         'album': item['strAlbum'],
                         'artist': [item['strArtist']],
                         'mediatype': "song"})
        track.set_properties({'mbid': item['strMusicBrainzID']})
        track.set_art({'thumb': "http://i.ytimg.com/vi/%s/0.jpg" % youtube_id})
        tracks.append(track)
    return tracks


def handle_musicvideos(results):
    if not results.get('mvids'):
        return []
    mvids = []
    for item in results['mvids']:
        youtube_id = Utils.extract_youtube_id(item.get('strMusicVid', ''))
        mvid = ListItem(label=item['strTrack'],
                        path=Utils.convert_youtube_url(item['strMusicVid']))
        mvid.set_infos({'title': item['strTrack'],
                        'plot': item['strDescriptionEN'],
                        'mediatype': "musicvideo"})
        mvid.set_properties({'id': item['idTrack']})
        mvid.set_art({'thumb': "http://i.ytimg.com/vi/%s/0.jpg" % youtube_id})
        mvids.append(mvid)
    return mvids


def extended_artist_info(results):
    artists = []
    if not results.get('artists'):
        return None
    local_bio = 'strBiography' + addon.setting("LanguageID").upper()
    for artist in results['artists']:
        description = ""
        if local_bio in artist and artist[local_bio]:
            description = artist.get(local_bio)
        elif artist.get('strBiographyEN'):
            description = artist.get('strBiographyEN')
        elif artist.get('strBiography'):
            description = artist.get('strBiography')
        if 'strReview' in artist and artist['strReview']:
            description += "[CR]" + artist.get('strReview')
        artist = {'label': artist.get('strArtist'),
                  'artist': artist.get('strArtist'),
                  'mediatype': "artist",
                  'Country': artist.get('strCountry'),
                  'mbid': artist.get('strMusicBrainzID'),
                  'thumb': artist.get('strArtistThumb'),
                  'Banner': artist.get('strArtistBanner'),
                  'clearlogo': artist.get('strArtistLogo'),
                  'fanart': artist.get('strArtistFanart'),
                  'fanart2': artist.get('strArtistFanart2'),
                  'fanart3': artist.get('strArtistFanart3'),
                  'Artist_Mood': artist.get('strMood'),
                  'Artist_Born': artist.get('intBornYear'),
                  'Artist_Formed': artist.get('intFormedYear'),
                  'Artist_Died': artist.get('intDiedYear'),
                  'Artist_Disbanded': artist.get('strDisbanded'),
                  'Artist_Mood': artist.get('strMood'),
                  'Artist_Description': description,
                  'Artist_Genre': artist.get('strGenre'),
                  'Artist_Style': artist.get('strStyle'),
                  'CountryCode': artist.get('strCountryCode'),
                  'Website': artist.get('strWebsite'),
                  'Twitter': artist.get('strTwitter'),
                  'Facebook': artist.get('strFacebook'),
                  'LastFMChart': artist.get('strLastFMChart'),
                  'Gender': artist.get('strGender'),
                  'audiodb_id': artist.get('idArtist'),
                  'Members': artist.get('intMembers')}
        artists.append(artist)
    if artists:
        return artists[0]
    else:
        return {}


def get_artist_discography(search_str):
    if not search_str:
        return []
    params = {"s": search_str}
    results = get_data("searchalbum", params)
    return handle_albums(results)


def get_artist_details(search_str):
    if not search_str:
        return []
    params = {"s": search_str}
    results = get_data("search", params)
    return extended_artist_info(results)


def get_most_loved_tracks(search_str="", mbid=""):
    if mbid:
        url = 'track-top10-mb'
        params = {"s": mbid}
    elif search_str:
        url = 'track-top10'
        params = {"s": search_str}
    else:
        return []
    results = get_data(url, params)
    return handle_tracks(results)


def get_album_details(audiodb_id="", mbid=""):
    if audiodb_id:
        url = 'album'
        params = {"m": audiodb_id}
    elif mbid:
        url = 'album-mb'
        params = {"i": mbid}
    else:
        return []
    results = get_data(url, params)
    return handle_albums(results)[0]


def get_musicvideos(audiodb_id):
    if not audiodb_id:
        return []
    params = {"i": audiodb_id}
    results = get_data("mvid", params)
    return handle_musicvideos(results)


def get_track_details(audiodb_id):
    if not audiodb_id:
        return []
    params = {"m": audiodb_id}
    results = get_data("track", params)
    return handle_tracks(results)


def get_data(url, params):
    params = {k: v for k, v in params.items() if v}
    params = {k: unicode(v).encode('utf-8') for k, v in params.items()}
    url = "%s%s.php?%s" % (BASE_URL, url, urllib.urlencode(params))
    return Utils.get_JSON_response(url=url,
                                   folder="TheAudioDB")
