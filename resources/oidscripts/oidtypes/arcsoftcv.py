# -*- coding: utf-8 -*-

"""
This module is concerned with the analysis of each variable found by the
debugger, as well as identifying and describing the buffers that should be
plotted in the ImageWatch window.
"""

import re

from oidscripts import symbols
from oidscripts.oidtypes import interface


# OpenCV constants
TV_CN_MAX = 16
TV_CN_SHIFT = 3
TV_MAT_CN_MASK = ((TV_CN_MAX - 1) << TV_CN_SHIFT)
TV_DEPTH_MAX = (1 << TV_CN_SHIFT)
TV_MAT_TYPE_MASK = (TV_DEPTH_MAX * TV_CN_MAX - 1)


class Mat(interface.TypeInspectorInterface):
    """
    Implementation for inspecting Arcsoft CV Mat classes
    """
    def get_buffer_metadata(self, obj_name, picked_obj, debugger_bridge):
        buffer = debugger_bridge.get_casted_pointer('char', picked_obj['data'])
        if buffer == 0x0:
            raise Exception('Received null buffer!')

        width = int(picked_obj['cols'])
        height = int(picked_obj['rows'])
        flags = int(picked_obj['flags'])

        channels = ((((flags) & TV_MAT_CN_MASK) >> TV_CN_SHIFT) + 1)
        row_stride = int(int(picked_obj['step'])/channels)

        if channels >= 3:
            pixel_layout = 'bgra'
        else:
            pixel_layout = 'rgba'

        cvtype = ((flags) & TV_MAT_TYPE_MASK)

        type_value = (cvtype & 7)

        if (type_value == symbols.OID_TYPES_UINT16 or
            type_value == symbols.OID_TYPES_INT16):
            row_stride = int(row_stride / 2)
        elif (type_value == symbols.OID_TYPES_INT32 or
              type_value == symbols.OID_TYPES_FLOAT32):
            row_stride = int(row_stride / 4)
        elif type_value == symbols.OID_TYPES_FLOAT64:
            row_stride = int(row_stride / 8)

        return {
            'display_name':  obj_name + ' (' + str(picked_obj.type) + ')',
            'pointer': buffer,
            'width': width,
            'height': height,
            'channels': channels,
            'type': type_value,
            'row_stride': row_stride,
            'pixel_layout': pixel_layout,
            'transpose_buffer' : False
        }

    def is_symbol_observable(self, symbol, symbol_name):
        """
        Returns true if the given symbol is of observable type (the type of the
        buffer you are working with). Make sure to check for pointers of your
        type as well
        """
        # Check if symbol type is the expected buffer
        symbol_type = str(symbol.type)
        type_regex = r'(const\s+)?tv::Mat(\s+?[*&])?'
        return re.match(type_regex, symbol_type) is not None

