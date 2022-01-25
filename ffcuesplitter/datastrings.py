"""
Name: datastrings.py
Porpose: useful information strings
Writer: jeanslack <jeanlucperni@gmail.com>
license: GPL3
####################################################################

This file is part of ffcuesplitter.

    ffcuesplitter is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    ffcuesplitter is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with ffcuesplitter.  If not, see <http://www.gnu.org/licenses/>.
"""
def informations():
    """
    All general info of the ffcuesplitter
    """
    data = {'author': "Gianluca Pernigotto - Jeanslack",
            'mail': '<jeanlucperni@gmail.com>',
            'copyright': '© 2022',
            'version': '1.0.3',
            'release': 'January 25 2022',
            'rls_name': "FFcuesplitter",
            'prg_name': "ffcuesplitter",
            'webpage': "https://github.com/jeanslack/FFcuesplitter",
            'short_decript': ("FFmpeg based audio splitter for audio CD "
                              "images supplied with CUE sheet files."),
            }

    lic = f"""
Copyright - {data['copyright']} {data['author']}
Author and Developer: {data['author']}
Mail: {data['mail']}

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License 3 as published by
the Free Software Foundation; version .

This package is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this package; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA
"""

    short_license = "GPL3 (Gnu Public License)"

    return (data, lic, short_license)
