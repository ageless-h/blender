# SPDX-FileCopyrightText: 2009-2023 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

from __future__ import annotations

import bpy
from bpy.types import Operator
from bpy.props import (
    BoolProperty,
    StringProperty,
)
from bpy.app.translations import contexts as i18n_contexts


def _lang_module_get(sc):
    return __import__(
        "_console_" + sc.language,
        # for python 3.3, maybe a bug???
        level=0,
    )


class ConsoleExec(Operator):
    """Execute the current console line as a Python expression"""
    bl_idname = "console.execute"
    bl_label = "Console Execute"
    bl_options = {'UNDO_GROUPED'}

    interactive: BoolProperty(
        options={'SKIP_SAVE'},
    )

    @classmethod
    def poll(cls, context):
        return (context.area and context.area.type == 'CONSOLE')

    def execute(self, context):
        sc = context.space_data

        module = _lang_module_get(sc)
        execute = getattr(module, "execute", None)

        if execute is not None:
            return execute(context, self.interactive)
        else:
            print("Error: bpy.ops.console.execute_{:s} - not found".format(sc.language))
            return {'FINISHED'}


class ConsoleHistorySearch(Operator):
    bl_idname = "console.history_search"
    bl_label = "Console History Search"

    @classmethod
    def poll(cls, context):
        return (context.area and context.area.type == 'CONSOLE')

    def _update_header(self, context):
        match = "[no match]"
        if getattr(self, "_matches", None):
            match = self._matches[self._match_index]
        query = getattr(self, "_query", "")
        context.area.header_text_set("History Search: {:s}  {:s}".format(query, match))

    def cancel(self, context):
        if context.area:
            context.area.header_text_set(None)

    def _update_matches(self, context):
        sc = context.space_data
        query = getattr(self, "_query", "")
        query_cf = query.casefold()

        matches = []
        seen = set()
        for cl in reversed(sc.history[:-1]):
            body = cl.body
            if not body:
                continue
            if query_cf and (query_cf not in body.casefold()):
                continue
            if body in seen:
                continue
            seen.add(body)
            matches.append(body)

        self._matches = matches
        if not matches:
            self._match_index = 0
        else:
            self._match_index = self._match_index % len(matches)

        self._update_header(context)

    def _cycle_match(self, context, step):
        if not getattr(self, "_matches", None):
            self._update_header(context)
            return

        self._match_index = (self._match_index + step) % len(self._matches)
        self._update_header(context)

    def invoke(self, context, _event):
        sc = context.space_data

        try:
            line_object = sc.history[-1]
        except:
            return {'CANCELLED'}

        self._original_text = line_object.body
        self._query = ""
        self._match_index = 0
        self._matches = []

        self._update_matches(context)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if not (context.area and context.area.type == 'CONSOLE'):
            if context.area:
                context.area.header_text_set(None)
            return {'CANCELLED'}

        if event.type in {'WHEELUPMOUSE', 'WHEELDOWNMOUSE', 'MIDDLEMOUSE'}:
            return {'PASS_THROUGH'}

        if event.type == 'TEXTINPUT':
            text = (
                getattr(event, "unicode", "") or
                getattr(event, "ascii", "") or
                getattr(event, "text", "")
            )
            if text:
                self._query += text
                self._match_index = 0
                self._update_matches(context)
            return {'RUNNING_MODAL'}

        if event.type == 'BACK_SPACE' and event.value == 'PRESS':
            if self._query:
                self._query = self._query[:-1]
                self._match_index = 0
                self._update_matches(context)
            return {'RUNNING_MODAL'}

        if event.type == 'R' and event.ctrl and event.value == 'PRESS':
            self._cycle_match(context, -1 if event.shift else 1)
            return {'RUNNING_MODAL'}

        if event.type == 'UP_ARROW' and event.value == 'PRESS':
            self._cycle_match(context, -1)
            return {'RUNNING_MODAL'}

        if event.type == 'DOWN_ARROW' and event.value == 'PRESS':
            self._cycle_match(context, 1)
            return {'RUNNING_MODAL'}

        if event.type in {'RET', 'NUMPAD_ENTER'} and event.value == 'PRESS':
            sc = context.space_data
            try:
                line_object = sc.history[-1]
            except:
                context.area.header_text_set(None)
                return {'CANCELLED'}

            if self._matches:
                text = self._matches[self._match_index]
            else:
                text = self._original_text

            line_object.body = text
            line_object.current_character = len(text)

            context.area.header_text_set(None)
            return {'FINISHED'}

        if event.type in {'ESC', 'RIGHTMOUSE'}:
            sc = context.space_data
            try:
                line_object = sc.history[-1]
            except:
                context.area.header_text_set(None)
                return {'CANCELLED'}

            line_object.body = self._original_text
            line_object.current_character = len(self._original_text)

            context.area.header_text_set(None)
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}


class ConsoleAutocomplete(Operator):
    """Evaluate the namespace up until the cursor and give a list of """ \
        """options or complete the name if there is only one"""
    bl_idname = "console.autocomplete"
    bl_label = "Console Autocomplete"

    @classmethod
    def poll(cls, context):
        return (context.area and context.area.type == 'CONSOLE')

    def execute(self, context):
        sc = context.space_data
        module = _lang_module_get(sc)
        autocomplete = getattr(module, "autocomplete", None)

        if autocomplete:
            return autocomplete(context)
        else:
            print("Error: bpy.ops.console.autocomplete_{:s} - not found".format(sc.language))
            return {'FINISHED'}


class ConsoleCopyAsScript(Operator):
    """Copy the console contents for use in a script"""
    bl_idname = "console.copy_as_script"
    bl_label = "Copy to Clipboard (as Script)"

    @classmethod
    def poll(cls, context):
        return (context.area and context.area.type == 'CONSOLE')

    def execute(self, context):
        sc = context.space_data

        module = _lang_module_get(sc)
        copy_as_script = getattr(module, "copy_as_script", None)

        if copy_as_script:
            return copy_as_script(context)
        else:
            print("Error: copy_as_script - not found for {!r}".format(sc.language))
            return {'FINISHED'}


class ConsoleBanner(Operator):
    """Print a message when the terminal initializes"""
    bl_idname = "console.banner"
    bl_label = "Console Banner"

    @classmethod
    def poll(cls, context):
        return (context.area and context.area.type == 'CONSOLE')

    def execute(self, context):
        sc = context.space_data

        # default to python
        if not sc.language:
            sc.language = "python"

        module = _lang_module_get(sc)
        banner = getattr(module, "banner", None)

        if banner:
            return banner(context)
        else:
            print("Error: bpy.ops.console.banner_{:s} - not found".format(sc.language))
            return {'FINISHED'}


class ConsoleLanguage(Operator):
    """Set the current language for this console"""
    bl_idname = "console.language"
    bl_label = "Console Language"

    language: StringProperty(
        name="Language",
        translation_context=i18n_contexts.editor_python_console,
        maxlen=32,
    )

    @classmethod
    def poll(cls, context):
        return (context.area and context.area.type == 'CONSOLE')

    def execute(self, context):
        sc = context.space_data

        # default to python
        sc.language = self.language

        bpy.ops.console.banner()

        # insert a new blank line
        bpy.ops.console.history_append(text="", current_character=0, remove_duplicates=True)

        return {'FINISHED'}


classes = (
    ConsoleAutocomplete,
    ConsoleBanner,
    ConsoleCopyAsScript,
    ConsoleExec,
    ConsoleHistorySearch,
    ConsoleLanguage,
)
