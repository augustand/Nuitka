#
#     Copyright 2011, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     If you submit Kay Hayen patches to this software in either form, you
#     automatically grant him a copyright assignment to the code, or in the
#     alternative a BSD license to the code, should your jurisdiction prevent
#     this. Obviously it won't affect code that comes to him indirectly or
#     code you don't submit to him.
#
#     This is to reserve my ability to re-license the code at any time, e.g.
#     the PSF. With this version of Nuitka, using it for Closed Source will
#     not be allowed.
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, version 3 of the License.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#     Please leave the whole of this copyright notice intact.
#
""" Namify constants

"""

from logging import warning

import hashlib, re

# pylint: disable=W0622
from nuitka.__past__ import long, unicode
# pylint: enable=W0622

class ExceptionCannotNamify( Exception ):
    pass

def namifyConstant( constant ):
    # Many branches and everyone has a return, pylint: disable=R0911,R0912

    if type( constant ) == int:
        if constant == 0:
            return "int_0"
        elif constant > 0:
            return "int_pos_%d" % constant
        else:
            return "int_neg_%d" % abs( constant )
    elif type( constant ) == long:
        if constant == 0:
            return "long_0"
        elif constant > 0:
            return "long_pos_%d" % constant
        else:
            return "long_neg_%d" % abs( constant )
    elif constant is None:
        return "none"
    elif constant is True:
        return "true"
    elif constant is False:
        return "false"
    elif constant is Ellipsis:
        return "ellipsis"
    elif type( constant ) == str:
        return "str_" + _namifyString( constant )
    elif type( constant ) == unicode:
        if _isAscii( constant ):
            return "unicode_" + _namifyString( str( constant ) )
        else:
            # Others are better digested to not cause compiler trouble
            return "unicode_digest_" + _digest( repr( constant ) )
    elif type( constant ) == float:
        return "float_%s" % repr( constant ).replace( ".", "_" ).replace( "-", "_minus_" ).replace( "+", "" )
    elif type( constant ) == complex:
        value = str( constant ).replace( "+", "p" ).replace( "-", "m" ).replace(".","_")

        if value.startswith( "(" ) and value.endswith( ")" ):
            value = value[1:-1]

        return "complex_%s" % value
    elif type( constant ) == dict:
        if constant == {}:
            return "dict_empty"
        else:
            return "dict_" + _digest( repr( constant ) )
    elif type( constant ) == set:
        if constant == set():
            return "set_empty"
        else:
            return "set_" + _digest( repr( constant ) )
    elif type( constant ) == frozenset:
        if constant == frozenset():
            return "frozenset_empty"
        else:
            return "frozenset_" + _digest( repr( constant ) )
    elif type( constant ) == tuple:
        if constant == ():
            return "tuple_empty"
        else:
            result = "tuple_"

            try:
                parts = []

                for value in constant:
                    parts.append( namifyConstant( value ) )

                return result + "_".join( parts )
            except ExceptionCannotNamify:
                warning( "Couldn't namify '%r'" % value )

                return "tuple_" + hashlib.md5( repr( constant ) ).hexdigest()
    elif type( constant ) == list:
        if constant == []:
            return "list_empty"
        else:
            result = "list_"

            try:
                parts = []

                for value in constant:
                    parts.append( namifyConstant( value ) )

                return result + "_".join( parts )
            except ExceptionCannotNamify:
                warning( "Couldn't namify '%r'" % value )

                return "list_" + hashlib.md5( repr( constant ) ).hexdigest()

    raise ExceptionCannotNamify( constant )

_re_str_needs_no_digest = re.compile( r"^([a-z]|[A-Z]|[0-9]|_){1,40}$", re.S )

def _namifyString( string ):
    if string == "":
        return "empty"
    elif string == ".":
        return "dot"
    elif _re_str_needs_no_digest.match( string ) and "\n" not in string:
        # Some strings can be left intact for source code readability.
        return "plain_" + string
    elif len( string ) == 1:
        return "chr_%d" % ord( string )
    elif len( string ) > 2 and string[0] == "<" and string[-1] == ">" and \
           _re_str_needs_no_digest.match( string[1:-1] ) and "\n" not in string:
        return "angle_" + string[1:-1]
    else:
        # Others are better digested to not cause compiler trouble
        return "digest_" + _digest( string )



def _isAscii( string ):
    try:
        _unused = str( string )

        return True
    except UnicodeEncodeError:
        return False

def _digest( value ):
    if str is not unicode:
        return hashlib.md5( value ).hexdigest()
    else:
        return hashlib.md5( value.encode( "utf_8" ) ).hexdigest()