# -*- coding: utf8 -*-

# Copyright (C) 2015 - Philipp Temminghoff <phil65@kodi.tv>
# This program is Free Software see LICENSE file for details

import xbmc
import xbmcgui
from ..Utils import *
from ..TheMovieDB import *
from ..WindowManager import wm
from T9Search import T9Search
from collections import deque
import ast
from ..OnClickHandler import OnClickHandler
from .. import VideoPlayer

PLAYER = VideoPlayer.VideoPlayer()
ch = OnClickHandler()


class DialogBaseList(object):
    ACTION_PREVIOUS_MENU = [92, 9]
    ACTION_EXIT_SCRIPT = [13, 10]

    def __init__(self, *args, **kwargs):
        super(DialogBaseList, self).__init__(*args, **kwargs)
        self.listitem_list = kwargs.get('listitems', None)
        self.last_searches = deque(maxlen=10)
        self.search_str = kwargs.get('search_str', "")
        self.filter_label = kwargs.get("filter_label", "")
        self.mode = kwargs.get("mode", "filter")
        self.filters = kwargs.get('filters', [])
        self.color = kwargs.get('color', "FFAAAAAA")
        self.page = 1
        self.column = None
        self.last_position = 0
        self.total_pages = 1
        self.total_items = 0
        check_version()

    def onInit(self):
        super(DialogBaseList, self).onInit()
        HOME.setProperty("WindowColor", self.color)
        self.window.setProperty("WindowColor", self.color)
        if SETTING("alt_browser_layout") == "true":
            self.window.setProperty("alt_layout", "true")
        self.update_ui()
        xbmc.sleep(200)
        if self.total_items > 0:
            xbmc.executebuiltin("SetFocus(500)")
            self.getControl(500).selectItem(self.last_position)
        else:
            xbmc.executebuiltin("SetFocus(6000)")

    def onAction(self, action):
        if action in self.ACTION_PREVIOUS_MENU:
            self.close()
            wm.pop_stack()
        elif action in self.ACTION_EXIT_SCRIPT:
            self.close()
        elif action == xbmcgui.ACTION_CONTEXT_MENU:
            self.context_menu()

    def onFocus(self, control_id):
        old_page = self.page
        if control_id == 600:
            self.go_to_next_page()
        elif control_id == 700:
            self.go_to_prev_page()
        if self.page != old_page:
            self.update()

    def onClick(self, control_id):
        if control_id == 5001:
            self.get_sort_type()
            self.update()
        elif control_id == 5005:
            if len(self.filters) > 1:
                listitems = ["%s: %s" % (f["typelabel"], f["label"]) for f in self.filters]
                listitems.append(LANG(32078))
                index = xbmcgui.Dialog().select(heading=ADDON.getLocalizedString(32077),
                                                list=listitems)
                if index == -1:
                    return None
                elif index == len(listitems) - 1:
                    self.filters = []
                else:
                    del self.filters[index]
            else:
                self.filters = []
            self.page = 1
            self.mode = "filter"
            self.update()

        elif control_id == 6000:
            settings_str = SETTING("search_history")
            if settings_str:
                self.last_searches = deque(ast.literal_eval(settings_str), maxlen=10)
            dialog = T9Search(u'script-%s-T9Search.xml' % ADDON_NAME, ADDON_PATH,
                              call=self.search,
                              start_value=self.search_str,
                              history=self.last_searches)
            dialog.doModal()
            if dialog.classic_mode:
                result = xbmcgui.Dialog().input(heading=LANG(16017),
                                                type=xbmcgui.INPUT_ALPHANUM)
                if result and result > -1:
                    self.search(result)
            if self.search_str:
                listitem = {"label": self.search_str}
                if listitem in self.last_searches:
                    self.last_searches.remove(listitem)
                self.last_searches.appendleft(listitem)
                setting_str = str(list(self.last_searches))
                ADDON.setSetting("search_history", setting_str)
            if self.total_items > 0:
                self.setFocusId(500)

    def search(self, label):
        if not label:
            return None
        self.search_str = label
        self.mode = "search"
        self.filters = []
        self.page = 1
        self.update_content()
        self.update_ui()

    def set_filter_url(self):
        filter_list = []
        for item in self.filters:
            filter_list.append("%s=%s" % (item["type"], item["id"]))
        self.filter_url = "&".join(filter_list)
        if self.filter_url:
            self.filter_url += "&"

    def set_filter_label(self):
        filter_list = []
        for item in self.filters:
            filter_label = item["label"].replace("|", " | ").replace(",", " + ")
            filter_list.append("[COLOR FFAAAAAA]%s:[/COLOR] %s" % (item["typelabel"], filter_label))
        self.filter_label = "  -  ".join(filter_list)

    def update_content(self, add=False, force_update=False):
        if add:
            self.old_items = self.listitems
        else:
            self.old_items = []
        data = self.fetch_data(force=force_update)
        self.listitems = data.get("listitems", [])
        self.total_pages = data.get("results_per_page", "")
        self.total_items = data.get("total_results", "")
        self.next_page_token = data.get("next_page_token", "")
        self.prev_page_token = data.get("prev_page_token", "")
        self.listitems = self.old_items + create_listitems(self.listitems)

    def update_ui(self):
        if not self.listitems and self.getFocusId() == 500:
            self.setFocusId(6000)
        self.getControl(500).reset()
        if self.listitems:
            self.getControl(500).addItems(self.listitems)
            if self.column is not None:
                self.getControl(500).selectItem(self.column)
        self.window.setProperty("TotalPages", str(self.total_pages))
        self.window.setProperty("TotalItems", str(self.total_items))
        self.window.setProperty("CurrentPage", str(self.page))
        self.window.setProperty("Filter_Label", self.filter_label)
        self.window.setProperty("Sort_Label", self.sort_label)
        if self.page == self.total_pages:
            self.window.clearProperty("ArrowDown")
        else:
            self.window.setProperty("ArrowDown", "True")
        if self.page > 1:
            self.window.setProperty("ArrowUp", "True")
        else:
            self.window.clearProperty("ArrowUp")
        if self.order == "asc":
            self.window.setProperty("Order_Label", LANG(584))
        else:
            self.window.setProperty("Order_Label", LANG(585))

    @busy_dialog
    def update(self, force_update=False):
        self.update_content(force_update=force_update)
        self.update_ui()

    def add_filter(self, key, value, typelabel, label, force_overwrite=False):
        index = -1
        new_filter = {"id": value,
                      "type": key,
                      "typelabel": typelabel,
                      "label": label}
        if new_filter in self.filters:
            return False
        for i, item in enumerate(self.filters):
            if item["type"] == key:
                index = i
                break
        if not value:
            return False
        if index == -1:
            self.filters.append(new_filter)
            return None
        if force_overwrite:
            self.filters[index]["id"] = urllib.quote_plus(str(value))
            self.filters[index]["label"] = str(label)
            return None
        dialog = xbmcgui.Dialog()
        ret = dialog.yesno(heading=LANG(587),
                           line1=LANG(32106),
                           nolabel="OR",
                           yeslabel="AND")
        if ret:
            self.filters[index]["id"] = self.filters[index]["id"] + "," + urllib.quote_plus(str(value))
            self.filters[index]["label"] = self.filters[index]["label"] + "," + label
        else:
            self.filters[index]["id"] = self.filters[index]["id"] + "|" + urllib.quote_plus(str(value))
            self.filters[index]["label"] = self.filters[index]["label"] + "|" + label
